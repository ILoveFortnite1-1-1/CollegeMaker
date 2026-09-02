"""Cookie-Based Guest Portfolio Storage & Session Manager."""
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
from typing import Any, Dict, Optional, Tuple
import uuid
from server.config import settings
from server.models.canonical import CanonicalCollege
from server.models.portfolio import (
    PortfolioItem,
    PortfolioSummary,
    StudentPortfolio,
    StudentPreferences,
)
from server.services.fit_scorer import fit_scorer
from server.services.scorecard import scorecard_service


class PortfolioService:
    """Manages anonymous guest portfolios persisted in SQLite with in-memory fallback."""

    def __init__(self):
        self.db_path: Path = settings.DATABASE_PATH
        self._memory_store: Dict[str, StudentPortfolio] = {}
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Create a connection to SQLite database."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        """Initialize portfolios table."""
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS portfolios (
                        portfolio_id TEXT PRIMARY KEY,
                        data_json TEXT NOT NULL,
                        created_at TIMESTAMP NOT NULL,
                        updated_at TIMESTAMP NOT NULL
                    )
                    """
                )
                conn.commit()
        except Exception:
            pass

    async def get_or_create_portfolio(self, portfolio_id: Optional[str] = None) -> Tuple[StudentPortfolio, str, bool]:
        """Fetch existing portfolio by ID or generate a new guest portfolio session."""
        now_str = datetime.now(timezone.utc).isoformat()
        is_new = False

        if not portfolio_id:
            portfolio_id = f"port_{uuid.uuid4().hex}"
            is_new = True
            new_portfolio = StudentPortfolio(
                portfolio_id=portfolio_id,
                colleges=[],
                preferences=StudentPreferences(),
                created_at=now_str,
                updated_at=now_str,
            )
            await self._save_portfolio(new_portfolio)
            return new_portfolio, portfolio_id, is_new

        # Attempt to load existing portfolio
        portfolio = await self._load_portfolio(portfolio_id)
        if not portfolio:
            is_new = True
            portfolio = StudentPortfolio(
                portfolio_id=portfolio_id,
                colleges=[],
                preferences=StudentPreferences(),
                created_at=now_str,
                updated_at=now_str,
            )
            await self._save_portfolio(portfolio)

        return portfolio, portfolio_id, is_new

    async def add_college(
        self,
        portfolio_id: str,
        college_id: str,
        notes: Optional[str] = None,
        tag: Optional[str] = None,
    ) -> StudentPortfolio:
        """Save a college to the student's portfolio and calculate dynamic fit score."""
        portfolio, pid, _ = await self.get_or_create_portfolio(portfolio_id)
        cid = str(college_id).strip()

        # Fetch college data
        college = await scorecard_service.get_college_by_id(cid)
        if not college:
            raise ValueError(f"College with ID '{college_id}' not found.")

        # Calculate fit score against preferences
        fit_res = fit_scorer.evaluate_college_fit(college, portfolio.preferences)
        breakdown_dict = fit_res.to_breakdown_dict()
        college.fit_score = fit_res.overall_score
        college.fit_category = tag or fit_res.category
        college.fit_breakdown = breakdown_dict

        now_str = datetime.now(timezone.utc).isoformat()

        # Check if already in portfolio
        existing_idx = next(
            (i for i, item in enumerate(portfolio.colleges) if str(item.college_id) == cid or str(item.id) == cid),
            None,
        )

        item = PortfolioItem(
            id=college.id,
            college_id=college.id,
            name=college.name,
            canonical_name=college.name,
            college_name=college.name,
            added_at=now_str,
            notes=notes,
            tag=tag or fit_res.category,
            category_override=tag,
            college=college,
            fit_score=fit_res.overall_score,
            fit_category=tag or fit_res.category,
            fit_breakdown=breakdown_dict,
        )

        if existing_idx is not None:
            # Update notes/tag if provided
            if notes is not None:
                item.notes = notes
            if tag is not None:
                item.tag = tag
            portfolio.colleges[existing_idx] = item
        else:
            portfolio.colleges.append(item)

        portfolio.updated_at = now_str
        await self._save_portfolio(portfolio)
        return portfolio

    async def update_college_item(
        self,
        portfolio_id: str,
        college_id: str,
        notes: Optional[str] = None,
        tag: Optional[str] = None,
        custom_label: Optional[str] = None,
    ) -> StudentPortfolio:
        """Update tags, notes, or custom labels on a saved college item."""
        portfolio, pid, _ = await self.get_or_create_portfolio(portfolio_id)
        cid = str(college_id).strip()

        existing_item = next(
            (item for item in portfolio.colleges if str(item.college_id) == cid or str(item.id) == cid),
            None,
        )
        if existing_item:
            if notes is not None:
                existing_item.notes = notes
            if tag is not None:
                existing_item.tag = tag
            if custom_label is not None:
                existing_item.custom_label = custom_label
            portfolio.updated_at = datetime.now(timezone.utc).isoformat()
            await self._save_portfolio(portfolio)
        return portfolio

    async def update_college_tracker(
        self,
        portfolio_id: str,
        college_id: str,
        tracker_data: Dict[str, Any],
    ) -> StudentPortfolio:
        """Update application tracker milestone progress and deadlines for a saved college."""
        portfolio, pid, _ = await self.get_or_create_portfolio(portfolio_id)
        cid = str(college_id).strip()

        existing_item = next(
            (item for item in portfolio.colleges if str(item.college_id) == cid or str(item.id) == cid),
            None,
        )
        if existing_item:
            from server.models.portfolio import ApplicationTracker
            current_dict = existing_item.tracker.model_dump() if hasattr(existing_item, "tracker") and existing_item.tracker else {}
            current_dict.update({k: v for k, v in tracker_data.items() if v is not None})
            existing_item.tracker = ApplicationTracker(**current_dict)
            portfolio.updated_at = datetime.now(timezone.utc).isoformat()
            await self._save_portfolio(portfolio)
        return portfolio

    async def remove_college(self, portfolio_id: str, college_id: str) -> StudentPortfolio:
        """Remove a saved college from the student's portfolio."""
        portfolio, pid, _ = await self.get_or_create_portfolio(portfolio_id)
        cid = str(college_id).strip()

        portfolio.colleges = [item for item in portfolio.colleges if str(item.college_id) != cid and str(item.id) != cid]
        portfolio.updated_at = datetime.now(timezone.utc).isoformat()
        await self._save_portfolio(portfolio)
        return portfolio

    async def update_preferences(
        self,
        portfolio_id: str,
        preferences: StudentPreferences,
    ) -> StudentPortfolio:
        """Update student preferences and dynamically recalculate fit scores for all saved colleges."""
        portfolio, pid, _ = await self.get_or_create_portfolio(portfolio_id)
        portfolio.preferences = preferences
        now_str = datetime.now(timezone.utc).isoformat()
        portfolio.updated_at = now_str

        # Recalculate fit for all saved colleges
        for item in portfolio.colleges:
            college = await scorecard_service.get_college_by_id(item.college_id)
            if college:
                fit_res = fit_scorer.evaluate_college_fit(college, portfolio.preferences)
                breakdown_dict = fit_res.to_breakdown_dict()
                college.fit_score = fit_res.overall_score
                college.fit_category = fit_res.category
                college.fit_breakdown = breakdown_dict
                item.college = college
                item.fit_score = fit_res.overall_score
                item.fit_category = fit_res.category
                item.fit_breakdown = breakdown_dict

        await self._save_portfolio(portfolio)
        return portfolio

    async def clear_portfolio(self, portfolio_id: str) -> StudentPortfolio:
        """Clear all saved colleges from the portfolio."""
        portfolio, pid, _ = await self.get_or_create_portfolio(portfolio_id)
        portfolio.colleges = []
        portfolio.updated_at = datetime.now(timezone.utc).isoformat()
        await self._save_portfolio(portfolio)
        return portfolio

    async def get_summary(self, portfolio_id: str) -> PortfolioSummary:
        """Calculate summary statistics across saved colleges in the portfolio."""
        portfolio, _, _ = await self.get_or_create_portfolio(portfolio_id)
        colleges = portfolio.colleges

        if not colleges:
            return PortfolioSummary()

        reach = sum(1 for c in colleges if c.fit_category == "Reach")
        target = sum(1 for c in colleges if c.fit_category == "Target")
        likely = sum(1 for c in colleges if c.fit_category == "Likely")

        # Compute averages from college records
        prices = [
            c.college.costs.net_price_average.value
            for c in colleges
            if c.college and c.college.costs and c.college.costs.net_price_average and c.college.costs.net_price_average.value
        ]
        avg_price = int(sum(prices) / len(prices)) if prices else None

        admits = [
            c.college.admissions.acceptance_rate.value
            for c in colleges
            if c.college and c.college.admissions and c.college.admissions.acceptance_rate and c.college.admissions.acceptance_rate.value
        ]
        avg_admit = round(sum(admits) / len(admits), 3) if admits else None

        earnings = [
            c.college.outcomes.median_earnings_10yr.value
            for c in colleges
            if c.college and c.college.outcomes and c.college.outcomes.median_earnings_10yr and c.college.outcomes.median_earnings_10yr.value
        ]
        avg_earnings = int(sum(earnings) / len(earnings)) if earnings else None

        return PortfolioSummary(
            total_colleges=len(colleges),
            reach_count=reach,
            target_count=target,
            likely_count=likely,
            average_net_price=avg_price,
            average_acceptance_rate=avg_admit,
            average_median_earnings=avg_earnings,
        )

    async def _load_portfolio(self, portfolio_id: str) -> Optional[StudentPortfolio]:
        """Load portfolio from SQLite or fallback in-memory cache."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT data_json FROM portfolios WHERE portfolio_id = ?", (portfolio_id,))
                row = cursor.fetchone()
                if row:
                    data = json.loads(row["data_json"])
                    return StudentPortfolio(**data)
        except Exception:
            pass

        return self._memory_store.get(portfolio_id)

    async def _save_portfolio(self, portfolio: StudentPortfolio) -> None:
        """Save portfolio to SQLite and memory store."""
        self._memory_store[portfolio.portfolio_id] = portfolio
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO portfolios (portfolio_id, data_json, created_at, updated_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        portfolio.portfolio_id,
                        json.dumps(portfolio.model_dump()),
                        portfolio.created_at,
                        portfolio.updated_at,
                    ),
                )
                conn.commit()
        except Exception:
            pass


portfolio_service = PortfolioService()
