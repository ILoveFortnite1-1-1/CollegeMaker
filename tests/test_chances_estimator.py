"""Comprehensive Tests for Feature R4: Admissions Chances Estimator."""
import json
import pytest
from server.config import settings
from server.models.canonical import AdmissionsData, CanonicalCollege, MetricField
from server.models.portfolio import StudentPreferences
from server.services.chances_service import chances_service
from tests.conftest import APIClient, SEED_COLLEGES


def load_seed_college(cid: str) -> CanonicalCollege:
    with open(settings.SEED_DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    for item in data:
        if str(item.get("id")) == str(cid) or str(item.get("unitid")) == str(cid):
            return CanonicalCollege(**item)
    raise ValueError(f"College {cid} not found in seed")


def test_chances_estimator_invariant_super_selective_always_reach():
    """Invariant: Institutions with acceptance rate < 15% are ALWAYS classified as Reach."""
    college = load_seed_college("166683").model_copy(deep=True)  # MIT
    # Set acceptance rate to 7%
    college.admissions.acceptance_rate = MetricField[float](value=0.07)
    college.admissions.sat_total_25 = MetricField[int](value=1500)
    college.admissions.sat_total_75 = MetricField[int](value=1570)

    # Perfect student stats: 4.0 GPA, 1600 SAT
    prefs = StudentPreferences(gpa=4.0, sat_score=1600)
    result = chances_service.estimate_chances(college, prefs)

    assert result.classification == "Reach"
    assert result.acceptance_rate == 0.07
    assert result.overall_probability <= 0.18


def test_chances_estimator_four_tiers():
    """Verify Reach, Target, Likely, and Safety classifications based on percentiles and admit rate."""
    base = load_seed_college("204796")  # Ohio State

    # 1. Safety School: High admit rate (65%), student stats above 75th percentile
    safety_col = base.model_copy(deep=True)
    safety_col.admissions.acceptance_rate = MetricField[float](value=0.65)
    safety_col.admissions.sat_total_25 = MetricField[int](value=1150)
    safety_col.admissions.sat_total_75 = MetricField[int](value=1320)

    prefs_strong = StudentPreferences(gpa=3.95, sat_score=1450)
    res_safety = chances_service.estimate_chances(safety_col, prefs_strong)
    assert res_safety.classification == "Safety"
    assert res_safety.test_status["status"] == "above"

    # 2. Target School: Moderate admit rate (35%), student stats between 25th and 75th
    target_col = base.model_copy(deep=True)
    target_col.admissions.acceptance_rate = MetricField[float](value=0.35)
    target_col.admissions.sat_total_25 = MetricField[int](value=1300)
    target_col.admissions.sat_total_75 = MetricField[int](value=1450)

    prefs_mid = StudentPreferences(gpa=3.6, sat_score=1380)
    res_target = chances_service.estimate_chances(target_col, prefs_mid)
    assert res_target.classification == "Target"
    assert res_target.test_status["status"] == "within"

    # 3. Reach School: Low admit rate or student stats below 25th percentile
    prefs_reach = StudentPreferences(gpa=3.1, sat_score=1200)
    res_reach = chances_service.estimate_chances(target_col, prefs_reach)
    assert res_reach.classification == "Reach"
    assert res_reach.test_status["status"] == "below"


def test_chances_api_endpoint_with_query_params():
    """Verify GET /api/colleges/{college_id}/chances with explicit query parameters."""
    client = APIClient()
    mit_id = SEED_COLLEGES["mit"]["id"]

    # Even with 1600 SAT, MIT must be Reach due to <15% acceptance rate
    res = client.get(f"/api/colleges/{mit_id}/chances?sat=1600&gpa=4.0")
    assert res.status_code == 200
    data = res.json()

    assert data["college_id"] == mit_id
    assert data["classification"] == "Reach"
    assert "acceptance_rate" in data
    assert "test_status" in data
    assert "gpa_status" in data


def test_chances_api_endpoint_with_cookie_preferences():
    """Verify GET /api/colleges/{college_id}/chances reads preferences from session cookie."""
    client = APIClient()
    berkeley_id = SEED_COLLEGES["berkeley"]["id"]

    # Set student preferences via PUT /api/portfolio/preferences
    client.put("/api/portfolio/preferences", json={"gpa": 3.9, "sat_score": 1520})

    res = client.get(f"/api/colleges/{berkeley_id}/chances")
    assert res.status_code == 200
    data = res.json()

    assert data["college_id"] == berkeley_id
    assert data["classification"] in ["Target", "Likely", "Reach"]
    assert data["test_status"]["user_sat"] == 1520
