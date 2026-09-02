"""
Tier 5: Adversarial & Stress Test Suite
Targets:
1. 8-dimension fit scoring math under extreme/adversarial boundary conditions.
2. Missing data normalization, graceful fallback, and confidence integrity.
3. Reach / Target / Likely categorization stability and probability boundary invariants.
4. Scale & Portfolio Lifecycle: 50+ colleges, note/tag mutations, weight recalculations,
   complete clearance, session isolation, and SQLite database hygiene.
"""

import json
import sqlite3
import pytest
from server.config import settings
from server.models.canonical import (
    AdmissionsData,
    CanonicalCollege,
    ConfidenceLevel,
    CostData,
    Location,
    MetricField,
    OutcomesData,
    SourceType,
)
from server.models.portfolio import (
    FitWeights,
    StudentPreferences,
)
from server.services.fit_scorer import fit_scorer
from tests.conftest import APIClient


def get_seed_college(cid: str) -> CanonicalCollege:
    """Synchronously load a college from the bundled seed dataset."""
    with open(settings.SEED_DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    for item in data:
        if str(item.get("id")) == str(cid) or str(item.get("unitid")) == str(cid):
            return CanonicalCollege(**item)
    raise ValueError(f"Seed college {cid} not found")


# ==============================================================================
# SECTION 1: 8-Dimension Fit Scoring Math & Extreme Boundary Inputs
# ==============================================================================

def test_fit_weights_all_zero_normalization():
    """Adversarial Case: All 8 weights set to 0.0 must normalize equally (1/8 each) and not divide by zero."""
    weights = FitWeights(
        career=0.0,
        roi=0.0,
        academic=0.0,
        admissions=0.0,
        experience=0.0,
        strength=0.0,
        location=0.0,
        cost=0.0,
    )
    norm = weights.normalized()
    assert len(norm) == 8
    total = sum(norm.values())
    assert abs(total - 1.0) < 1e-5
    for k, v in norm.items():
        assert abs(v - 0.125) < 1e-5


@pytest.mark.parametrize("dim_name", [
    "career", "roi", "academic", "admissions", "experience", "strength", "location", "cost"
])
def test_fit_weights_single_weight_100_percent(dim_name):
    """Adversarial Case: Single weight 100%, all others 0%. The overall score must match that dimension's raw score."""
    kwargs = {d: 0.0 for d in ["career", "roi", "academic", "admissions", "experience", "strength", "location", "cost"]}
    kwargs[dim_name] = 100.0
    weights = FitWeights(**kwargs)
    prefs = StudentPreferences(weights=weights)

    college = get_seed_college("166683")  # MIT
    analysis = fit_scorer.evaluate_college_fit(college, prefs)
    norm = analysis.normalized_weights_used
    assert abs(norm[dim_name] - 1.0) < 1e-5

    target_dim = next(d for d in analysis.dimensions if d.dimension == dim_name)
    assert abs(analysis.overall_score - round(target_dim.raw_score, 1)) < 0.2


def test_fit_weights_negative_and_extreme_values():
    """Adversarial Case: Negative weights must be clamped to 0.0 and weights must sum to 1.0."""
    weights = FitWeights(
        career=-50.0,
        roi=100.0,
        academic=100.0,
        admissions=0.0,
        experience=0.0,
        strength=0.0,
        location=0.0,
        cost=0.0,
    )
    norm = weights.normalized()
    assert norm["career"] == 0.0
    assert abs(norm["roi"] - 0.5) < 1e-5
    assert abs(norm["academic"] - 0.5) < 1e-5
    assert sum(norm.values()) == pytest.approx(1.0)


def test_fit_weights_subset_dimensions_normalization():
    """Verify that normalizing against a subset of dimensions distributes 100% weight strictly across available dims."""
    weights = FitWeights(career=25, roi=25, academic=25, cost=25)
    subset = ["career", "cost"]
    norm = weights.normalized(subset)
    assert len(norm) == 2
    assert abs(norm["career"] - 0.5) < 1e-5
    assert abs(norm["cost"] - 0.5) < 1e-5
    assert sum(norm.values()) == pytest.approx(1.0)


# ==============================================================================
# SECTION 2: Missing Data Normalization & Metric Edge Cases
# ==============================================================================

def test_fit_scorer_with_completely_empty_college_metrics():
    """Adversarial Case: College with missing optional metrics must evaluate to a valid bounded score [0, 100]."""
    sparse_college = CanonicalCollege(
        id="sparse_999999",
        unitid=999999,
        name="Sparse University",
        location=Location(city="Nowhere", state="XX"),
        undergrad_size=MetricField(value=None),
        admissions=AdmissionsData(acceptance_rate=MetricField(value=None)),
        costs=CostData(
            tuition_in_state=MetricField(value=None),
            tuition_out_of_state=MetricField(value=None),
            net_price_average=MetricField(value=None),
        ),
        outcomes=OutcomesData(
            completion_rate_6yr=MetricField(value=None),
            median_earnings_10yr=MetricField(value=None),
        ),
        popular_programs=[],
    )

    prefs = StudentPreferences(
        sat_score=1400,
        budget_max_annual=30000,
        preferred_majors=["Computer Science"],
        home_state="CA",
    )

    analysis = fit_scorer.evaluate_college_fit(sparse_college, prefs)
    assert isinstance(analysis.overall_score, float)
    assert 0.0 <= analysis.overall_score <= 100.0
    assert analysis.category in ["Reach", "Target", "Likely"]
    assert 0.0 <= analysis.admissions_probability <= 1.0
    assert len(analysis.dimensions) == 8

    # Ensure every dimension produced a non-empty rationale
    for dim in analysis.dimensions:
        assert isinstance(dim.rationale, str) and len(dim.rationale) > 0
        assert 0.0 <= dim.raw_score <= 100.0


@pytest.mark.parametrize("budget_val", [0, -1000, -99999999, 1, 10000000])
def test_fit_scorer_budget_boundary_conditions(budget_val):
    """Adversarial Case: Budget = 0, negative, $1, or $10M must never cause ZeroDivisionError and must produce bounded scores."""
    college = get_seed_college("166683")  # MIT
    prefs = StudentPreferences(budget_max_annual=budget_val)
    analysis = fit_scorer.evaluate_college_fit(college, prefs)
    cost_dim = next(d for d in analysis.dimensions if d.dimension == "cost")
    assert 0.0 <= cost_dim.raw_score <= 100.0
    assert 0.0 <= analysis.overall_score <= 100.0


@pytest.mark.parametrize("sat_val", [0, 400, 800, 1200, 1600, 2400])
def test_fit_scorer_sat_extreme_boundaries(sat_val):
    """Adversarial Case: SAT scores from 0 up to 2400 stay stable and bounded."""
    college = get_seed_college("170976")  # Michigan
    prefs = StudentPreferences(sat_score=sat_val)
    analysis = fit_scorer.evaluate_college_fit(college, prefs)
    assert 0.0 <= analysis.overall_score <= 100.0
    assert 0.0 <= analysis.admissions_probability <= 1.0


def test_fit_scorer_major_matching_adversarial_inputs():
    """Adversarial Case: Major matching with SQL injection, XSS payloads, regex metacharacters, and unicode."""
    college = get_seed_college("166683")
    adversarial_majors = [
        "'; DROP TABLE colleges; --",
        "<script>alert('xss')</script>",
        "Computer Science (B.S.) [Specialized] +.*$^",
        "Électronique & Intelligence Artificielle 日本語",
        "A" * 5000,
    ]

    prefs = StudentPreferences(preferred_majors=adversarial_majors)
    analysis = fit_scorer.evaluate_college_fit(college, prefs)
    strength_dim = next(d for d in analysis.dimensions if d.dimension == "strength")
    assert 0.0 <= strength_dim.raw_score <= 100.0
    assert isinstance(strength_dim.rationale, str)


def test_fit_scorer_income_bracket_resolution():
    """Verify that specific income bracket prices are resolved when available."""
    college = get_seed_college("166683")

    prefs_low_income = StudentPreferences(family_income_bracket="0_30k", budget_max_annual=15000)
    analysis_low = fit_scorer.evaluate_college_fit(college, prefs_low_income)

    prefs_high_income = StudentPreferences(family_income_bracket="110k_plus", budget_max_annual=15000)
    analysis_high = fit_scorer.evaluate_college_fit(college, prefs_high_income)

    cost_low = next(d for d in analysis_low.dimensions if d.dimension == "cost")
    cost_high = next(d for d in analysis_high.dimensions if d.dimension == "cost")

    assert cost_low.raw_score >= cost_high.raw_score


# ==============================================================================
# SECTION 3: Reach / Target / Likely Categorization Stability
# ==============================================================================

def test_reach_target_likely_super_selective_invariance():
    """Adversarial Invariant: Colleges with acceptance rate < 15% are ALWAYS Reach, even with SAT 1600."""
    harvard = get_seed_college("166027")  # Harvard (~3.4%)
    mit = get_seed_college("166683")      # MIT (~4.0%)
    stanford = get_seed_college("243744") # Stanford (~3.9%)

    for college in [harvard, mit, stanford]:
        prefs_perfect = StudentPreferences(sat_score=1600, gpa=4.0)
        analysis = fit_scorer.evaluate_college_fit(college, prefs_perfect)
        assert analysis.category == "Reach", f"{college.name} should be Reach even for SAT 1600"
        assert analysis.admissions_probability < 0.20


def test_reach_target_likely_transitions_across_admit_rates():
    """Verify clean categorization transitions across acceptance rates for standard students."""
    rates = [0.02, 0.10, 0.149, 0.18, 0.25, 0.40, 0.60, 0.85, 1.0]

    for rate in rates:
        syn_college = CanonicalCollege(
            id=f"rate_{int(rate*100)}",
            unitid=int(rate * 10000),
            name=f"University of Rate {rate}",
            location=Location(city="City", state="CA"),
            undergrad_size=MetricField(value=5000),
            admissions=AdmissionsData(
                acceptance_rate=MetricField(value=rate, source="test", source_type=SourceType.GOVERNMENT, confidence=ConfidenceLevel.REPORTED),
                sat_total_25=MetricField(value=1200, source="test", source_type=SourceType.GOVERNMENT, confidence=ConfidenceLevel.REPORTED),
                sat_total_75=MetricField(value=1400, source="test", source_type=SourceType.GOVERNMENT, confidence=ConfidenceLevel.REPORTED),
            ),
            costs=CostData(
                tuition_in_state=MetricField(value=10000),
                tuition_out_of_state=MetricField(value=20000),
                net_price_average=MetricField(value=15000),
            ),
            outcomes=OutcomesData(
                completion_rate_6yr=MetricField(value=0.85),
                median_earnings_10yr=MetricField(value=75000),
            ),
        )

        # Student with SAT 1500 (above 75th percentile)
        analysis_high_sat = fit_scorer.evaluate_college_fit(syn_college, StudentPreferences(sat_score=1500))
        if rate < 0.15:
            assert analysis_high_sat.category == "Reach"
        elif rate >= 0.30:
            assert analysis_high_sat.category == "Likely"
        else:
            assert analysis_high_sat.category == "Target"

        # Student with SAT 1100 (below 25th percentile)
        analysis_low_sat = fit_scorer.evaluate_college_fit(syn_college, StudentPreferences(sat_score=1100))
        assert analysis_low_sat.category == "Reach"


def test_randomized_monte_carlo_probability_bounds():
    """Adversarial Monte Carlo: Test 200 randomized college-student profiles to prove invariants:
    1. overall_score is bounded in [0.0, 100.0]
    2. admissions_probability is bounded in [0.0, 1.0]
    3. category is strictly one of 'Reach', 'Target', 'Likely'
    """
    import random
    random.seed(42)

    for i in range(200):
        admit = random.choice([None, 0.0, random.uniform(0.01, 1.0)])
        sat25 = random.choice([None, random.randint(800, 1400)])
        sat75 = sat25 + random.randint(50, 300) if sat25 else None
        net_p = random.choice([None, random.randint(5000, 90000)])
        earn = random.choice([None, random.randint(20000, 180000)])

        syn_col = CanonicalCollege(
            id=f"mc_{i}",
            unitid=100000 + i,
            name=f"Monte Carlo College {i}",
            location=Location(city="Test", state=random.choice(["CA", "NY", "TX", "MA", "OH"])),
            undergrad_size=MetricField(value=random.randint(1000, 40000)),
            admissions=AdmissionsData(
                acceptance_rate=MetricField(value=admit),
                sat_total_25=MetricField(value=sat25) if sat25 is not None else None,
                sat_total_75=MetricField(value=sat75) if sat75 is not None else None,
            ),
            costs=CostData(
                tuition_in_state=MetricField(value=10000),
                tuition_out_of_state=MetricField(value=20000),
                net_price_average=MetricField(value=net_p),
            ),
            outcomes=OutcomesData(
                completion_rate_6yr=MetricField(value=0.8),
                median_earnings_10yr=MetricField(value=earn),
            ),
        )

        prefs = StudentPreferences(
            sat_score=random.choice([None, random.randint(400, 1600)]),
            budget_max_annual=random.choice([None, 0, random.randint(5000, 80000)]),
            home_state=random.choice([None, "CA", "FL"]),
            preferred_majors=random.choice([[], ["Computer Science"], ["Economics", "Music"]]),
            weights=FitWeights(
                career=random.uniform(0, 50),
                roi=random.uniform(0, 50),
                academic=random.uniform(0, 50),
                admissions=random.uniform(0, 50),
                experience=random.uniform(0, 50),
                strength=random.uniform(0, 50),
                location=random.uniform(0, 50),
                cost=random.uniform(0, 50),
            )
        )

        res = fit_scorer.evaluate_college_fit(syn_col, prefs)
        assert 0.0 <= res.overall_score <= 100.0, f"Score out of bounds: {res.overall_score}"
        assert 0.0 <= res.admissions_probability <= 1.0, f"Prob out of bounds: {res.admissions_probability}"
        assert res.category in ["Reach", "Target", "Likely"], f"Invalid category: {res.category}"


# ==============================================================================
# SECTION 4: Scale, Lifecycle & SQLite Database Hygiene
# ==============================================================================

def test_portfolio_lifecycle_with_50_colleges_and_db_hygiene():
    """Scale Stress: Add 50 seed colleges to a single portfolio, update notes, change weights,
    verify SQLite persistence, compute summary stats, and clear the portfolio.
    """
    client = APIClient()
    session_id = "adv-test-session-50-colleges"
    client.set_cookie(settings.COOKIE_NAME, session_id)

    # 1. Fetch seed colleges (52 colleges available)
    resp = client.get("/api/colleges?limit=60")
    assert resp.status_code == 200
    all_colleges = resp.json().get("colleges", [])
    assert len(all_colleges) >= 50

    target_50 = all_colleges[:50]

    # 2. Add 50 colleges sequentially
    for c in target_50:
        add_resp = client.post(
            "/api/portfolio/colleges",
            json={"college_id": c["id"], "notes": f"Initial note for {c['name']}", "tag": "Target"},
        )
        assert add_resp.status_code == 200

    # 3. Retrieve portfolio and verify 50 items
    get_resp = client.get("/api/portfolio")
    assert get_resp.status_code == 200
    pdata = get_resp.json()
    items = pdata.get("colleges", [])
    assert len(items) == 50

    summary = pdata.get("summary", {})
    assert summary.get("total_colleges") == 50
    assert summary.get("reach_count") + summary.get("target_count") + summary.get("likely_count") == 50
    assert summary.get("average_net_price") is not None and summary.get("average_net_price") > 0
    assert summary.get("average_median_earnings") is not None and summary.get("average_median_earnings") > 0

    # 4. Verify Raw SQLite Persistence directly
    with sqlite3.connect(settings.DATABASE_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT data_json FROM portfolios WHERE portfolio_id = ?", (session_id,))
        row = cur.fetchone()
        assert row is not None
        db_portfolio = json.loads(row["data_json"])
        assert len(db_portfolio["colleges"]) == 50
        assert db_portfolio["portfolio_id"] == session_id

    # 5. Update custom notes and labels on a subset of colleges
    first_cid = target_50[0]["id"]
    update_resp = client.put(
        f"/api/portfolio/colleges/{first_cid}",
        json={"notes": "Updated adversarial test note", "custom_label": "High Priority Dream School", "tag": "Reach"},
    )
    assert update_resp.status_code == 200
    updated_items = update_resp.json().get("colleges", [])
    updated_first = next(item for item in updated_items if item["id"] == first_cid or item["college_id"] == first_cid)
    assert updated_first["notes"] == "Updated adversarial test note"
    assert updated_first["custom_label"] == "High Priority Dream School"
    assert updated_first["tag"] == "Reach"

    # 6. Update student preferences / weights and verify all 50 colleges are recalculated
    new_prefs = {
        "budget_max_annual": 25000,
        "sat_score": 1550,
        "home_state": "CA",
        "preferred_majors": ["Computer Science", "Engineering"],
        "weights": {
            "career": 0.0,
            "roi": 0.0,
            "academic": 0.0,
            "admissions": 0.0,
            "experience": 0.0,
            "strength": 0.0,
            "location": 0.0,
            "cost": 100.0,  # 100% cost weight
        }
    }
    pref_resp = client.put("/api/portfolio/preferences", json=new_prefs)
    assert pref_resp.status_code == 200
    recalced_items = pref_resp.json().get("colleges", [])
    assert len(recalced_items) == 50

    # Verify that each item's fit_score reflects the cost dimension
    for item in recalced_items:
        bd = item.get("fit_breakdown", {})
        cost_info = bd.get("cost", {})
        assert cost_info is not None
        cost_raw = cost_info.get("raw_score")
        if cost_raw is not None:
            assert abs(item.get("composite_score", 0) - cost_raw) < 1.0

    # 7. Remove single college
    del_resp = client.delete(f"/api/portfolio/colleges/{first_cid}")
    assert del_resp.status_code == 200
    assert len(del_resp.json().get("colleges", [])) == 49

    # 8. Clear entire portfolio
    clear_resp = client.delete("/api/portfolio")
    assert clear_resp.status_code == 200
    cleared_data = clear_resp.json()
    assert len(cleared_data.get("colleges", [])) == 0
    assert cleared_data.get("summary", {}).get("total_colleges") == 0

    # 9. Verify SQLite Database is fully synchronized to 0 items
    with sqlite3.connect(settings.DATABASE_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT data_json FROM portfolios WHERE portfolio_id = ?", (session_id,))
        row = cur.fetchone()
        assert row is not None
        db_cleared = json.loads(row["data_json"])
        assert len(db_cleared["colleges"]) == 0


def test_portfolio_guest_session_isolation():
    """Adversarial Case: Verify strict isolation between concurrent guest sessions."""
    client_a = APIClient()
    client_b = APIClient()

    session_a = "guest-session-alpha-111"
    session_b = "guest-session-beta-222"

    client_a.set_cookie(settings.COOKIE_NAME, session_a)
    client_b.set_cookie(settings.COOKIE_NAME, session_b)

    # Add MIT to session A
    resp_a = client_a.post("/api/portfolio/colleges", json={"college_id": "166683", "notes": "Session A Private"})
    assert resp_a.status_code == 200

    # Add Stanford to session B
    resp_b = client_b.post("/api/portfolio/colleges", json={"college_id": "243744", "notes": "Session B Private"})
    assert resp_b.status_code == 200

    # Check Session A contents
    data_a = client_a.get("/api/portfolio").json()
    assert len(data_a["colleges"]) == 1
    assert data_a["colleges"][0]["id"] == "166683"
    assert data_a["colleges"][0]["notes"] == "Session A Private"

    # Check Session B contents
    data_b = client_b.get("/api/portfolio").json()
    assert len(data_b["colleges"]) == 1
    assert data_b["colleges"][0]["id"] == "243744"
    assert data_b["colleges"][0]["notes"] == "Session B Private"

    # Mutate Session A and ensure Session B is untouched
    client_a.delete("/api/portfolio")
    assert len(client_a.get("/api/portfolio").json()["colleges"]) == 0
    assert len(client_b.get("/api/portfolio").json()["colleges"]) == 1


def test_portfolio_corrupted_sqlite_record_recovery():
    """Adversarial Case: If SQLite contains corrupted/unparseable JSON for a portfolio ID,
    the API/service must recover gracefully by generating a clean portfolio without crashing.
    """
    corrupt_session_id = "corrupt-session-666"

    # Inject corrupt JSON into SQLite
    with sqlite3.connect(settings.DATABASE_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT OR REPLACE INTO portfolios (portfolio_id, data_json, created_at, updated_at)
            VALUES (?, ?, datetime('now'), datetime('now'))
            """,
            (corrupt_session_id, "{ CORRUPTED INVALID JSON !!!"),
        )
        conn.commit()

    client = APIClient()
    client.set_cookie(settings.COOKIE_NAME, corrupt_session_id)
    resp = client.get("/api/portfolio")
    assert resp.status_code == 200
    pdata = resp.json()
    assert pdata.get("colleges") == []
