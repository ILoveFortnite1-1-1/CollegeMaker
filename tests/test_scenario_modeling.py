"""Comprehensive Tests for Feature R5: 'What-If' Scenario Modeling."""
import pytest
from server.models.portfolio import ScenarioOverrideRequest
from server.services.scenario_service import scenario_service
from tests.conftest import APIClient, SEED_COLLEGES


def test_scenario_modeling_non_persistence():
    """Verify scenario modeling does not mutate database or saved portfolio preferences."""
    client = APIClient()
    cid = SEED_COLLEGES["osu"]["id"]

    # 1. Add college to portfolio with baseline preferences
    client.post("/api/portfolio/colleges", json={"college_id": cid})
    client.put(
        "/api/portfolio/preferences",
        json={
            "home_state": "CA",  # Out-of-state for Ohio State
            "preferred_majors": ["History"],
            "budget_max_annual": 30000,
            "gpa": 3.4,
            "sat_score": 1250,
        },
    )

    baseline_portfolio = client.get("/api/portfolio").json()
    assert baseline_portfolio["preferences"]["home_state"] == "CA"
    assert baseline_portfolio["preferences"]["preferred_majors"] == ["History"]

    # 2. Execute scenario simulation with in-state residency, new major, and $10,000 aid
    scenario_payload = {
        "college_id": cid,
        "hypothetical_major": "Computer Science",
        "is_in_state": True,
        "annual_aid_amount": 10000,
        "gpa": 3.9,
        "sat_score": 1480,
    }
    sim_res = client.post("/api/portfolio/scenario", json=scenario_payload)
    assert sim_res.status_code == 200
    sim_data = sim_res.json()

    assert "results" in sim_data
    assert len(sim_data["results"]) >= 1
    res0 = sim_data["results"][0]

    assert res0["college_id"] == cid
    assert "baseline_fit_score" in res0
    assert "what_if_fit_score" in res0
    assert "fit_score_delta" in res0
    assert "dimension_deltas" in res0

    # With in-state residency and $10,000 aid, net price must be lower in scenario
    assert res0["what_if_net_price"] < res0["baseline_net_price"]
    assert res0["net_price_delta"] < 0

    # 3. Verify original preferences in database remain strictly UNCHANGED
    after_portfolio = client.get("/api/portfolio").json()
    assert after_portfolio["preferences"]["home_state"] == "CA"
    assert after_portfolio["preferences"]["preferred_majors"] == ["History"]
    assert after_portfolio["preferences"]["gpa"] == 3.4
    assert after_portfolio["preferences"]["sat_score"] == 1250


def test_scenario_modeling_all_saved_colleges():
    """Verify simulating without college_id evaluates all saved colleges in portfolio."""
    client = APIClient()
    c1 = SEED_COLLEGES["mit"]["id"]
    c2 = SEED_COLLEGES["berkeley"]["id"]

    client.post("/api/portfolio/colleges", json={"college_id": c1})
    client.post("/api/portfolio/colleges", json={"college_id": c2})

    sim_res = client.post(
        "/api/portfolio/scenario",
        json={"annual_aid_amount": 5000, "gpa": 3.95},
    )
    assert sim_res.status_code == 200
    results = sim_res.json()["results"]
    assert len(results) >= 2
    cids = [r["college_id"] for r in results]
    assert c1 in cids
    assert c2 in cids


def test_scenario_modeling_net_price_zero_bound():
    """Verify when hypothetical aid covers full cost, projected net price becomes 0 (not reverting to 25000)."""
    client = APIClient()
    cid = SEED_COLLEGES["osu"]["id"]
    client.post("/api/portfolio/colleges", json={"college_id": cid})

    # Massive aid covering entire cost
    sim_res = client.post(
        "/api/portfolio/scenario",
        json={"college_id": cid, "annual_aid_amount": 100000},
    )
    assert sim_res.status_code == 200
    res = sim_res.json()["results"][0]
    assert res["what_if_net_price"] == 0
    assert res["what_if_fit_score"] >= res["baseline_fit_score"]
    assert res["net_price_delta"] <= -res["baseline_net_price"]


def test_scenario_modeling_annual_loans():
    """Verify hypothetical yearly loans calculate total debt and estimated monthly payments."""
    client = APIClient()
    cid = SEED_COLLEGES["mit"]["id"]
    client.post("/api/portfolio/colleges", json={"college_id": cid})

    sim_res = client.post(
        "/api/portfolio/scenario",
        json={"college_id": cid, "annual_loan_amount": 5500},
    )
    assert sim_res.status_code == 200
    res = sim_res.json()["results"][0]
    assert res["annual_loan_amount"] == 5500
    assert res["total_debt_at_graduation"] == 22000
    # 22000 debt over 10 yrs at 5.5% is approx $238.76/mo
    assert abs(res["estimated_monthly_payment"] - 238.76) < 1.0
    assert res["what_if_out_of_pocket"] == max(0, res["what_if_net_price"] - 5500)
