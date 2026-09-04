"""What-If Scenario Simulation Service."""
from typing import Any, Dict, List, Optional
from server.models.canonical import CanonicalCollege
from server.models.portfolio import (
    ScenarioOverrideRequest,
    ScenarioResult,
    StudentPortfolio,
)
from server.services.fit_scorer import fit_scorer
from server.services.scorecard import scorecard_service


class ScenarioService:
    """Executes hypothetical what-if scenario simulations in-memory without database mutation."""

    async def simulate_scenario(
        self,
        portfolio: StudentPortfolio,
        request: ScenarioOverrideRequest,
    ) -> Dict[str, Any]:
        """Apply temporary overrides, evaluate fit with fit_scorer, and compute deltas."""
        colleges_to_simulate: List[CanonicalCollege] = []

        # If a specific college_id was requested
        if request.college_id:
            cid = str(request.college_id).strip()
            # Check if in portfolio
            found = False
            for item in portfolio.colleges:
                if str(item.college_id) == cid or str(item.id) == cid:
                    col = item.college or await scorecard_service.get_college_by_id(item.college_id)
                    if col:
                        colleges_to_simulate.append(col)
                        found = True
                    break
            if not found:
                col = await scorecard_service.get_college_by_id(cid)
                if col:
                    colleges_to_simulate.append(col)
        else:
            # All saved colleges in portfolio
            for item in portfolio.colleges:
                col = item.college or await scorecard_service.get_college_by_id(item.college_id)
                if col:
                    colleges_to_simulate.append(col)

        # Clone student preferences in-memory
        temp_prefs = portfolio.preferences.model_copy(deep=True)

        if request.hypothetical_major:
            temp_prefs.preferred_majors = [request.hypothetical_major]
        if request.budget_max_annual is not None:
            temp_prefs.budget_max_annual = int(request.budget_max_annual)
        if request.gpa is not None:
            temp_prefs.gpa = float(request.gpa)
        if request.sat_score is not None:
            temp_prefs.sat_score = int(request.sat_score)
        if request.act_score is not None:
            temp_prefs.act_score = int(request.act_score)

        results: List[ScenarioResult] = []

        for college in colleges_to_simulate:
            temp_college = college.model_copy(deep=True)
            prefs_for_college = temp_prefs.model_copy(deep=True)

            # Residency adjustment
            if request.is_in_state is True:
                if college.location and college.location.state:
                    prefs_for_college.home_state = college.location.state
                if "public" in (college.control or "").lower() and college.costs and college.costs.tuition_in_state and college.costs.tuition_in_state.value:
                    if temp_college.costs and temp_college.costs.net_price_average:
                        temp_college.costs.net_price_average.value = college.costs.tuition_in_state.value
            elif request.is_in_state is False:
                prefs_for_college.home_state = "XX"
                if "public" in (college.control or "").lower() and college.costs and college.costs.tuition_out_of_state and college.costs.tuition_out_of_state.value:
                    if temp_college.costs and temp_college.costs.net_price_average:
                        temp_college.costs.net_price_average.value = college.costs.tuition_out_of_state.value

            # Financial aid override
            if request.annual_aid_amount is not None and request.annual_aid_amount > 0:
                if temp_college.costs and temp_college.costs.net_price_average and temp_college.costs.net_price_average.value is not None:
                    curr_net = temp_college.costs.net_price_average.value
                    temp_college.costs.net_price_average.value = max(0, curr_net - int(request.annual_aid_amount))

            # Run baseline vs what-if fit evaluation
            baseline_fit = fit_scorer.evaluate_college_fit(college, portfolio.preferences)
            what_if_fit = fit_scorer.evaluate_college_fit(temp_college, prefs_for_college)

            baseline_net = (
                college.costs.net_price_average.value
                if college.costs and college.costs.net_price_average and college.costs.net_price_average.value is not None
                else 25000
            )
            what_if_net = (
                temp_college.costs.net_price_average.value
                if temp_college.costs and temp_college.costs.net_price_average and temp_college.costs.net_price_average.value is not None
                else 25000
            )

            # Annual loan calculation & out-of-pocket cash commitment
            loan_amt = max(0, int(request.annual_loan_amount or 0))
            what_if_out_of_pocket = max(0, what_if_net - loan_amt)
            grad_debt = loan_amt * 4

            # Standard 10-year repayment at 5.5% annual interest rate
            r = 0.055 / 12.0
            n = 120
            if grad_debt > 0:
                monthly_loan_pay = round(grad_debt * (r * (1 + r)**n) / ((1 + r)**n - 1), 2)
            else:
                monthly_loan_pay = 0.0

            # Scorecard median debt benchmark
            scorecard_debt = 16000
            try:
                if getattr(college, "outcomes", None) and getattr(college.outcomes, "median_debt_grad", None) and college.outcomes.median_debt_grad.value:
                    scorecard_debt = int(college.outcomes.median_debt_grad.value)
            except Exception:
                pass
            scorecard_monthly_pay = round(scorecard_debt * (r * (1 + r)**n) / ((1 + r)**n - 1), 2)

            score_diff = round(what_if_fit.overall_score - baseline_fit.overall_score, 1)
            cost_diff = int(what_if_net - baseline_net)

            # Dimension score differences
            base_dims = {d.dimension: d.raw_score for d in baseline_fit.dimensions}
            dim_deltas = {}
            for d in what_if_fit.dimensions:
                base_val = base_dims.get(d.dimension, 0.0)
                dim_deltas[d.dimension] = round(d.raw_score - base_val, 1)

            res = ScenarioResult(
                college_id=str(college.id),
                college_name=college.name,
                baseline_fit_score=round(baseline_fit.overall_score, 1),
                what_if_fit_score=round(what_if_fit.overall_score, 1),
                fit_score_delta=score_diff,
                baseline_category=baseline_fit.category,
                what_if_category=what_if_fit.category,
                baseline_net_price=baseline_net,
                what_if_net_price=what_if_net,
                net_price_delta=cost_diff,
                annual_loan_amount=loan_amt,
                what_if_out_of_pocket=what_if_out_of_pocket,
                total_debt_at_graduation=grad_debt,
                estimated_monthly_payment=monthly_loan_pay,
                median_debt_scorecard=scorecard_debt,
                scorecard_monthly_loan_payment=scorecard_monthly_pay,
                dimension_deltas=dim_deltas,
                baseline={
                    "overall_score": round(baseline_fit.overall_score, 1),
                    "category": baseline_fit.category,
                    "net_price": baseline_net,
                    "breakdown": baseline_fit.to_breakdown_dict(),
                },
                scenario={
                    "overall_score": round(what_if_fit.overall_score, 1),
                    "category": what_if_fit.category,
                    "net_price": what_if_net,
                    "out_of_pocket": what_if_out_of_pocket,
                    "annual_loan": loan_amt,
                    "total_debt_grad": grad_debt,
                    "monthly_payment": monthly_loan_pay,
                    "breakdown": what_if_fit.to_breakdown_dict(),
                },
                delta={
                    "fit_score": score_diff,
                    "net_price": cost_diff,
                    "category_changed": baseline_fit.category != what_if_fit.category,
                },
            )
            results.append(res)

        results_data = [r.model_dump() for r in results]
        return {
            "results": results_data,
            "scenarios": results_data,
            "applied_overrides": request.model_dump(),
            "count": len(results_data),
        }


scenario_service = ScenarioService()
