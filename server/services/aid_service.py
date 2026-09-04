"""Financial Aid Comparison & Loan Amortization Service."""
from typing import Any, Dict, List, Optional
from server.models.canonical import CanonicalCollege
from server.models.portfolio import (
    CollegeAidComparison,
    FinancialAidOffer,
    StudentPortfolio,
    StudentPreferences,
)
from server.services.scorecard import scorecard_service


def calculate_loan_payment(total_loan_debt: float, apr: float = 0.055, n_months: int = 120) -> float:
    """Calculate 10-year monthly loan payment using standard amortization formula."""
    p = float(total_loan_debt)
    if p <= 0:
        return 0.0
    r = float(apr) / 12.0
    if r <= 0:
        return round(p / float(n_months), 2)
    factor = (1.0 + r) ** n_months
    monthly = p * (r * factor) / (factor - 1.0)
    return round(monthly, 2)


def get_college_sticker_price(
    college: CanonicalCollege,
    preferences: Optional[StudentPreferences] = None,
    offer: Optional[FinancialAidOffer] = None,
) -> tuple[int, str]:
    """Derive appropriate published sticker price (or custom override) with provenance source."""
    if offer and offer.custom_sticker_price is not None and offer.custom_sticker_price > 0:
        return int(offer.custom_sticker_price), "User Override"

    costs = getattr(college, "costs", None)
    if not costs:
        return 25000, "Estimated National Baseline"

    home_state = preferences.home_state if preferences and preferences.home_state else None
    coll_state = college.location.state if college.location and college.location.state else None
    is_public = "public" in (college.control or "").lower()

    tuition_val = None
    source_tag = "Scorecard Data"
    if is_public and home_state and coll_state and home_state.strip().upper() == coll_state.strip().upper():
        if costs.tuition_in_state and costs.tuition_in_state.value:
            tuition_val = costs.tuition_in_state.value
            source_tag = "Scorecard In-State Tuition + Living"
    else:
        if costs.tuition_out_of_state and costs.tuition_out_of_state.value:
            tuition_val = costs.tuition_out_of_state.value
            source_tag = "Scorecard Out-of-State Tuition + Living" if is_public else "Scorecard Private Tuition + Living"

    if tuition_val is not None:
        rb = costs.room_and_board.value if costs.room_and_board and costs.room_and_board.value else 13000
        books = costs.books_supplies.value if costs.books_supplies and costs.books_supplies.value else 1200
        return int(tuition_val + rb + books), source_tag

    if costs.net_price_average and costs.net_price_average.value:
        return int(costs.net_price_average.value), "Scorecard Net Price Average"

    return 25000, "Estimated National Baseline"


def get_scorecard_median_debt(college: CanonicalCollege) -> int:
    """Retrieve Scorecard median debt at graduation or standard national benchmark."""
    try:
        if getattr(college, "outcomes", None) and getattr(college.outcomes, "median_debt_grad", None) and college.outcomes.median_debt_grad.value:
            return int(college.outcomes.median_debt_grad.value)
    except Exception:
        pass
    return 16000


def calculate_monthly_loan_payment(total_debt: float, apr: float = 0.055, n_months: int = 120) -> float:
    """Standard 10-year monthly loan repayment formula at specified APR."""
    if total_debt <= 0:
        return 0.0
    r = apr / 12.0
    factor = (1.0 + r) ** n_months
    monthly = total_debt * (r * factor) / (factor - 1.0)
    return round(monthly, 2)


class AidService:
    """Evaluates and compares financial aid packages across colleges."""

    async def build_college_comparison(
        self,
        college: CanonicalCollege,
        offer: Optional[FinancialAidOffer] = None,
        preferences: Optional[StudentPreferences] = None,
    ) -> CollegeAidComparison:
        sticker, sticker_source = get_college_sticker_price(college, preferences, offer)
        offer_obj = offer or FinancialAidOffer(college_id=college.id)
        metrics = offer_obj.calculate_metrics(default_sticker_price=sticker)

        scorecard_debt = get_scorecard_median_debt(college)
        scorecard_monthly = calculate_monthly_loan_payment(scorecard_debt)
        metrics["median_debt_scorecard"] = scorecard_debt
        metrics["scorecard_monthly_loan_payment"] = scorecard_monthly

        return CollegeAidComparison(
            college_id=str(college.id),
            college_name=college.name,
            has_offer=bool(
                offer
                and (
                    offer.total_grants > 0
                    or offer.federal_loans > 0
                    or offer.work_study > 0
                    or offer.custom_sticker_price is not None
                )
            ),
            sticker_price=int(metrics["sticker_price"]),
            sticker_price_source=sticker_source,
            total_grants=int(metrics["total_grants"]),
            total_self_help=int(metrics["total_self_help"]),
            net_annual_cost=int(metrics["net_annual_cost"]),
            four_year_total_cost=int(metrics["four_year_total_cost"]),
            annual_out_of_pocket=int(metrics.get("annual_out_of_pocket", metrics["net_annual_cost"])),
            four_year_out_of_pocket=int(metrics.get("four_year_out_of_pocket", metrics["four_year_total_cost"])),
            federal_loans=int(metrics.get("federal_loans", offer_obj.federal_loans or 0)),
            total_debt_at_graduation=int(metrics["total_debt_at_graduation"]),
            estimated_monthly_payment=float(metrics["estimated_monthly_payment"]),
            monthly_loan_payment=float(metrics["monthly_loan_payment"]),
            median_debt_scorecard=scorecard_debt,
            scorecard_monthly_loan_payment=scorecard_monthly,
            offer=offer_obj,
            metrics=metrics,
        )

    async def get_portfolio_aid_comparison(self, portfolio: StudentPortfolio) -> Dict[str, Any]:
        """Aggregate aid comparisons for all saved colleges, highlight best value school."""
        comparisons: List[CollegeAidComparison] = []

        for item in portfolio.colleges:
            college = item.college
            if not college:
                college = await scorecard_service.get_college_by_id(item.college_id)
            if not college:
                continue

            offer = portfolio.aid_offers.get(str(item.college_id)) or getattr(item, "aid_offer", None)
            comp = await self.build_college_comparison(college, offer, portfolio.preferences)
            comparisons.append(comp)

        best_value_id = None
        schools_with_offers = [c for c in comparisons if c.has_offer]
        pool = schools_with_offers if schools_with_offers else comparisons

        if pool:
            sorted_pool = sorted(pool, key=lambda c: c.net_annual_cost)
            best_value_id = sorted_pool[0].college_id
            for c in comparisons:
                if c.college_id == best_value_id:
                    c.is_best_value = True

        comp_dicts = [c.model_dump() for c in comparisons]

        active_loans = [c.estimated_monthly_payment for c in comparisons if c.estimated_monthly_payment > 0]
        avg_monthly = round(sum(active_loans) / len(active_loans), 2) if active_loans else 0.0
        bench_monthly = round(sum(c.scorecard_monthly_loan_payment or 0 for c in comparisons) / len(comparisons), 2) if comparisons else 0.0

        return {
            "colleges": comp_dicts,
            "schools": comp_dicts,
            "best_value_college_id": best_value_id,
            "count_with_offers": len(schools_with_offers),
            "total_schools": len(comparisons),
            "average_monthly_loan_payment": avg_monthly,
            "benchmark_monthly_loan_payment": bench_monthly,
        }


aid_service = AidService()

