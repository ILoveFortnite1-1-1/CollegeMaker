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

            if college_had_deadline:
                colleges_with_deadlines.add(cid)

        # Sort chronologically by date
        events.sort(key=lambda e: (e["date"], e["college_name"]))

        # Upcoming 14 days
        upcoming_14_days = [
            e for e in events
            if 0 <= e["days_remaining"] <= 14
        ]

        return {
            "events": events,
            "upcoming_14_days": upcoming_14_days,
            "total_events": len(events),
            "colleges_with_deadlines": len(colleges_with_deadlines),
        }


calendar_service = CalendarService()
