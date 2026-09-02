"""Multi-College Side-by-Side Comparison Engine."""
from typing import Any, Dict, List, Optional
from server.models.canonical import CanonicalCollege
from server.models.portfolio import StudentPreferences
from server.services.fit_scorer import fit_scorer
from server.services.scorecard import scorecard_service


class ComparisonService:
    """Builds normalized comparison matrices and best-in-class highlights for 2–6 colleges."""

    async def compare_colleges(
        self,
        college_ids: List[str],
        preferences: Optional[StudentPreferences] = None,
    ) -> Dict[str, Any]:
        """Generate normalized comparison data across 2 to 6 colleges."""
        if not college_ids or len(college_ids) < 2:
            raise ValueError("Comparison requires at least 2 college IDs.")
        if len(college_ids) > 6:
            raise ValueError("Comparison supports a maximum of 6 colleges simultaneously.")

        colleges: List[CanonicalCollege] = []
        for cid in college_ids:
            college = await scorecard_service.get_college_by_id(cid.strip())
            if college:
                # Apply fit scoring
                fit_res = fit_scorer.evaluate_college_fit(college, preferences)
                college.fit_score = fit_res.overall_score
                college.fit_category = fit_res.category
                college.fit_breakdown = fit_res.model_dump()
                colleges.append(college)

        if len(colleges) < 2:
            raise ValueError("Could not find at least 2 valid colleges for comparison.")

        # Build comparison metrics matrix
        metrics = self._build_metrics_matrix(colleges)

        # Calculate Best-in-Class awards
        best_in_class = self._calculate_best_in_class(colleges)

        # Build comparative summary
        summary = self._generate_comparative_summary(colleges, best_in_class)

        return {
            "colleges": colleges,
            "metrics": metrics,
            "best_in_class": best_in_class,
            "summary": summary,
        }

    def _build_metrics_matrix(self, colleges: List[CanonicalCollege]) -> Dict[str, List[Dict[str, Any]]]:
        """Construct normalized metric rows grouped by category."""
        def get_val(obj, default=None):
            if obj is not None and hasattr(obj, "value") and obj.value is not None:
                return obj.value
            return default

        def format_sat(c):
            s25 = get_val(c.admissions.sat_total_25)
            s75 = get_val(c.admissions.sat_total_75)
            if s25 and s75:
                return f"{s25} - {s75}"
            return "N/A"

        def format_act(c):
            a25 = get_val(c.admissions.act_25)
            a75 = get_val(c.admissions.act_75)
            if a25 and a75:
                return f"{a25} - {a75}"
            return "N/A"

        def format_fee(c):
            fee = get_val(c.admissions.application_fee)
            return f"${fee}" if fee is not None else "Free"

        def format_currency(val):
            return f"${val:,}" if val is not None else "N/A"

        def format_percent(val):
            return f"{round(val * 100, 1)}%" if val is not None else "N/A"

        return {
            "Overview": [
                {
                    "label": "Location",
                    "values": {c.id: f"{c.location.city}, {c.location.state}" for c in colleges},
                },
                {
                    "label": "Setting",
                    "values": {c.id: c.location.location_type for c in colleges},
                },
                {
                    "label": "Institution Type",
                    "values": {c.id: c.control.replace("_", " ").title() for c in colleges},
                },
                {
                    "label": "Undergraduate Size",
                    "values": {
                        c.id: f"{get_val(c.undergrad_size):,}" if get_val(c.undergrad_size) is not None else "N/A"
                        for c in colleges
                    },
                },
            ],
            "Admissions": [
                {
                    "label": "Acceptance Rate",
                    "values": {
                        c.id: format_percent(get_val(c.admissions.acceptance_rate)) for c in colleges
                    },
                },
                {
                    "label": "SAT Middle 50%",
                    "values": {c.id: format_sat(c) for c in colleges},
                },
                {
                    "label": "ACT Middle 50%",
                    "values": {c.id: format_act(c) for c in colleges},
                },
                {
                    "label": "Application Fee",
                    "values": {c.id: format_fee(c) for c in colleges},
                },
            ],
            "Costs & Financial Aid": [
                {
                    "label": "Average Annual Net Price",
                    "values": {
                        c.id: format_currency(get_val(c.costs.net_price_average)) for c in colleges
                    },
                },
                {
                    "label": "In-State Tuition",
                    "values": {
                        c.id: format_currency(get_val(c.costs.tuition_in_state)) for c in colleges
                    },
                },
                {
                    "label": "Out-of-State Tuition",
                    "values": {
                        c.id: format_currency(get_val(c.costs.tuition_out_of_state)) for c in colleges
                    },
                },
                {
                    "label": "Room & Board",
                    "values": {
                        c.id: format_currency(get_val(c.costs.room_and_board)) for c in colleges
                    },
                },
                {
                    "label": "Net Price ($0 - $30k Income)",
                    "values": {
                        c.id: format_currency(get_val(c.costs.net_price_income_0_30k)) for c in colleges
                    },
                },
                {
                    "label": "Net Price ($48k - $75k Income)",
                    "values": {
                        c.id: format_currency(get_val(c.costs.net_price_income_48k_75k)) for c in colleges
                    },
                },
            ],
            "Academic & Career Outcomes": [
                {
                    "label": "6-Year Graduation Rate",
                    "values": {
                        c.id: format_percent(get_val(c.outcomes.completion_rate_6yr)) for c in colleges
                    },
                },
                {
                    "label": "Median 10-Yr Earnings",
                    "values": {
                        c.id: format_currency(get_val(c.outcomes.median_earnings_10yr)) for c in colleges
                    },
                },
                {
                    "label": "First-Year Retention Rate",
                    "values": {
                        c.id: format_percent(get_val(c.outcomes.retention_rate_ft)) for c in colleges
                    },
                },
                {
                    "label": "Faculty-to-Student Ratio",
                    "values": {
                        c.id: get_val(c.faculty_to_student_ratio, "N/A") for c in colleges
                    },
                },
            ],
            "Fit & Classification": [
                {
                    "label": "Overall Fit Score",
                    "values": {c.id: f"{c.fit_score}/100" if c.fit_score is not None else "N/A" for c in colleges},
                },
                {
                    "label": "Admissions Classification",
                    "values": {c.id: c.fit_category or "Target" for c in colleges},
                },
            ],
        }

    def _calculate_best_in_class(self, colleges: List[CanonicalCollege]) -> Dict[str, Dict[str, Any]]:
        """Identify standout colleges for key metrics."""
        # 1. Lowest Net Price
        valid_price = [
            c for c in colleges if c.costs.net_price_average and c.costs.net_price_average.value
        ]
        best_price = min(valid_price, key=lambda c: c.costs.net_price_average.value) if valid_price else None

        # 2. Highest Earnings
        valid_earnings = [
            c for c in colleges if c.outcomes.median_earnings_10yr and c.outcomes.median_earnings_10yr.value
        ]
        best_earnings = (
            max(valid_earnings, key=lambda c: c.outcomes.median_earnings_10yr.value) if valid_earnings else None
        )

        # 3. Highest Graduation Rate
        valid_grad = [
            c for c in colleges if c.outcomes.completion_rate_6yr and c.outcomes.completion_rate_6yr.value
        ]
        best_grad = max(valid_grad, key=lambda c: c.outcomes.completion_rate_6yr.value) if valid_grad else None

        # 4. Highest Fit Score
        valid_fit = [c for c in colleges if c.fit_score is not None]
        best_fit = max(valid_fit, key=lambda c: c.fit_score) if valid_fit else None

        return {
            "lowest_net_price": {
                "college_id": best_price.id,
                "college_name": best_price.name,
                "value": f"${best_price.costs.net_price_average.value:,}/yr",
            }
            if best_price
            else None,
            "highest_earnings": {
                "college_id": best_earnings.id,
                "college_name": best_earnings.name,
                "value": f"${best_earnings.outcomes.median_earnings_10yr.value:,}/yr",
            }
            if best_earnings
            else None,
            "highest_graduation_rate": {
                "college_id": best_grad.id,
                "college_name": best_grad.name,
                "value": f"{int(best_grad.outcomes.completion_rate_6yr.value * 100)}%",
            }
            if best_grad
            else None,
            "highest_fit_score": {
                "college_id": best_fit.id,
                "college_name": best_fit.name,
                "value": f"{best_fit.fit_score}/100",
            }
            if best_fit
            else None,
        }

    def _generate_comparative_summary(
        self,
        colleges: List[CanonicalCollege],
        best: Dict[str, Any],
    ) -> str:
        """Create a human-readable comparative summary statement."""
        parts = []
        if best.get("highest_fit_score"):
            parts.append(
                f"**{best['highest_fit_score']['college_name']}** aligns best with your profile preferences ({best['highest_fit_score']['value']})."
            )
        if best.get("lowest_net_price"):
            parts.append(
                f"**{best['lowest_net_price']['college_name']}** offers the lowest annual net price at {best['lowest_net_price']['value']}."
            )
        if best.get("highest_earnings"):
            parts.append(
                f"**{best['highest_earnings']['college_name']}** leads in post-graduation median earnings at {best['highest_earnings']['value']}."
            )
        return " ".join(parts)


comparison_service = ComparisonService()
