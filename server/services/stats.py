"""Visitor Statistics Service."""
from datetime import datetime, timezone
import sqlite3
from pathlib import Path
from server.config import settings


class StatsService:
    """Manages persistent page visit statistics in SQLite."""

    def __init__(self):
        self.db_path: Path = settings.DATABASE_PATH
        self._init_db()

    def _init_db(self) -> None:
        """Ensure visitor_stats table exists and is initialized."""
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
                    "INSERT INTO visitor_stats (id, total_visits, last_visited_at) VALUES (1, 1, ?)",
                    (datetime.now(timezone.utc).isoformat(),)
                )

    def record_visit(self) -> int:
        """Increment and return the total visit count."""
        now_str = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE visitor_stats 
                SET total_visits = total_visits + 1, last_visited_at = ?
                WHERE id = 1
                """,
                (now_str,)
            )
            cursor.execute("SELECT total_visits FROM visitor_stats WHERE id = 1")
            row = cursor.fetchone()
            return row[0] if row else 1

    def get_visit_count(self) -> int:
        """Get the current total visit count."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT total_visits FROM visitor_stats WHERE id = 1")
            row = cursor.fetchone()
            return row[0] if row else 0


stats_service = StatsService()
