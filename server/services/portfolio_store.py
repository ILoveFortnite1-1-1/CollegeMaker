"""Portfolio Store: CRUD Service for Essays, Requirements Checklist, and Aid Offers."""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid

from server.models.portfolio import (
    ChecklistItem,
    FinancialAidOffer,
    EssayEntry,
    StudentPortfolio,
)
from server.services.portfolio import portfolio_service


DEFAULT_REQUIREMENTS = [
    {"name": "Counselor Recommendation", "category": "Recommendation", "required": True, "completed": False},
    {"name": "2 Teacher Recommendations", "category": "Recommendation", "required": True, "completed": False},
    {"name": "Official High School Transcript", "category": "Academic", "required": True, "completed": False},
    {"name": "FAFSA Application", "category": "Financial Aid", "required": True, "completed": False},
    {"name": "CSS Profile", "category": "Financial Aid", "required": True, "completed": False},
    {"name": "Admissions Interview", "category": "Interview", "required": False, "completed": False},
    {"name": "Common App Main Essay", "category": "Essays", "required": True, "completed": False},
    {"name": "Supplemental Essays", "category": "Essays", "required": True, "completed": False},
]


class PortfolioStore:
    """Store interface extending portfolio operations with Essay and Checklist management."""

    # -------------------------------------------------------------------------
    # Essay CRUD Operations (R3)
    # -------------------------------------------------------------------------
    async def get_essays(self, portfolio_id: str) -> List[EssayEntry]:
        """Get all essay entries for a portfolio."""
        portfolio, _, _ = await portfolio_service.get_or_create_portfolio(portfolio_id)
        return portfolio.essays

    async def get_essay(self, portfolio_id: str, essay_id: str) -> Optional[EssayEntry]:
        """Get a single essay entry by ID."""
        portfolio, _, _ = await portfolio_service.get_or_create_portfolio(portfolio_id)
        for essay in portfolio.essays:
            if essay.id == essay_id:
                return essay
        return None

    async def create_essay(self, portfolio_id: str, essay_data: Dict[str, Any]) -> EssayEntry:
        """Create and persist a new essay entry."""
        portfolio, _, _ = await portfolio_service.get_or_create_portfolio(portfolio_id)
        essay_obj = EssayEntry(**essay_data)
        portfolio.essays.append(essay_obj)
        portfolio.updated_at = datetime.now(timezone.utc).isoformat()
        await portfolio_service._save_portfolio(portfolio)
        return essay_obj

    async def update_essay(self, portfolio_id: str, essay_id: str, update_data: Dict[str, Any]) -> Optional[EssayEntry]:
        """Update an existing essay entry."""
        portfolio, _, _ = await portfolio_service.get_or_create_portfolio(portfolio_id)
        target = None
        for essay in portfolio.essays:
            if essay.id == essay_id:
                target = essay
                break

        if not target:
            return None

        for k, v in update_data.items():
            if v is not None and hasattr(target, k):
                setattr(target, k, v)

        target.updated_at = datetime.now(timezone.utc).isoformat()
        portfolio.updated_at = datetime.now(timezone.utc).isoformat()
        await portfolio_service._save_portfolio(portfolio)
        return target

    async def delete_essay(self, portfolio_id: str, essay_id: str) -> bool:
        """Delete an essay entry by ID."""
        portfolio, _, _ = await portfolio_service.get_or_create_portfolio(portfolio_id)
        initial_len = len(portfolio.essays)
        portfolio.essays = [e for e in portfolio.essays if e.id != essay_id]
        if len(portfolio.essays) < initial_len:
            portfolio.updated_at = datetime.now(timezone.utc).isoformat()
            await portfolio_service._save_portfolio(portfolio)
            return True
        return False

    # -------------------------------------------------------------------------
    # Requirements Checklist Operations (R7)
    # -------------------------------------------------------------------------
    def _find_college_item(self, portfolio: StudentPortfolio, college_id: str):
        cid = str(college_id).strip()
        for item in portfolio.colleges:
            if str(item.college_id) == cid or str(item.id) == cid:
                return item
        return None

    def _ensure_defaults(self, item):
        if not item.tracker.requirements:
            is_private = bool(item.college and "private" in (item.college.control or "").lower())
            for req_def in DEFAULT_REQUIREMENTS:
                req_copy = dict(req_def)
                if req_copy["name"] == "CSS Profile" and not is_private:
                    req_copy["required"] = False
                item.tracker.requirements.append(ChecklistItem(**req_copy))

    async def get_checklist(self, portfolio_id: str, college_id: str) -> List[ChecklistItem]:
        """Get checklist items for a saved college, initializing defaults if empty."""
        portfolio, _, _ = await portfolio_service.get_or_create_portfolio(portfolio_id)
        item = self._find_college_item(portfolio, college_id)
        if not item:
            return []

        if not item.tracker.requirements:
            self._ensure_defaults(item)
            await portfolio_service._save_portfolio(portfolio)

        return item.tracker.requirements

    async def add_checklist_item(
        self,
        portfolio_id: str,
        college_id: str,
        item_data: Dict[str, Any],
    ) -> Optional[ChecklistItem]:
        """Add a custom checklist item to a specific saved college."""
        portfolio, _, _ = await portfolio_service.get_or_create_portfolio(portfolio_id)
        item = self._find_college_item(portfolio, college_id)
        if not item:
            return None

        self._ensure_defaults(item)

        new_req = ChecklistItem(**item_data)
        item.tracker.requirements.append(new_req)
        portfolio.updated_at = datetime.now(timezone.utc).isoformat()
        await portfolio_service._save_portfolio(portfolio)
        return new_req


    async def update_checklist_item(
        self,
        portfolio_id: str,
        college_id: str,
        item_id: str,
        update_data: Dict[str, Any],
    ) -> Optional[ChecklistItem]:
        """Update or toggle a checklist item's completion / required status."""
        portfolio, _, _ = await portfolio_service.get_or_create_portfolio(portfolio_id)
        item = self._find_college_item(portfolio, college_id)
        if not item:
            return None

        # Ensure initialized
        if not item.tracker.requirements:
            await self.get_checklist(portfolio_id, college_id)

        target_req = None
        for req in item.tracker.requirements:
            if req.id == item_id or req.name == item_id:
                target_req = req
                break

        if not target_req:
            return None

        for k, v in update_data.items():
            if v is not None and hasattr(target_req, k):
                setattr(target_req, k, v)

        portfolio.updated_at = datetime.now(timezone.utc).isoformat()
        await portfolio_service._save_portfolio(portfolio)
        return target_req

    async def delete_checklist_item(
        self,
        portfolio_id: str,
        college_id: str,
        item_id: str,
    ) -> bool:
        """Delete a checklist item from a college tracker."""
        portfolio, _, _ = await portfolio_service.get_or_create_portfolio(portfolio_id)
        item = self._find_college_item(portfolio, college_id)
        if not item:
            return False

        initial_len = len(item.tracker.requirements)
        item.tracker.requirements = [r for r in item.tracker.requirements if r.id != item_id and r.name != item_id]
        if len(item.tracker.requirements) < initial_len:
            portfolio.updated_at = datetime.now(timezone.utc).isoformat()
            await portfolio_service._save_portfolio(portfolio)
            return True
        return False

    async def get_requirements_matrix(self, portfolio_id: str) -> Dict[str, Any]:
        """Construct cross-school matrix (schools = cols, requirements = rows)."""
        portfolio, _, _ = await portfolio_service.get_or_create_portfolio(portfolio_id)

        colleges_meta = []
        all_req_names = []
        school_requirements: Dict[str, Dict[str, List[ChecklistItem]]] = {}

        for item in portfolio.colleges:
            cid = str(item.id or item.college_id)
            cname = item.canonical_name or item.college_name
            colleges_meta.append({"id": cid, "name": cname})

            reqs = await self.get_checklist(portfolio_id, cid)
            req_map: Dict[str, List[ChecklistItem]] = {}
            for r in reqs:
                if r.name not in req_map:
                    req_map[r.name] = []
                req_map[r.name].append(r)
                if r.name not in all_req_names:
                    all_req_names.append(r.name)
            school_requirements[cid] = req_map

        matrix_rows = []
        summary_counts: Dict[str, int] = {}

        for name in all_req_names:
            req_count = 0
            completed_count = 0
            col_status: Dict[str, Any] = {}

            for c in colleges_meta:
                cid = c["id"]
                req_items = school_requirements.get(cid, {}).get(name, [])
                if req_items:
                    is_required = any(r.required for r in req_items)
                    is_completed = any(r.completed for r in req_items)
                    active_item = next((r for r in req_items if r.completed), req_items[0])
                    col_status[cid] = {
                        "id": active_item.id,
                        "required": is_required,
                        "completed": is_completed,
                        "deadline": active_item.deadline,
                    }
                    if is_required:
                        req_count += 1
                    if is_completed:
                        completed_count += 1
                else:
                    col_status[cid] = {
                        "id": None,
                        "required": False,
                        "completed": False,
                        "deadline": None,
                    }

            summary_counts[name] = req_count
            matrix_rows.append({
                "requirement_name": name,
                "name": name,
                "total_schools_requiring": req_count,
                "completed_count": completed_count,
                "schools": col_status,
            })

        return {
            "matrix": matrix_rows,
            "colleges": colleges_meta,
            "summary_counts": summary_counts,
        }

    async def toggle_requirement_all(
        self,
        portfolio_id: str,
        requirement_name: str,
        completed: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """Toggle or set a specific requirement for all saved colleges in one operation."""
        portfolio, _, _ = await portfolio_service.get_or_create_portfolio(portfolio_id)
        if not portfolio.colleges:
            return {"requirement_name": requirement_name, "updated": 0, "completed": False}

        for item in portfolio.colleges:
            self._ensure_defaults(item)

        if completed is None:
            all_done = True
            found_any = False
            for item in portfolio.colleges:
                for r in item.tracker.requirements:
                    if r.name == requirement_name and r.required:
                        found_any = True
                        if not r.completed:
                            all_done = False
                            break
                if not all_done:
                    break
            target_state = not (all_done if found_any else False)
        else:
            target_state = bool(completed)

        updated_count = 0
        for item in portfolio.colleges:
            matched = False
            for r in item.tracker.requirements:
                if r.name == requirement_name:
                    r.required = True
                    r.completed = target_state
                    matched = True
                    updated_count += 1
            if not matched:
                item.tracker.requirements.append(
                    ChecklistItem(name=requirement_name, required=True, completed=target_state)
                )
                updated_count += 1

        portfolio.updated_at = datetime.now(timezone.utc).isoformat()
        await portfolio_service._save_portfolio(portfolio)
        return {
            "requirement_name": requirement_name,
            "completed": target_state,
            "updated_colleges": len(portfolio.colleges),
            "updated_count": updated_count,
        }

    async def toggle_all_requirements(
        self,
        portfolio_id: str,
        completed: bool = True,
    ) -> Dict[str, Any]:
        """Mark ALL requirements across ALL saved colleges as completed (or incomplete) in one click."""
        portfolio, _, _ = await portfolio_service.get_or_create_portfolio(portfolio_id)
        target_state = bool(completed)
        updated_count = 0

        for item in portfolio.colleges:
            self._ensure_defaults(item)
            for r in item.tracker.requirements:
                r.completed = target_state
                updated_count += 1

        portfolio.updated_at = datetime.now(timezone.utc).isoformat()
        await portfolio_service._save_portfolio(portfolio)
        return {
            "completed": target_state,
            "colleges_count": len(portfolio.colleges),
            "updated_count": updated_count,
        }

    async def toggle_college_checklist_all(
        self,
        portfolio_id: str,
        college_id: str,
        completed: bool = True,
    ) -> Dict[str, Any]:
        """Mark all requirements for a single college as completed (or incomplete) in one click."""
        portfolio, _, _ = await portfolio_service.get_or_create_portfolio(portfolio_id)
        item = self._find_college_item(portfolio, college_id)
        if not item:
            return {"college_id": college_id, "updated": 0, "completed": False}

        self._ensure_defaults(item)
        target_state = bool(completed)
        updated_count = 0
        for r in item.tracker.requirements:
            r.completed = target_state
            updated_count += 1

        portfolio.updated_at = datetime.now(timezone.utc).isoformat()
        await portfolio_service._save_portfolio(portfolio)
        return {
            "college_id": college_id,
            "completed": target_state,
            "updated_count": updated_count,
        }

    # -------------------------------------------------------------------------
    # Aid Offers (R1)
    # -------------------------------------------------------------------------
    async def save_aid_offer(
        self,
        portfolio_id: str,
        college_id: str,
        offer_data: Dict[str, Any],
    ) -> FinancialAidOffer:
        """Save aid offer for a college in the portfolio."""
        portfolio, _, _ = await portfolio_service.get_or_create_portfolio(portfolio_id)
        cid = str(college_id).strip()
        offer_dict = dict(offer_data)
        offer_dict["college_id"] = cid
        offer_obj = FinancialAidOffer(**offer_dict)

        portfolio.aid_offers[cid] = offer_obj

        # Also sync on portfolio item if present
        item = self._find_college_item(portfolio, cid)
        if item:
            item.aid_offer = offer_obj

        portfolio.updated_at = datetime.now(timezone.utc).isoformat()
        await portfolio_service._save_portfolio(portfolio)
        return offer_obj

    async def delete_aid_offer(self, portfolio_id: str, college_id: str) -> bool:
        """Delete aid offer for a college in the portfolio."""
        portfolio, _, _ = await portfolio_service.get_or_create_portfolio(portfolio_id)
        cid = str(college_id).strip()
        deleted = False
        if cid in portfolio.aid_offers:
            del portfolio.aid_offers[cid]
            deleted = True

        item = self._find_college_item(portfolio, cid)
        if item and item.aid_offer:
            item.aid_offer = None
            deleted = True

        if deleted:
            portfolio.updated_at = datetime.now(timezone.utc).isoformat()
            await portfolio_service._save_portfolio(portfolio)
        return deleted


portfolio_store = PortfolioStore()
