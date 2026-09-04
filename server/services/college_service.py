"""College Service for Field-of-Study Alumni Outcomes and Profile Data."""
from typing import Any, Dict, List, Optional
from server.models.canonical import CanonicalCollege, FieldOfStudyItem
from server.services.scorecard import scorecard_service
from server.services.scorecard_client import scorecard_client


class CollegeService:
    """Provides high-level college data queries and field-of-study outcomes analysis."""

    async def get_college(self, college_id: str) -> Optional[CanonicalCollege]:
        """Fetch canonical college profile by ID."""
        return await scorecard_service.get_college_by_id(str(college_id).strip())

    async def get_field_of_study(
        self,
        college_id: str,
        preferred_majors: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Get field-of-study earnings by major, sorted by earnings with preferred majors marked."""
        cid = str(college_id).strip()
        college = await self.get_college(cid)
        if not college:
            return {
                "college_id": cid,
                "college_name": "Unknown",
                "overall_median_earnings": 0,
                "majors": [],
                "programs": [],
                "preferred_matches": [],
            }

        programs = await scorecard_client.get_field_of_study_programs(cid, college.unitid)

        prefs_clean = [p.strip().lower() for p in (preferred_majors or []) if p and p.strip()]
        preferred_matches = []

        for p in programs:
            title_lower = p.major_title.lower()
            is_match = False
            for pref in prefs_clean:
                if pref in title_lower or title_lower in pref:
                    is_match = True
                    break
            p.is_preferred = is_match
            if is_match and p.major_title not in preferred_matches:
                preferred_matches.append(p.major_title)

        # Sort by median earnings descending
        programs.sort(key=lambda x: x.median_earnings or 0, reverse=True)

        overall_earnings = 60000
        if college.outcomes and college.outcomes.median_earnings_10yr and college.outcomes.median_earnings_10yr.value:
            overall_earnings = college.outcomes.median_earnings_10yr.value

        prog_dicts = [p.model_dump() for p in programs]

        return {
            "college_id": cid,
            "college_name": college.name,
            "overall_median_earnings": overall_earnings,
            "majors": prog_dicts,
            "programs": prog_dicts,
            "preferred_matches": preferred_matches,
            "count": len(prog_dicts),
        }


college_service = CollegeService()
