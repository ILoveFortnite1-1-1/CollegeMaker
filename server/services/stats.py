"""Visitor Statistics Service with Cloud Persistence & SQLite Fallback."""
from datetime import datetime, timezone
import sqlite3
from pathlib import Path
import httpx
from server.config import settings

CLOUD_COUNTER_HIT_URL = "https://abacus.jasoncameron.dev/hit/collegemaker_portfolio_app/visits"
CLOUD_COUNTER_GET_URL = "https://abacus.jasoncameron.dev/get/collegemaker_portfolio_app/visits"
BASELINE_VISIT_OFFSET = 18  # Preserve existing lifetime visits across ephemeral restarts


class StatsService:
    """Manages permanent page visit statistics with cloud persistence and SQLite fallback."""

    def __init__(self):
        self.db_path: Path = settings.DATABASE_PATH
        self._init_db()

    def _init_db(self) -> None:
        """Ensure visitor_stats table exists and is initialized."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS visitor_stats (
                    id INTEGER PRIMARY KEY,
                    total_visits INTEGER DEFAULT 0,
                    last_visited_at TEXT
                )
                """
            )
            cursor.execute("SELECT COUNT(*) FROM visitor_stats WHERE id = 1")
            if cursor.fetchone()[0] == 0:
                cursor.execute(
                    "INSERT INTO visitor_stats (id, total_visits, last_visited_at) VALUES (1, ?, ?)",
                    (BASELINE_VISIT_OFFSET, datetime.now(timezone.utc).isoformat()),
                )

    async def record_visit(self) -> int:
        """Increment cloud counter and update local SQLite cache."""
        now_str = datetime.now(timezone.utc).isoformat()

        # 1. Try cloud persistent increment
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.get(CLOUD_COUNTER_HIT_URL)
                if res.status_code == 200:
                    data = res.json()
                    val = data.get("value")
                    if isinstance(val, int):
                        total = val + BASELINE_VISIT_OFFSET
                        self._update_sqlite_cache(total, now_str)
                        return total
        except Exception:
            pass  # Fall back to SQLite if network is unavailable

        # 2. Fallback to local SQLite counter
        return self._increment_sqlite_fallback(now_str)

    async def get_visit_count(self) -> int:
        """Get current total visit count."""
        # 1. Try cloud persistent get
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.get(CLOUD_COUNTER_GET_URL)
                if res.status_code == 200:
                    data = res.json()
                    val = data.get("value")
                    if isinstance(val, int):
                        return val + BASELINE_VISIT_OFFSET
        except Exception:
            pass

        # 2. Fallback to local SQLite
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT total_visits FROM visitor_stats WHERE id = 1")
            row = cursor.fetchone()
            return row[0] if row else BASELINE_VISIT_OFFSET

    def _update_sqlite_cache(self, total: int, now_str: str) -> None:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE visitor_stats SET total_visits = ?, last_visited_at = ? WHERE id = 1",
                    (total, now_str),
                )
        except Exception:
            pass

    def _increment_sqlite_fallback(self, now_str: str) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE visitor_stats SET total_visits = total_visits + 1, last_visited_at = ? WHERE id = 1",
                (now_str,),
            )
            cursor.execute("SELECT total_visits FROM visitor_stats WHERE id = 1")
            row = cursor.fetchone()
            return row[0] if row else BASELINE_VISIT_OFFSET


stats_service = StatsService()
