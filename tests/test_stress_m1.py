"""Milestone 1 Backend Correctness & Adversarial Stress Tests.

Empirical verification of boundary values, edge cases, data integrity,
and error handling across all 7 Milestone 1 backend features:
- R1: Financial Aid Offer Comparison
- R2: Deadline Calendar
- R3: Essay Tracker
- R4: Admissions Chances Estimator
- R5: What-If Scenario Modeling
- R6: Alumni Outcomes Deep Dive
- R7: Per-School Requirements Checklist
"""
import json
import pytest
from server.config import settings
from server.models.canonical import CanonicalCollege, MetricField, AdmissionsData
from server.models.portfolio import (
    ApplicationTracker,
    ChecklistItem,
    FinancialAidOffer,
    PortfolioItem,
    ScenarioOverrideRequest,
    StudentPortfolio,
    StudentPreferences,
)
from server.services.aid_service import aid_service, calculate_loan_payment
from server.services.calendar_service import calendar_service
from server.services.chances_service import chances_service
from server.services.college_service import college_service
from server.services.scenario_service import scenario_service
from server.services.scorecard_client import scorecard_client
from tests.conftest import APIClient, SEED_COLLEGES


def load_college_from_seed(cid: str) -> CanonicalCollege:
    with open(settings.SEED_DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    for item in data:
        if str(item.get("id")) == str(cid) or str(item.get("unitid")) == str(cid):
            return CanonicalCollege(**item)
    raise ValueError(f"College {cid} not found in seed data")


# =============================================================================
# 1. Feature R1: Financial Aid Offer Comparison Stress Tests
# =============================================================================

def test_aid_zero_aid_equals_published_sticker():
    """When student receives zero aid, net cost must strictly equal published sticker price."""
    college = load_college_from_seed(SEED_COLLEGES["mit"]["id"])
    offer = FinancialAidOffer(
        college_id=str(college.id),
        merit_aid=0,
        need_based_grants=0,
        institutional_grants=0,
        outside_scholarships=0,
        federal_loans=0,
        work_study=0,
        custom_sticker_price=None,
    )
    metrics = offer.calculate_metrics(default_sticker_price=82000)
    assert metrics["total_grants"] == 0
    assert metrics["net_annual_cost"] == 82000
    assert metrics["four_year_total_cost"] == 328000
    assert metrics["total_debt_at_graduation"] == 0
    assert metrics["estimated_monthly_payment"] == 0.0


def test_aid_grants_exceeding_sticker_clamped_to_zero():
    """When grant aid exceeds sticker price, net annual and 4-year costs must clamp to 0."""
    offer = FinancialAidOffer(
        merit_aid=50000,
        need_based_grants=40000,
        custom_sticker_price=60000,
    )
    metrics = offer.calculate_metrics()
    assert metrics["total_grants"] == 90000
    assert metrics["net_annual_cost"] == 0
    assert metrics["four_year_total_cost"] == 0


@pytest.mark.asyncio
async def test_aid_negative_numbers_and_sticker_override_consistency():
    """Adversarial: Test aid offer with negative numbers and check sticker price vs source tag."""
    college = load_college_from_seed(SEED_COLLEGES["mit"]["id"])
    # If a negative custom_sticker_price is passed
    offer = FinancialAidOffer(
        college_id=str(college.id),
        merit_aid=-5000,
        federal_loans=-2000,
        custom_sticker_price=-15000,
    )
    comp = await aid_service.build_college_comparison(college, offer)

    # Document empirical behavior:
    # If custom_sticker_price is negative, get_college_sticker_price ignores it (returns published sticker),
    # but offer.calculate_metrics uses -15000 directly.
    # Check if sticker_price is negative or if it was sanitized:
    assert comp.total_grants == 0
    assert comp.total_self_help == 0
    # Observe the discrepancy between sticker_price and sticker_price_source:
    if comp.sticker_price < 0:
        pytest.fail(
            f"Negative custom_sticker_price was accepted ({comp.sticker_price}) while "
            f"sticker_price_source claimed '{comp.sticker_price_source}'"
        )


def test_aid_loan_amortization_boundaries():
    """Test loan payment calculation with zero, negative, and extreme loan amounts."""
    assert calculate_loan_payment(0) == 0.0
    assert calculate_loan_payment(-5000) == 0.0
    # $1,000,000 loan debt
    payment_large = calculate_loan_payment(1_000_000, apr=0.055, n_months=120)
    assert payment_large > 10000.0


# =============================================================================
# 2. Feature R4: Admissions Chances Estimator Stress Tests
# =============================================================================

def test_chances_gpa_zero_should_be_reach():
    """Adversarial: A GPA of 0.0 must be classified as Reach, never Likely or Safety."""
    osu = load_college_from_seed(SEED_COLLEGES["osu"]["id"])
    est = chances_service.estimate_chances(osu, custom_gpa=0.0)
    assert est.classification == "Reach", (
        f"Empirical Bug: Student with GPA=0.0 was classified as '{est.classification}' "
        f"with overall_probability={est.overall_probability}. Summary: '{est.summary}'"
    )


def test_chances_gpa_monotonicity_in_gap():
    """Adversarial: GPA 3.30 must not be classified higher (e.g. Likely) than GPA 3.40 (Target)."""
    osu = load_college_from_seed(SEED_COLLEGES["osu"]["id"])
    est_330 = chances_service.estimate_chances(osu, custom_gpa=3.30)
    est_340 = chances_service.estimate_chances(osu, custom_gpa=3.40)

    # In chances_service, GPA=3.30 falls into the unhandled gap [3.20, 3.40),
    # triggering the 'stats not provided' fallback which returns 'Likely',
    # while GPA=3.40 enters the 'between' tier which returns 'Target' for 53% admit rate.
    rank = {"Safety": 4, "Likely": 3, "Target": 2, "Reach": 1}
    assert rank[est_330.classification] <= rank[est_340.classification], (
        f"Empirical Bug: Inverted classification! GPA 3.30 got '{est_330.classification}' "
        f"while higher GPA 3.40 got '{est_340.classification}'"
    )


def test_chances_extreme_gpa_and_sat_values():
    """Test extreme test scores: SAT=400 (min), SAT=1600 (max), SAT=0, GPA=5.0."""
    osu = load_college_from_seed(SEED_COLLEGES["osu"]["id"])

    # SAT 400 must be below 25th percentile
    est_400 = chances_service.estimate_chances(osu, custom_sat=400)
    assert est_400.test_status["status"] == "below"
    assert est_400.classification == "Reach"

    # SAT 1600 must be above 75th percentile
    est_1600 = chances_service.estimate_chances(osu, custom_sat=1600)
    assert est_1600.test_status["status"] == "above"
    assert est_1600.classification in ["Safety", "Likely"]

    # GPA 5.0 (weighted)
    est_50 = chances_service.estimate_chances(osu, custom_gpa=5.0)
    assert est_50.classification in ["Safety", "Likely"]


def test_chances_missing_percentiles_on_college():
    """When college has no SAT/ACT percentile data, system must degrade gracefully without error."""
    osu = load_college_from_seed(SEED_COLLEGES["osu"]["id"]).model_copy(deep=True)
    osu.admissions.sat_total_25 = None
    osu.admissions.sat_total_75 = None
    osu.admissions.sat_reading_25 = None
    osu.admissions.sat_reading_75 = None
    osu.admissions.sat_math_25 = None
    osu.admissions.sat_math_75 = None
    osu.admissions.act_25 = None
    osu.admissions.act_75 = None

    est = chances_service.estimate_chances(osu, custom_sat=1450, custom_gpa=3.8)
    assert est.classification in ["Safety", "Likely", "Target", "Reach"]
    assert est.test_status["status"] == "unreported"


def test_chances_ultra_selective_invariance():
    """Invariant: Institutions with acceptance rate < 15% are ALWAYS classified as Reach."""
    for cid in [SEED_COLLEGES["mit"]["id"], SEED_COLLEGES["stanford"]["id"]]:
        col = load_college_from_seed(cid)
        # Even with perfect stats (GPA 4.0, SAT 1600, ACT 36)
        est = chances_service.estimate_chances(col, custom_gpa=4.0, custom_sat=1600, custom_act=36)
        assert est.classification == "Reach"
        assert est.overall_probability <= 0.18


# =============================================================================
# 3. Feature R5: What-If Scenario Modeling Stress Tests
# =============================================================================

@pytest.mark.asyncio
async def test_scenario_nonexistent_college_id():
    """Scenario simulation with nonexistent college ID should return empty results without crashing."""
    portfolio = StudentPortfolio(portfolio_id="test_scen_empty")
    req = ScenarioOverrideRequest(college_id="nonexistent_999999", gpa=3.8)
    res = await scenario_service.simulate_scenario(portfolio, req)
    assert res["count"] == 0
    assert res["results"] == []


@pytest.mark.asyncio
async def test_scenario_empty_overrides():
    """Scenario simulation with empty overrides should return delta 0 against baseline."""
    col = load_college_from_seed(SEED_COLLEGES["mit"]["id"])
    item = PortfolioItem(college_id=str(col.id), college_name=col.name, college=col)
    portfolio = StudentPortfolio(portfolio_id="test_scen_col", colleges=[item])

    req = ScenarioOverrideRequest()
    res = await scenario_service.simulate_scenario(portfolio, req)
    assert res["count"] == 1
    result0 = res["results"][0]
    assert result0["fit_score_delta"] == 0.0
    assert result0["net_price_delta"] == 0


@pytest.mark.asyncio
async def test_scenario_negative_budget_does_not_crash():
    """Scenario simulation with negative budget must not raise 500 error."""
    col = load_college_from_seed(SEED_COLLEGES["osu"]["id"])
    item = PortfolioItem(college_id=str(col.id), college_name=col.name, college=col)
    portfolio = StudentPortfolio(portfolio_id="test_scen_neg", colleges=[item])

    req = ScenarioOverrideRequest(budget_max_annual=-5000)
    res = await scenario_service.simulate_scenario(portfolio, req)
    assert res["count"] == 1
    assert "what_if_fit_score" in res["results"][0]


# =============================================================================
# 4. Feature R3: Essay Tracker Stress Tests
# =============================================================================

def test_essay_tracker_word_boundaries_and_status_transitions():
    """Test essay with 0 words, exceeding word limit, and all draft status transitions."""
    client = APIClient()

    # 1. Create with 0 words
    res1 = client.post("/api/portfolio/essays", json={
        "title": "Boundary Essay",
        "prompt": "Why our school?",
        "word_limit": 250,
        "current_word_count": 0,
        "draft_status": "Not Started",
    })
    assert res1.status_code == 200
    essay_id = res1.json()["id"]
    assert res1.json()["word_count"] == 0
    assert res1.json()["status"] == "Not Started"

    # 2. Exceeding word limit (350 words for a 250 limit)
    res2 = client.put(f"/api/portfolio/essays/{essay_id}", json={
        "current_word_count": 350,
        "draft_status": "Drafting",
    })
    assert res2.status_code == 200
    assert res2.json()["word_count"] == 350

    # 3. Transitions: Drafting -> Reviewing -> Final
    res3 = client.put(f"/api/portfolio/essays/{essay_id}", json={"draft_status": "Reviewing"})
    assert res3.status_code == 200
    assert res3.json()["status"] == "Reviewing"

    res4 = client.put(f"/api/portfolio/essays/{essay_id}", json={"draft_status": "Final"})
    assert res4.status_code == 200
    assert res4.json()["status"] == "Final"

    # 4. Empty prompt string
    res5 = client.post("/api/portfolio/essays", json={
        "title": "Empty Prompt",
        "prompt": "",
    })
    assert res5.status_code == 200


def test_essay_missing_prompt_status_code():
    """Adversarial: Missing required prompt must return 422 Unprocessable Entity, NEVER 500."""
    client = APIClient()
    res = client.post("/api/portfolio/essays", json={"title": "Missing Prompt Essay"})
    assert res.status_code in [400, 422], (
        f"Empirical Bug: Missing required field returned HTTP {res.status_code} instead of 422/400. Body: {res.text}"
    )


def test_scenario_malformed_type_status_code():
    """Adversarial: Passing malformed data type to scenario endpoint must return 422/400, NEVER 500."""
    client = APIClient()
    res = client.post("/api/portfolio/scenario", json={"annual_aid_amount": "not-an-integer"})
    assert res.status_code in [400, 422], (
        f"Empirical Bug: Invalid type in scenario payload returned HTTP {res.status_code} instead of 422/400. Body: {res.text}"
    )


def test_aid_malformed_type_status_code():
    """Adversarial: Passing malformed data type to aid offer endpoint must return 422/400, NEVER 500."""
    client = APIClient()
    cid = SEED_COLLEGES["mit"]["id"]
    client.post("/api/portfolio/colleges", json={"college_id": cid})
    res = client.post(f"/api/portfolio/aid/{cid}", json={"merit_aid": "not-an-integer"})
    assert res.status_code in [400, 422], (
        f"Empirical Bug: Invalid type in aid offer payload returned HTTP {res.status_code} instead of 422/400. Body: {res.text}"
    )


# =============================================================================
# 5. Feature R2: Deadline Calendar Stress Tests
# =============================================================================

def test_calendar_aggregation_boundaries():
    """Test calendar aggregation with no colleges, colleges without deadlines, and invalid date formats."""
    # 1. No saved colleges
    empty_p = StudentPortfolio(portfolio_id="cal_empty")
    res1 = calendar_service.get_portfolio_calendar(empty_p)
    assert res1["total_events"] == 0
    assert res1["events"] == []

    # 2. College with no deadlines
    col = load_college_from_seed(SEED_COLLEGES["mit"]["id"])
    item_no_dl = PortfolioItem(college_id=str(col.id), college_name=col.name, tracker=ApplicationTracker())
    res2 = calendar_service.get_portfolio_calendar(StudentPortfolio(portfolio_id="cal_no_dl", colleges=[item_no_dl]))
    assert res2["total_events"] == 0

    # 3. College with corrupted / invalid date strings
    corrupted_tracker = ApplicationTracker(
        priority_deadline="corrupted-date",
        regular_deadline="9999-99-99",
        fafsa_deadline="2025/12/31",  # slash format
        scholarship_deadlines={"Malformed": "invalid"},
    )
    item_corrupt = PortfolioItem(college_id=str(col.id), college_name=col.name, tracker=corrupted_tracker)
    res3 = calendar_service.get_portfolio_calendar(StudentPortfolio(portfolio_id="cal_corrupt", colleges=[item_corrupt]))
    # Must silently ignore malformed dates without throwing exceptions
    assert res3["total_events"] == 0


# =============================================================================
# 6. Feature R7: Per-School Requirements Checklist Stress Tests
# =============================================================================

def test_checklist_toggle_nonexistent_item_returns_404():
    """Toggling a nonexistent checklist item must return 404."""
    client = APIClient()
    cid = SEED_COLLEGES["mit"]["id"]
    client.post("/api/portfolio/colleges", json={"college_id": cid})

    res = client.put(f"/api/portfolio/tracker/{cid}/checklist/nonexistent_chk_id", json={"completed": True})
    assert res.status_code == 404


def test_checklist_missing_required_name_status_code():
    """Adversarial: Creating a checklist item without name must return 422/400, NEVER 500."""
    client = APIClient()
    cid = SEED_COLLEGES["mit"]["id"]
    client.post("/api/portfolio/colleges", json={"college_id": cid})

    res = client.post(f"/api/portfolio/tracker/{cid}/checklist", json={"required": True})
    assert res.status_code in [400, 422], (
        f"Empirical Bug: Checklist creation without name returned HTTP {res.status_code} instead of 422/400. Body: {res.text}"
    )


def test_checklist_duplicate_item_names_matrix_shadowing():
    """Adversarial: Adding duplicate item names must not shadow completion status in cross-school matrix."""
    client = APIClient()
    cid = SEED_COLLEGES["mit"]["id"]
    client.post("/api/portfolio/colleges", json={"college_id": cid})

    # Add duplicate custom requirement
    res1 = client.post(f"/api/portfolio/tracker/{cid}/checklist", json={"name": "Audition Video", "required": True})
    assert res1.status_code == 200
    id1 = res1.json()["id"]

    res2 = client.post(f"/api/portfolio/tracker/{cid}/checklist", json={"name": "Audition Video", "required": True})
    assert res2.status_code == 200
    id2 = res2.json()["id"]

    # Mark first item as completed
    client.put(f"/api/portfolio/tracker/{cid}/checklist/{id1}", json={"completed": True})

    # In matrix, check if completed_count reflects the completed item
    matrix = client.get("/api/portfolio/requirements-matrix").json()
    row = next((r for r in matrix["matrix"] if r["name"] == "Audition Video"), None)
    assert row is not None

    # If duplicate items with the same name are allowed, the matrix shouldn't show 0 completed
    # when one of them was marked complete
    assert row["completed_count"] >= 1, (
        f"Empirical Bug: Matrix completed_count was 0 despite item {id1} being completed. "
        f"Second item {id2} shadowed it."
    )
