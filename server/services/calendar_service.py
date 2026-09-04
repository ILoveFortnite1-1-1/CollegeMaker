"""Deadline Calendar Aggregation & Scheduling Service."""
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from server.models.portfolio import StudentPortfolio


class CalendarService:
    """Aggregates all college application and aid deadlines across saved colleges."""

    def get_portfolio_calendar(
        self,
        portfolio: StudentPortfolio,
        reference_date: Optional[date] = None,
        auto_populate_defaults: bool = False,
    ) -> Dict[str, Any]:
        """Collect all deadlines across saved colleges, sort chronologically, and find 14-day upcoming events."""
        today = reference_date or datetime.now(timezone.utc).date()
        events: List[Dict[str, Any]] = []
        colleges_with_deadlines = set()

        for item in portfolio.colleges:
            cid = str(item.id or item.college_id)
            cname = item.canonical_name or item.college_name
            tracker = item.tracker

            if not tracker:
                continue

            college_had_deadline = False

            # Helper to add event
            def _add_event(
                evt_key: str,
                title: str,
                raw_date: Optional[str],
                deadline_type: str,
                color: str,
                category_label: str,
            ):
                nonlocal college_had_deadline
                if not raw_date or not isinstance(raw_date, str):
                    return
                date_str = raw_date.strip()
                if not date_str:
                    return
                # Extract YYYY-MM-DD
                try:
                    clean_date_str = date_str[:10]
                    d = datetime.strptime(clean_date_str, "%Y-%m-%d").date()
                except Exception:
                    return

                college_had_deadline = True
                days_remaining = (d - today).days
                is_past = days_remaining < 0

                events.append({
                    "id": f"evt_{cid}_{evt_key}",
                    "college_id": cid,
                    "college_name": cname,
                    "title": title,
                    "date": clean_date_str,
                    "deadline_type": deadline_type,
                    "type": deadline_type,
                    "category": deadline_type,
                    "category_label": category_label,
                    "color": color,
                    "days_remaining": days_remaining,
                    "is_past": is_past,
                })

            # Priority Application Deadline
            if tracker.priority_deadline:
                _add_event("priority", "Priority Application Deadline", tracker.priority_deadline, "app_deadline", "#2563eb", "Application Deadline")

            # Regular Application Deadline
            if tracker.regular_deadline:
                _add_event("regular", "Regular Decision Deadline", tracker.regular_deadline, "app_deadline", "#2563eb", "Application Deadline")

            # FAFSA Deadline
            if getattr(tracker, "fafsa_deadline", None):
                _add_event("fafsa", "FAFSA Financial Aid Deadline", tracker.fafsa_deadline, "financial_aid", "#059669", "Financial Aid")

            # CSS Profile Deadline
            if getattr(tracker, "css_profile_deadline", None):
                _add_event("css_profile", "CSS Profile Deadline", tracker.css_profile_deadline, "financial_aid", "#059669", "Financial Aid")

            # Decision Date
            if getattr(tracker, "decision_date", None):
                _add_event("decision", "Admissions Decision Notification", tracker.decision_date, "decision", "#7c3aed", "Decision Date")

            # Scholarship Deadlines
            scholarships = getattr(tracker, "scholarship_deadlines", None)
            if isinstance(scholarships, dict):
                for idx, (s_name, s_date) in enumerate(scholarships.items()):
                    safe_key = f"sch_{idx}"
                    _add_event(safe_key, f"{s_name} Deadline", s_date, "scholarship", "#d97706", "Scholarship")
            elif isinstance(scholarships, list):
                for idx, s_item in enumerate(scholarships):
                    if isinstance(s_item, dict):
                        name = s_item.get("name", f"Scholarship #{idx+1}")
                        s_date = s_item.get("deadline")
                        _add_event(f"sch_{idx}", f"{name} Deadline", s_date, "scholarship", "#d97706", "Scholarship")

            if not college_had_deadline and auto_populate_defaults:
                # Automatically pull important standard dates for the college so calendar doesn't start empty
                app_fall_year = today.year if today.month >= 8 else today.year - 1
                spring_year = app_fall_year + 1

                cname_str = (cname or "").lower()
                is_private = bool(item.college and getattr(item.college, "control", None) and "private" in str(item.college.control).lower())
                is_uc_or_csu = "university of california" in cname_str or "california state" in cname_str

                # Priority / Early Action Deadline
                p_date = f"{app_fall_year}-11-30" if is_uc_or_csu else f"{app_fall_year}-11-01"
                _add_event("priority", "Priority / Early Action Deadline", p_date, "app_deadline", "#2563eb", "Application Deadline")

                # Regular Decision Deadline
                r_date = f"{spring_year}-01-05" if is_private else f"{spring_year}-01-15"
                _add_event("regular", "Regular Decision Deadline", r_date, "app_deadline", "#2563eb", "Application Deadline")

                # Merit Scholarship Priority Deadline
                _add_event("sch_merit", "Merit Scholarship Priority Deadline", f"{app_fall_year}-12-01", "scholarship", "#d97706", "Scholarship")

                # FAFSA Priority Deadline
                _add_event("fafsa", "FAFSA Financial Aid Priority Deadline", f"{spring_year}-02-01", "financial_aid", "#059669", "Financial Aid")

                # CSS Profile Deadline (for private / selective institutions)
                if is_private:
                    _add_event("css_profile", "CSS Profile Financial Aid Deadline", f"{spring_year}-01-15", "financial_aid", "#059669", "Financial Aid")

                # Admissions Decision Notification
                dec_date = f"{spring_year}-03-25" if is_uc_or_csu else f"{spring_year}-03-31"
                _add_event("decision", "Admissions Decision Notification", dec_date, "decision", "#7c3aed", "Decision Date")

            if college_had_deadline:
                colleges_with_deadlines.add(cid)

        # Sort chronologically by date
        events.sort(key=lambda e: (e["date"], e["college_name"]))

        # Upcoming 14 days
        upcoming_14_days = [
            e for e in events
            if 0 <= e["days_remaining"] <= 14
        ]

        national_milestones = self.get_national_milestones(today)

        return {
            "events": events,
            "upcoming_14_days": upcoming_14_days,
            "total_events": len(events),
            "colleges_with_deadlines": len(colleges_with_deadlines),
            "national_milestones": national_milestones,
        }

    def get_national_milestones(self, reference_date: Optional[date] = None) -> List[Dict[str, Any]]:
        """Standard national admissions, financial aid, and decision roadmap dates for current cycle."""
        today = reference_date or datetime.now(timezone.utc).date()
        app_fall_year = today.year if today.month >= 8 else today.year - 1
        spring_year = app_fall_year + 1

        milestones = [
            {
                "id": f"nat_common_app_open_{app_fall_year}",
                "college_id": "national",
                "college_name": "National Admissions",
                "title": "Common Application Opens for Fall Admissions",
                "date": f"{app_fall_year}-08-01",
                "deadline_type": "app_deadline",
                "type": "app_deadline",
                "category": "app_deadline",
                "category_label": "Application Milestone",
                "color": "#2563eb",
                "is_national": True,
            },
            {
                "id": f"nat_early_action_{app_fall_year}",
                "college_id": "national",
                "college_name": "National Admissions",
                "title": "National Early Action / Early Decision Milestone",
                "date": f"{app_fall_year}-11-01",
                "deadline_type": "app_deadline",
                "type": "app_deadline",
                "category": "app_deadline",
                "category_label": "Application Deadline",
                "color": "#2563eb",
                "is_national": True,
            },
            {
                "id": f"nat_uc_deadline_{app_fall_year}",
                "college_id": "national",
                "college_name": "National Admissions",
                "title": "UC & Cal State Application Submission Deadline",
                "date": f"{app_fall_year}-11-30",
                "deadline_type": "app_deadline",
                "type": "app_deadline",
                "category": "app_deadline",
                "category_label": "Application Deadline",
                "color": "#2563eb",
                "is_national": True,
            },
            {
                "id": f"nat_fafsa_open_{app_fall_year}",
                "college_id": "national",
                "college_name": "Federal Student Aid",
                "title": "Federal FAFSA Application Opens (Financial Aid)",
                "date": f"{app_fall_year}-12-01",
                "deadline_type": "financial_aid",
                "type": "financial_aid",
                "category": "financial_aid",
                "category_label": "Financial Aid",
                "color": "#059669",
                "is_national": True,
            },
            {
                "id": f"nat_regular_decision_{spring_year}",
                "college_id": "national",
                "college_name": "National Admissions",
                "title": "National Regular Decision Standard Deadline",
                "date": f"{spring_year}-01-01",
                "deadline_type": "app_deadline",
                "type": "app_deadline",
                "category": "app_deadline",
                "category_label": "Application Deadline",
                "color": "#2563eb",
                "is_national": True,
            },
            {
                "id": f"nat_css_profile_{spring_year}",
                "college_id": "national",
                "college_name": "College Board",
                "title": "CSS Profile Priority Financial Aid Milestone",
                "date": f"{spring_year}-01-15",
                "deadline_type": "financial_aid",
                "type": "financial_aid",
                "category": "financial_aid",
                "category_label": "Financial Aid",
                "color": "#059669",
                "is_national": True,
            },
            {
                "id": f"nat_fafsa_priority_{spring_year}",
                "college_id": "national",
                "college_name": "Federal Student Aid",
                "title": "National FAFSA Financial Aid Priority Deadline",
                "date": f"{spring_year}-02-01",
                "deadline_type": "financial_aid",
                "type": "financial_aid",
                "category": "financial_aid",
                "category_label": "Financial Aid",
                "color": "#059669",
                "is_national": True,
            },
            {
                "id": f"nat_ivy_day_{spring_year}",
                "college_id": "national",
                "college_name": "National Admissions",
                "title": "National Regular Admissions Notifications (Ivy Day Release)",
                "date": f"{spring_year}-03-31",
                "deadline_type": "decision",
                "type": "decision",
                "category": "decision",
                "category_label": "Decision Notification",
                "color": "#7c3aed",
                "is_national": True,
            },
            {
                "id": f"nat_decision_day_{spring_year}",
                "college_id": "national",
                "college_name": "National Admissions",
                "title": "National College Decision Day (Deposit Due)",
                "date": f"{spring_year}-05-01",
                "deadline_type": "decision",
                "type": "decision",
                "category": "decision",
                "category_label": "Decision Day",
                "color": "#7c3aed",
                "is_national": True,
            },
        ]

        for m in milestones:
            d = datetime.strptime(m["date"], "%Y-%m-%d").date()
            m["days_remaining"] = (d - today).days
            m["is_past"] = m["days_remaining"] < 0

        milestones.sort(key=lambda x: x["date"])
        return milestones


calendar_service = CalendarService()
