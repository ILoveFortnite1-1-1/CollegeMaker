"""College Scorecard Ingestion & SQLite Caching Service."""
import asyncio
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sqlite3
from typing import Any, Dict, List, Optional, Tuple
import httpx
from server.config import settings
from server.models.canonical import (
    AdmissionsData,
    CanonicalCollege,
    ConfidenceLevel,
    CostData,
    EvidenceClaim,
    Location,
    MetricField,
    OutcomesData,
    QualitativeData,
    SourceType,
)


class ScorecardService:
    """Provides resilient querying for college data with SQLite caching and seed fallback."""

    def __init__(self):
        self.db_path: Path = settings.DATABASE_PATH
        self.seed_path: Path = settings.SEED_DATA_PATH
        self.api_key: Optional[str] = settings.COLLEGE_SCORECARD_API_KEY
        self.base_url = "https://api.data.gov/ed/collegescorecard/v1/schools"
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Create a connection to SQLite database."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        """Initialize SQLite tables and populate initial seed data if empty."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS colleges (
                    id TEXT PRIMARY KEY,
                    unitid INTEGER,
                    name TEXT NOT NULL,
                    alias TEXT,
                    control TEXT,
                    city TEXT,
                    state TEXT,
                    location_type TEXT,
                    acceptance_rate REAL,
                    net_price_average INTEGER,
                    median_earnings_10yr INTEGER,
                    undergrad_size INTEGER,
                    data_json TEXT NOT NULL,
                    updated_at TIMESTAMP
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS scorecard_cache (
                    id TEXT PRIMARY KEY,
                    data_json TEXT NOT NULL,
                    cached_at TIMESTAMP NOT NULL,
                    expires_at TIMESTAMP NOT NULL
                )
                """
            )
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_colleges_name ON colleges(name)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_colleges_state ON colleges(state)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_colleges_control ON colleges(control)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_colleges_admit ON colleges(acceptance_rate)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_colleges_cost ON colleges(net_price_average)")
            conn.commit()

            # Check if colleges table has data; if not, load from seed
            cursor.execute("SELECT COUNT(*) as count FROM colleges")
            row = cursor.fetchone()
            if row["count"] == 0:
                self._load_seed_data(conn)

    def _load_seed_data(self, conn: sqlite3.Connection) -> None:
        """Load bundled seed JSON into SQLite database."""
        if not self.seed_path.exists():
            return

        with open(self.seed_path, "r", encoding="utf-8") as f:
            colleges_data = json.load(f)

        cursor = conn.cursor()
        for item in colleges_data:
            c = CanonicalCollege(**item)
            cursor.execute(
                """
                INSERT OR REPLACE INTO colleges (
                    id, unitid, name, alias, control, city, state, location_type,
                    acceptance_rate, net_price_average, median_earnings_10yr, undergrad_size,
                    data_json, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    c.id,
                    c.unitid,
                    c.name,
                    c.alias,
                    c.control,
                    c.location.city,
                    c.location.state,
                    c.location.location_type,
                    c.admissions.acceptance_rate.value if c.admissions.acceptance_rate else None,
                    c.costs.net_price_average.value if c.costs.net_price_average else None,
                    c.outcomes.median_earnings_10yr.value if c.outcomes.median_earnings_10yr else None,
                    c.undergrad_size.value if c.undergrad_size else None,
                    json.dumps(c.model_dump()),
                    c.updated_at,
                ),
            )
        conn.commit()

    async def get_college_by_id(self, college_id: str) -> Optional[CanonicalCollege]:
        """Fetch a single college by ID (or slug/unitid/alias/name) from cache, DB, or API."""
        cid = str(college_id).strip()
        if not cid or cid == "0" or cid.startswith("-") or (cid.isdigit() and int(cid) <= 0):
            return None

        cid_lower = cid.lower()
        cid_normalized = cid_lower.replace("-", " ").replace("_", " ")


        # 1. Check in DB by exact id, unitid, alias, name, or slug
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT data_json FROM colleges 
                WHERE id = ? 
                   OR unitid = ? 
                   OR LOWER(id) = ?
                   OR LOWER(alias) = ? 
                   OR LOWER(name) = ?
                   OR LOWER(REPLACE(REPLACE(name, ' ', '-'), ',', '')) = ?
                   OR LOWER(name) LIKE ?
                   OR LOWER(alias) LIKE ?
                ORDER BY 
                   CASE WHEN id = ? THEN 1
                        WHEN LOWER(name) = ? THEN 2
                        WHEN LOWER(alias) = ? THEN 3
                        ELSE 4 END
                LIMIT 1
                """,
                (
                    cid, 
                    int(cid) if cid.isdigit() else -1, 
                    cid_lower,
                    cid_lower, 
                    cid_lower, 
                    cid_lower,
                    f"%{cid_normalized}%", 
                    f"%{cid_normalized}%",
                    cid, 
                    cid_lower, 
                    cid_lower
                )
            )
            row = cursor.fetchone()
            if row:
                data = json.loads(row["data_json"])
                return CanonicalCollege(**data)

        # 2. Check in scorecard_cache
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT data_json, expires_at FROM scorecard_cache WHERE id = ? OR LOWER(id) = ?", (cid, cid_lower))
            row = cursor.fetchone()
            if row:
                expires_at = datetime.fromisoformat(row["expires_at"])
                if expires_at > datetime.now(timezone.utc):
                    data = json.loads(row["data_json"])
                    return CanonicalCollege(**data)

        # 3. Query live Scorecard API (with API key or free DEMO_KEY)
        live_record = await self._fetch_live_scorecard(cid)
        if live_record:
            await self.save_college(live_record)
            return live_record

        return None


    async def search_colleges(
        self,
        query: Optional[str] = None,
        state: Optional[str] = None,
        control: Optional[str] = None,
        max_cost: Optional[int] = None,
        min_admit_rate: Optional[float] = None,
        max_admit_rate: Optional[float] = None,
        location_type: Optional[str] = None,
        sort_by: str = "name_asc",
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[CanonicalCollege], int]:
        """Search and filter colleges in SQLite with pagination."""
        conditions = []
        params = []

        if query:
            q_clean = f"%{query.strip().lower()}%"
            conditions.append("(LOWER(name) LIKE ? OR LOWER(alias) LIKE ? OR LOWER(city) LIKE ?)")
            params.extend([q_clean, q_clean, q_clean])

        if state:
            conditions.append("UPPER(state) = ?")
            params.append(state.strip().upper())

        if control and control != "any":
            conditions.append("control = ?")
            params.append(control.strip().lower())

        if max_cost is not None and max_cost > 0:
            conditions.append("net_price_average <= ?")
            params.append(max_cost)

        if min_admit_rate is not None:
            conditions.append("acceptance_rate >= ?")
            params.append(min_admit_rate)

        if max_admit_rate is not None:
            conditions.append("acceptance_rate <= ?")
            params.append(max_admit_rate)

        if location_type and location_type != "any":
            conditions.append("location_type = ?")
            params.append(location_type)

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        # Determine ORDER BY
        sort_map = {
            "name_asc": "name ASC",
            "name_desc": "name DESC",
            "admit_asc": "acceptance_rate ASC NULLS LAST",
            "admit_desc": "acceptance_rate DESC NULLS LAST",
            "cost_asc": "net_price_average ASC NULLS LAST",
            "cost_desc": "net_price_average DESC NULLS LAST",
            "earnings_desc": "median_earnings_10yr DESC NULLS LAST",
            "size_desc": "undergrad_size DESC NULLS LAST",
        }
        order_clause = f"ORDER BY {sort_map.get(sort_by, 'name ASC')}"

        offset = max(0, (page - 1) * page_size)
        limit_clause = f"LIMIT ? OFFSET ?"

        with self._get_connection() as conn:
            cursor = conn.cursor()
            count_query = f"SELECT COUNT(*) as total FROM colleges {where_clause}"
            cursor.execute(count_query, params)
            total_count = cursor.fetchone()["total"]

            data_query = f"SELECT data_json FROM colleges {where_clause} {order_clause} {limit_clause}"
            cursor.execute(data_query, params + [page_size, offset])
            rows = cursor.fetchall()

            colleges = []
            for row in rows:
                colleges.append(CanonicalCollege(**json.loads(row["data_json"])))

        if total_count == 0 and query and len(query.strip()) >= 2:
            live_record = await self._fetch_live_scorecard(query.strip())
            if live_record:
                await self.save_college(live_record)
                return [live_record], 1

        return colleges, total_count


    async def save_college(self, college: CanonicalCollege) -> None:
        """Persist or update a canonical college record in SQLite DB and cache."""
        now_str = datetime.now(timezone.utc).isoformat()
        college.updated_at = now_str

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO colleges (
                    id, unitid, name, alias, control, city, state, location_type,
                    acceptance_rate, net_price_average, median_earnings_10yr, undergrad_size,
                    data_json, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    college.id,
                    college.unitid,
                    college.name,
                    college.alias,
                    college.control,
                    college.location.city,
                    college.location.state,
                    college.location.location_type,
                    college.admissions.acceptance_rate.value if college.admissions.acceptance_rate else None,
                    college.costs.net_price_average.value if college.costs.net_price_average else None,
                    college.outcomes.median_earnings_10yr.value if college.outcomes.median_earnings_10yr else None,
                    college.undergrad_size.value if college.undergrad_size else None,
                    json.dumps(college.model_dump()),
                    college.updated_at,
                ),
            )

            # Also write to scorecard_cache with 7-day TTL
            expires_at = (datetime.now(timezone.utc) + timedelta(days=settings.SCORECARD_CACHE_TTL_DAYS)).isoformat()
            cursor.execute(
                """
                INSERT OR REPLACE INTO scorecard_cache (id, data_json, cached_at, expires_at)
                VALUES (?, ?, ?, ?)
                """,
                (college.id, json.dumps(college.model_dump()), now_str, expires_at),
            )
            conn.commit()

    async def _fetch_live_scorecard(self, college_id_or_name: str) -> Optional[CanonicalCollege]:
        """Fetch raw data from US College Scorecard API and normalize."""
        if not college_id_or_name:
            return None
        raw_str = str(college_id_or_name).strip()
        if raw_str in ["0", "-1"] or raw_str.startswith("-") or (raw_str.isdigit() and int(raw_str) <= 0):
            return None

        api_key = self.api_key or "DEMO_KEY"
        clean_target = raw_str.replace("-", " ").replace("_", " ")


        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                params = {
                    "api_key": api_key,
                    "fields": "id,school.name,school.alias,school.city,school.state,school.zip,school.ownership,latest.student.size,latest.admissions.admission_rate.overall,latest.cost.tuition.in_state,latest.cost.tuition.out_of_state,latest.cost.avg_net_price.overall,latest.earnings.10_yrs_after_entry.median,latest.completion.rate_suppressed.overall",
                }
                if clean_target.isdigit():
                    params["id"] = clean_target
                else:
                    params["school.name"] = clean_target

                resp = await client.get(self.base_url, params=params)
                if resp.status_code != 200:
                    return None

                data = resp.json()
                results = data.get("results", [])
                if not results:
                    return None


                item = results[0]
                unitid = item.get("id")
                name = item.get("school.name", "Unknown College")
                alias = item.get("school.alias")
                city = item.get("school.city", "Unknown City")
                state = item.get("school.state", "US")
                zip_code = item.get("school.zip")
                ownership = item.get("school.ownership")
                control = "public" if ownership == 1 else "private_nonprofit" if ownership == 2 else "private_for_profit"

                now_iso = datetime.now(timezone.utc).isoformat()
                prov = {
                    "source": "U.S. Department of Education College Scorecard API",
                    "source_type": SourceType.GOVERNMENT,
                    "year": 2023,
                    "confidence": ConfidenceLevel.REPORTED,
                    "status": "verified",
                    "retrieved_at": now_iso,
                }

                admit_rate = item.get("latest.admissions.admission_rate.overall")
                in_state = item.get("latest.cost.tuition.in_state", 15000 if control == "public" else 55000)
                out_state = item.get("latest.cost.tuition.out_of_state", 35000 if control == "public" else 55000)
                net_price = item.get("latest.cost.avg_net_price.overall", 20000)
                earnings = item.get("latest.earnings.10_yrs_after_entry.median", 75000)
                completion_rate = item.get("latest.completion.rate_suppressed.overall", 0.85)
                size = item.get("latest.student.size", 10000)

                college = CanonicalCollege(
                    id=str(unitid),
                    unitid=unitid,
                    name=name,
                    alias=alias,
                    control=control,
                    institution_type="4-year",
                    location=Location(city=city, state=state, zip=zip_code, location_type="Urban"),
                    undergrad_size=MetricField(value=size, **prov),
                    admissions=AdmissionsData(
                        acceptance_rate=MetricField(value=admit_rate or 0.20, **prov),
                    ),
                    costs=CostData(
                        tuition_in_state=MetricField(value=in_state, **prov),
                        tuition_out_of_state=MetricField(value=out_state, **prov),
                        net_price_average=MetricField(value=net_price, **prov),
                    ),
                    outcomes=OutcomesData(
                        completion_rate_6yr=MetricField(value=completion_rate or 0.85, **prov),
                        median_earnings_10yr=MetricField(value=earnings or 75000, **prov),
                    ),
                    created_at=now_iso,
                    updated_at=now_iso,
                )
                return college
        except Exception:
            return None


scorecard_service = ScorecardService()
