"""
End-to-End Integration and Server Verification Test Suite for Features R1 through R7.

Covers realistic student guest user journeys using FastAPI TestClient:
- Server Startup & Static Serving: Launches `python run.py`, queries /api/health and /, verifies 200 OK.
- Test 1 (R1 Aid Comparison): Save 2 colleges, submit aid offers with merit/loans/scholarships,
  verify net cost = sticker - grants, 4-year totals, monthly loan amortization, and best-value highlight.
- Test 2 (R2 Calendar): Update ApplicationTracker with priority/regular/FAFSA/CSS/scholarship deadlines,
  verify all deadlines returned, categorized by type, with 14-day upcoming list.
- Test 3 (R3 Essays): Full CRUD cycle: create essay, update draft status & word count, link multiple colleges,
  verify 'Used for N schools' reuse tracking, delete essay.
- Test 4 (R4 Chances): Update student GPA & SAT/ACT in preferences, query single college and portfolio chances,
  verify Reach/Target/Likely/Safety classification and percentile ranges.
- Test 5 (R5 What-If): Query POST /api/portfolio/scenario with overrides for major, in-state residency, aid, budget,
  verify recalculated fit score and delta without mutating saved preferences or colleges.
- Test 6 (R6 Alumni Outcomes): Query GET /api/colleges/{id}/field-of-study, verify top majors sorted by median earnings,
  and preferred majors from preferences flagged.
- Test 7 (R7 Requirements Checklist): Add custom checklist item to school tracker, toggle completed status,
  query GET /api/portfolio/requirements-matrix, verify matrix structure and aggregate counts ('N schools need X').
- Test 8 (Empty States): Query all 7 feature endpoints with a fresh empty guest portfolio (0 saved colleges),
  verify 200 OK responses with clean empty structures (no 500 crashes, no null errors).
"""

import os
import sys
import time
import socket
import subprocess
import urllib.request
from datetime import datetime, timezone, timedelta

import pytest
from fastapi.testclient import TestClient

from server.main import app
from server.services.aid_service import calculate_loan_payment
from tests.conftest import SEED_COLLEGES


def _find_free_port() -> int:
    """Acquire an available ephemeral TCP port for server startup verification."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


# =============================================================================
# 1. Server Startup Verification Test
# =============================================================================

def test_server_startup_via_run_py():
    """
    Verify server startup:
    Launch `python run.py` as a child process on a dynamic ephemeral port,
    poll /api/health until responsive, assert /api/health returns 200 with JSON,
    and assert / serves client/index.html with text/html. Then terminate cleanly.
    """
    port = _find_free_port()
    env = os.environ.copy()
    env["PORT"] = str(port)
    env["APP_ENV"] = "test"

    proc = subprocess.Popen(
        [sys.executable, "run.py"],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    try:
        # Poll /api/health for up to 15 seconds
        health_ok = False
        health_body = ""
        for _ in range(30):
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/health", timeout=1) as resp:
                    if resp.status == 200:
                        health_ok = True
                        health_body = resp.read().decode("utf-8")
                        break
            except Exception:
                time.sleep(0.4)

        assert health_ok, f"Server launched via run.py failed to respond on port {port}"
        assert "status" in health_body
        assert ("healthy" in health_body or "ok" in health_body or "degraded" in health_body)

        # Query root endpoint / to verify it serves client/index.html
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=2) as resp:
            assert resp.status == 200
            content_type = resp.headers.get("content-type", "").lower()
            assert "text/html" in content_type
            html_body = resp.read().decode("utf-8")
            assert "<title>College Portfolio" in html_body
            assert 'id="cookie-banner"' in html_body

    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=2)


def test_server_startup_in_process_health_and_index():
    """Verify FastAPI application in-process serves /api/health and / with client/index.html."""
    with TestClient(app) as client:
        # Health check
        res_health = client.get("/api/health")
        assert res_health.status_code == 200
        health_json = res_health.json()
        assert health_json["status"] in ["healthy", "ok", "degraded", "up"]
        assert "database" in health_json

        # Root static serving check
        res_index = client.get("/")
        assert res_index.status_code == 200
        assert "text/html" in res_index.headers.get("content-type", "").lower()
        assert "<title>College Portfolio" in res_index.text


# =============================================================================
# 2. Comprehensive E2E Tests: R1 through R7 + Empty States
# =============================================================================

def test_e2e_r1_financial_aid_comparison_user_journey():
    """
    Test 1 (R1 Aid Comparison):
    Save 2 colleges -> submit financial aid offers with merit aid, federal loans,
    outside scholarships -> verify net cost calculation (sticker - grants),
    4-year total, monthly payment estimate at graduation, and best-value highlight.
    """
    with TestClient(app) as client:
        c1_id = SEED_COLLEGES["stanford"]["id"]  # 243744
        c2_id = SEED_COLLEGES["mit"]["id"]       # 166683

        # Step 1: Save 2 colleges in guest portfolio
        res_add1 = client.post("/api/portfolio/colleges", json={"college_id": c1_id})
        assert res_add1.status_code == 200
        res_add2 = client.post("/api/portfolio/colleges", json={"college_id": c2_id})
        assert res_add2.status_code == 200

        # Step 2: Submit aid offer for Stanford
        # Sticker: $60,000, Merit: $25,000, Need: $15,000, Outside: $5,000, Federal Loans: $5,000
        # Total grants = 25000 + 15000 + 5000 = 45000
        # Net annual cost = 60000 - 45000 = 15000
        # 4-year total = 15000 * 4 = 60000
        # Total debt at grad = 5000 * 4 = 20000 -> Monthly loan payment = 217.05
        stanford_offer = {
            "merit_aid": 25000,
            "need_based_grants": 15000,
            "outside_scholarships": 5000,
            "federal_loans": 5000,
            "work_study": 2500,
            "custom_sticker_price": 60000,
        }
        res_aid1 = client.post(f"/api/portfolio/aid/{c1_id}", json=stanford_offer)
        assert res_aid1.status_code == 200
        aid1_data = res_aid1.json()
        assert aid1_data["status"] == "success"
        assert aid1_data["offer"]["merit_aid"] == 25000

        # Step 3: Submit aid offer for MIT
        # Sticker: $65,000, Merit: $10,000, Outside: $2,000, Federal Loans: $7,500
        # Total grants = 10000 + 2000 = 12000
        # Net annual cost = 65000 - 12000 = 53000
        # 4-year total = 53000 * 4 = 212000
        # Total debt at grad = 7500 * 4 = 30000 -> Monthly loan payment = 325.58
        mit_offer = {
            "merit_aid": 10000,
            "outside_scholarships": 2000,
            "federal_loans": 7500,
            "custom_sticker_price": 65000,
        }
        res_aid2 = client.post(f"/api/portfolio/aid/{c2_id}", json=mit_offer)
        assert res_aid2.status_code == 200

        # Step 4: Query side-by-side financial aid comparison
        comp_res = client.get("/api/portfolio/aid/comparison")
        assert comp_res.status_code == 200
        comp_data = comp_res.json()

        assert comp_data["count_with_offers"] == 2
        # Best-value school must be Stanford ($15,000 net annual cost vs $53,000)
        assert comp_data["best_value_college_id"] == c1_id

        schools = comp_data["colleges"]
        stanford_item = next(s for s in schools if s["college_id"] == c1_id)
        mit_item = next(s for s in schools if s["college_id"] == c2_id)

        # Verify Stanford metrics
        assert stanford_item["is_best_value"] is True
        assert stanford_item["sticker_price"] == 60000
        assert stanford_item["total_grants"] == 45000
        assert stanford_item["net_annual_cost"] == 15000
        assert stanford_item["four_year_total_cost"] == 60000
        assert stanford_item["total_debt_at_graduation"] == 20000
        assert abs(stanford_item["estimated_monthly_payment"] - 217.05) < 1.0

        # Verify MIT metrics
        assert mit_item["is_best_value"] is False
        assert mit_item["sticker_price"] == 65000
        assert mit_item["total_grants"] == 12000
        assert mit_item["net_annual_cost"] == 53000
        assert mit_item["four_year_total_cost"] == 212000
        assert mit_item["total_debt_at_graduation"] == 30000
        assert abs(mit_item["estimated_monthly_payment"] - 325.58) < 1.0

        # Step 5: Test deleting an offer and verifying comparison updates
        del_res = client.delete(f"/api/portfolio/aid/{c1_id}")
        assert del_res.status_code == 200
        assert del_res.json()["deleted"] is True

        comp_after_del = client.get("/api/portfolio/aid/comparison").json()
        assert comp_after_del["count_with_offers"] == 1
        assert comp_after_del["best_value_college_id"] == c2_id


def test_e2e_r2_deadline_calendar_user_journey():
    """
    Test 2 (R2 Calendar):
    Update ApplicationTracker with priority deadline, regular deadline, FAFSA,
    CSS Profile, and scholarship deadlines -> query GET /api/portfolio/calendar ->
    verify all deadlines returned, categorized by type, with 14-day upcoming list.
    """
    with TestClient(app) as client:
        cid = SEED_COLLEGES["stanford"]["id"]
        client.post("/api/portfolio/colleges", json={"college_id": cid})

        # Dynamically compute dates relative to current UTC date
        today = datetime.now(timezone.utc).date()
        priority_date = (today + timedelta(days=6)).strftime("%Y-%m-%d")    # within 14 days
        fafsa_date = (today + timedelta(days=9)).strftime("%Y-%m-%d")       # within 14 days
        regular_date = (today + timedelta(days=60)).strftime("%Y-%m-%d")   # beyond 14 days
        css_date = (today + timedelta(days=35)).strftime("%Y-%m-%d")       # beyond 14 days
        scholarship_upcoming = (today + timedelta(days=12)).strftime("%Y-%m-%d") # within 14 days
        scholarship_distant = (today + timedelta(days=45)).strftime("%Y-%m-%d")  # beyond 14 days

        tracker_payload = {
            "priority_deadline": priority_date,
            "regular_deadline": regular_date,
            "fafsa_deadline": fafsa_date,
            "css_profile_deadline": css_date,
            "scholarship_deadlines": {
                "Stanford Knight-Hennessy": scholarship_upcoming,
                "Presidential Leadership Award": scholarship_distant,
            },
        }

        update_res = client.put(f"/api/portfolio/colleges/{cid}/tracker", json=tracker_payload)
        assert update_res.status_code == 200

        # Query calendar endpoint
        cal_res = client.get("/api/portfolio/calendar")
        assert cal_res.status_code == 200
        cal_data = cal_res.json()

        assert "events" in cal_data
        assert "upcoming_14_days" in cal_data
        assert cal_data["total_events"] >= 6
        assert cal_data["colleges_with_deadlines"] >= 1

        events = cal_data["events"]

        # Verify deadlines categorized by type
        app_deadlines = [e for e in events if e["deadline_type"] == "app_deadline"]
        assert len(app_deadlines) >= 2
        app_dates = [e["date"] for e in app_deadlines]
        assert priority_date in app_dates
        assert regular_date in app_dates

        aid_deadlines = [e for e in events if e["deadline_type"] == "financial_aid"]
        assert len(aid_deadlines) >= 2
        aid_dates = [e["date"] for e in aid_deadlines]
        assert fafsa_date in aid_dates
        assert css_date in aid_dates

        sch_deadlines = [e for e in events if e["deadline_type"] == "scholarship"]
        assert len(sch_deadlines) >= 2
        sch_dates = [e["date"] for e in sch_deadlines]
        assert scholarship_upcoming in sch_dates
        assert scholarship_distant in sch_dates

        # Verify 14-day upcoming list contains only events within [0, 14] days
        upcoming = cal_data["upcoming_14_days"]
        upcoming_dates = [e["date"] for e in upcoming]

        assert priority_date in upcoming_dates
        assert fafsa_date in upcoming_dates
        assert scholarship_upcoming in upcoming_dates

        assert regular_date not in upcoming_dates
        assert css_date not in upcoming_dates
        assert scholarship_distant not in upcoming_dates

        for u_item in upcoming:
            assert 0 <= u_item["days_remaining"] <= 14


def test_e2e_r3_essay_tracker_crud_lifecycle_user_journey():
    """
    Test 3 (R3 Essays):
    Full CRUD cycle: create essay -> update draft status and word count ->
    link multiple colleges -> verify 'Used for N schools' reuse tracking -> delete essay.
    """
    with TestClient(app) as client:
        c1 = SEED_COLLEGES["stanford"]["id"]
        c2 = SEED_COLLEGES["mit"]["id"]
        c3 = SEED_COLLEGES["berkeley"]["id"]

        # Step 1: Create new essay entry
        create_payload = {
            "prompt": "Reflect on a time when you questioned or challenged a belief or idea.",
            "word_limit": 650,
            "current_word_count": 120,
            "draft_status": "Drafting",
            "colleges": [c1],
        }
        res_create = client.post("/api/portfolio/essays", json=create_payload)
        assert res_create.status_code == 200
        essay = res_create.json()

        assert "id" in essay
        essay_id = essay["id"]
        assert essay["prompt"] == create_payload["prompt"]
        assert essay["draft_status"] == "Drafting"
        assert essay["current_word_count"] == 120
        assert essay["word_limit"] == 650
        assert essay["colleges"] == [c1]
        assert essay["reuse_count"] == 1

        # Step 2: Query list of essays
        res_list = client.get("/api/portfolio/essays")
        assert res_list.status_code == 200
        list_data = res_list.json()
        assert list_data["count"] >= 1
        found_in_list = next((e for e in list_data["essays"] if e["id"] == essay_id), None)
        assert found_in_list is not None
        assert found_in_list["reuse_count"] == 1

        # Step 3: Update draft status and current word count
        update_payload = {
            "draft_status": "Reviewing",
            "current_word_count": 615,
        }
        res_update = client.put(f"/api/portfolio/essays/{essay_id}", json=update_payload)
        assert res_update.status_code == 200
        updated_essay = res_update.json()
        assert updated_essay["draft_status"] == "Reviewing"
        assert updated_essay["current_word_count"] == 615

        # Step 4: Link multiple colleges and verify 'Used for N schools' reuse tracking
        link_payload = {
            "colleges": [c1, c2, c3],
        }
        res_link = client.put(f"/api/portfolio/essays/{essay_id}", json=link_payload)
        assert res_link.status_code == 200
        linked_essay = res_link.json()
        assert len(linked_essay["colleges"]) == 3
        assert linked_essay["reuse_count"] == 3
        assert c1 in linked_essay["colleges"]
        assert c2 in linked_essay["colleges"]
        assert c3 in linked_essay["colleges"]

        # Also verify listed essays show reuse_count == 3
        res_list_after_link = client.get("/api/portfolio/essays")
        assert res_list_after_link.status_code == 200
        linked_in_list = next(e for e in res_list_after_link.json()["essays"] if e["id"] == essay_id)
        assert linked_in_list["reuse_count"] == 3

        # Step 5: Delete essay
        res_del = client.delete(f"/api/portfolio/essays/{essay_id}")
        assert res_del.status_code == 200
        assert res_del.json()["deleted"] is True

        # Verify essay is no longer returned in list
        res_final_list = client.get("/api/portfolio/essays")
        assert res_final_list.status_code == 200
        assert not any(e["id"] == essay_id for e in res_final_list.json()["essays"])

        # Attempting to delete again returns 404
        res_del_again = client.delete(f"/api/portfolio/essays/{essay_id}")
        assert res_del_again.status_code == 404


def test_e2e_r4_admissions_chances_user_journey():
    """
    Test 4 (R4 Chances):
    Update student GPA and SAT/ACT in preferences -> query GET /api/colleges/{id}/chances
    and GET /api/portfolio/chances -> verify Reach/Target/Likely/Safety classification
    and percentile ranges.
    """
    with TestClient(app) as client:
        mit_id = SEED_COLLEGES["mit"]["id"]   # Acceptance rate ~4% -> Reach invariant
        osu_id = SEED_COLLEGES["osu"]["id"]   # Acceptance rate ~53% -> Safety with high stats

        # Save both colleges
        client.post("/api/portfolio/colleges", json={"college_id": mit_id})
        client.post("/api/portfolio/colleges", json={"college_id": osu_id})

        # Update student profile with strong GPA and SAT
        pref_payload = {
            "gpa": 3.95,
            "sat_score": 1540,
            "act_score": 35,
            "budget_max_annual": 40000,
            "preferred_majors": ["Engineering"],
        }
        res_prefs = client.put("/api/portfolio/preferences", json=pref_payload)
        assert res_prefs.status_code == 200

        # Query single-college chances for MIT (ultra-selective < 15%)
        res_mit_chances = client.get(f"/api/colleges/{mit_id}/chances")
        assert res_mit_chances.status_code == 200
        mit_chances = res_mit_chances.json()

        assert mit_chances["classification"] == "Reach"
        assert mit_chances["acceptance_rate"] < 0.15
        assert mit_chances["gpa_status"]["user_gpa"] == 3.95
        assert mit_chances["test_status"]["user_sat"] == 1540
        assert mit_chances["test_status"]["sat_25"] is not None
        assert mit_chances["test_status"]["sat_75"] is not None

        # Query single-college chances for Ohio State
        # With 1540 SAT (> 75th percentile ~1440) and ~53% acceptance rate -> Safety
        res_osu_chances = client.get(f"/api/colleges/{osu_id}/chances")
        assert res_osu_chances.status_code == 200
        osu_chances = res_osu_chances.json()

        assert osu_chances["classification"] in ["Safety", "Likely"]
        assert osu_chances["acceptance_rate"] >= 0.40
        assert osu_chances["test_status"]["sat_25"] is not None
        assert osu_chances["test_status"]["sat_75"] is not None
        assert osu_chances["test_status"]["status"] == "above"

        # Query portfolio-wide chances endpoint
        res_port_chances = client.get("/api/portfolio/chances")
        assert res_port_chances.status_code == 200
        port_chances_data = res_port_chances.json()

        assert port_chances_data["total_colleges"] == 2
        assert "distribution" in port_chances_data
        dist = port_chances_data["distribution"]
        assert dist["Reach"] >= 1
        assert (dist["Safety"] + dist["Likely"]) >= 1

        chances_items = port_chances_data["chances"]
        assert len(chances_items) == 2
        college_ids_in_chances = [c["college_id"] for c in chances_items]
        assert mit_id in college_ids_in_chances
        assert osu_id in college_ids_in_chances


def test_e2e_r5_what_if_scenario_modeling_user_journey():
    """
    Test 5 (R5 What-If):
    Query POST /api/portfolio/scenario with overrides for major, in-state residency,
    aid, and budget -> verify recalculated fit score and delta without mutating
    saved preferences or colleges.
    """
    with TestClient(app) as client:
        berkeley_id = SEED_COLLEGES["berkeley"]["id"]  # 110635, public school in CA

        # Baseline: NY resident, History major, $20k budget
        init_prefs = {
            "home_state": "NY",
            "budget_max_annual": 20000,
            "preferred_majors": ["History"],
            "gpa": 3.5,
            "sat_score": 1320,
        }
        client.put("/api/portfolio/preferences", json=init_prefs)
        client.post("/api/portfolio/colleges", json={"college_id": berkeley_id})

        # Capture baseline portfolio state
        base_portfolio = client.get("/api/portfolio").json()
        saved_col = next(c for c in base_portfolio["colleges"] if c["id"] == berkeley_id)
        base_fit_score = saved_col["fit_score"]
        assert base_portfolio["preferences"]["home_state"] == "NY"
        assert base_portfolio["preferences"]["preferred_majors"] == ["History"]
        assert base_portfolio["preferences"]["budget_max_annual"] == 20000

        # Execute What-If simulation with temporary overrides:
        # - hypothetical major: "Computer Science"
        # - in-state residency: True (CA)
        # - annual aid amount: $12,000
        # - budget max: $40,000
        scenario_payload = {
            "college_id": berkeley_id,
            "hypothetical_major": "Computer Science",
            "is_in_state": True,
            "annual_aid_amount": 12000,
            "budget_max_annual": 40000,
            "gpa": 3.92,
            "sat_score": 1510,
        }
        res_scenario = client.post("/api/portfolio/scenario", json=scenario_payload)
        assert res_scenario.status_code == 200
        scenario_data = res_scenario.json()

        assert "results" in scenario_data
        assert len(scenario_data["results"]) == 1
        res0 = scenario_data["results"][0]

        assert res0["college_id"] == berkeley_id
        assert "baseline_fit_score" in res0
        assert "what_if_fit_score" in res0
        assert "fit_score_delta" in res0
        assert "baseline_net_price" in res0
        assert "what_if_net_price" in res0
        assert "net_price_delta" in res0
        assert "dimension_deltas" in res0

        # With in-state tuition override and $12,000 aid, net price must be substantially lower
        assert res0["what_if_net_price"] < res0["baseline_net_price"]
        assert res0["net_price_delta"] < 0

        # CRITICAL VERIFICATION: Zero-mutation guarantee
        # Saved preferences and saved college records must remain strictly unchanged!
        after_portfolio = client.get("/api/portfolio").json()
        after_prefs = after_portfolio["preferences"]

        assert after_prefs["home_state"] == "NY"
        assert after_prefs["budget_max_annual"] == 20000
        assert after_prefs["preferred_majors"] == ["History"]
        assert after_prefs["gpa"] == 3.5
        assert after_prefs["sat_score"] == 1320

        after_col = next(c for c in after_portfolio["colleges"] if c["id"] == berkeley_id)
        assert after_col["fit_score"] == base_fit_score


def test_e2e_r6_alumni_outcomes_field_of_study_user_journey():
    """
    Test 6 (R6 Alumni Outcomes):
    Query GET /api/colleges/{id}/field-of-study -> verify top majors sorted
    by median earnings and preferred majors from preferences flagged.
    """
    with TestClient(app) as client:
        mit_id = SEED_COLLEGES["mit"]["id"]

        # Step 1: Update preferences to declare student preferred majors
        pref_payload = {
            "preferred_majors": ["Computer Science", "Electrical Engineering"],
        }
        client.put("/api/portfolio/preferences", json=pref_payload)

        # Step 2: Query field of study outcomes endpoint
        res = client.get(f"/api/colleges/{mit_id}/field-of-study")
        assert res.status_code == 200
        data = res.json()

        assert data["college_id"] == mit_id
        assert "majors" in data
        assert len(data["majors"]) > 0

        majors = data["majors"]

        # Verify sorting: majors must be sorted descending by median earnings
        earnings_list = [m["median_earnings"] for m in majors if m.get("median_earnings") is not None]
        assert len(earnings_list) > 0
        assert earnings_list == sorted(earnings_list, reverse=True)

        # Verify preferred majors are flagged
        preferred_items = [m for m in majors if m.get("is_preferred")]
        assert len(preferred_items) >= 1
        preferred_titles = [m["major_title"] for m in preferred_items]
        assert any("Computer Science" in t or "Electrical" in t for t in preferred_titles)
        assert len(data.get("preferred_matches", [])) >= 1

        # Verify individual major record schema
        first_major = majors[0]
        assert "major_title" in first_major
        assert "cip_code" in first_major
        assert "credential_level" in first_major
        assert "median_earnings" in first_major


def test_e2e_r7_requirements_checklist_matrix_user_journey():
    """
    Test 7 (R7 Requirements Checklist):
    Add custom checklist item to school tracker -> toggle completed status ->
    query GET /api/portfolio/requirements-matrix -> verify matrix structure and
    aggregate counts ('N schools need X').
    """
    with TestClient(app) as client:
        c1 = SEED_COLLEGES["berkeley"]["id"]
        c2 = SEED_COLLEGES["stanford"]["id"]

        # Step 1: Save 2 colleges
        client.post("/api/portfolio/colleges", json={"college_id": c1})
        client.post("/api/portfolio/colleges", json={"college_id": c2})

        # Step 2: Add custom checklist item to Berkeley
        custom_item = {
            "name": "Design & Maker Portfolio Supplement",
            "required": True,
            "completed": False,
            "deadline": "2026-11-15",
            "notes": "10-piece creative portfolio with video pitch",
        }
        res_add = client.post(f"/api/portfolio/tracker/{c1}/checklist", json=custom_item)
        assert res_add.status_code == 200
        created = res_add.json()
        item_id = created["id"]
        assert created["name"] == custom_item["name"]
        assert created["completed"] is False

        # Step 3: Toggle item completed status
        res_toggle = client.put(
            f"/api/portfolio/tracker/{c1}/checklist/{item_id}",
            json={"completed": True},
        )
        assert res_toggle.status_code == 200
        assert res_toggle.json()["completed"] is True

        # Step 4: Query cross-school requirements matrix
        res_matrix = client.get("/api/portfolio/requirements-matrix")
        assert res_matrix.status_code == 200
        matrix_data = res_matrix.json()

        assert "matrix" in matrix_data
        assert "colleges" in matrix_data
        assert "summary_counts" in matrix_data

        assert len(matrix_data["colleges"]) == 2
        summary_counts = matrix_data["summary_counts"]

        # Find our custom requirement row
        custom_row = next((r for r in matrix_data["matrix"] if r["name"] == custom_item["name"]), None)
        assert custom_row is not None
        assert custom_row["total_schools_requiring"] == 1
        assert custom_row["completed_count"] == 1
        assert custom_row["schools"][c1]["required"] is True
        assert custom_row["schools"][c1]["completed"] is True
        assert custom_row["schools"][c2]["required"] is False

        # Verify aggregate counts ('N schools need X')
        # Standard requirements initialized on both schools:
        assert summary_counts.get("Official High School Transcript") == 2
        assert summary_counts.get(custom_item["name"]) == 1

        # Every row's total_schools_requiring matches summary_counts
        for row in matrix_data["matrix"]:
            assert row["total_schools_requiring"] == summary_counts[row["name"]]


def test_e2e_empty_states_across_all_features():
    """
    Test 8 (Empty States):
    Query all 7 feature endpoints with a fresh empty guest portfolio (0 saved colleges)
    -> verify 200 OK responses with clean empty structures (no 500 crashes, no null errors).
    """
    with TestClient(app) as client:
        # Verify 0 saved colleges initially
        res_base = client.get("/api/portfolio")
        assert res_base.status_code == 200
        assert len(res_base.json()["colleges"]) == 0

        # 1. R1 Aid Comparison empty state
        res_aid = client.get("/api/portfolio/aid/comparison")
        assert res_aid.status_code == 200
        aid_data = res_aid.json()
        assert aid_data["colleges"] == []
        assert aid_data["count_with_offers"] == 0
        assert aid_data["best_value_college_id"] is None

        # 2. R2 Calendar empty state
        res_cal = client.get("/api/portfolio/calendar")
        assert res_cal.status_code == 200
        cal_data = res_cal.json()
        assert cal_data["events"] == []
        assert cal_data["upcoming_14_days"] == []
        assert cal_data["total_events"] == 0
        assert cal_data["colleges_with_deadlines"] == 0

        # 3. R3 Essays empty state
        res_essays = client.get("/api/portfolio/essays")
        assert res_essays.status_code == 200
        essays_data = res_essays.json()
        assert essays_data["essays"] == []
        assert essays_data["count"] == 0

        # 4. R4 Chances empty state (portfolio)
        res_chances = client.get("/api/portfolio/chances")
        assert res_chances.status_code == 200
        chances_data = res_chances.json()
        assert chances_data["chances"] == []
        assert chances_data["total_colleges"] == 0
        assert chances_data["distribution"] == {"Reach": 0, "Target": 0, "Likely": 0, "Safety": 0}

        # 4b. R4 Chances on single college with empty profile
        mit_id = SEED_COLLEGES["mit"]["id"]
        res_col_chances = client.get(f"/api/colleges/{mit_id}/chances")
        assert res_col_chances.status_code == 200
        assert res_col_chances.json()["classification"] == "Reach"

        # 5. R5 What-If Scenario empty portfolio
        res_scenario_empty = client.post("/api/portfolio/scenario", json={})
        assert res_scenario_empty.status_code == 200
        assert res_scenario_empty.json()["results"] == []
        assert res_scenario_empty.json()["count"] == 0

        # 6. R6 Alumni Outcomes (field-of-study)
        res_fos = client.get(f"/api/colleges/{mit_id}/field-of-study")
        assert res_fos.status_code == 200
        fos_data = res_fos.json()
        assert "majors" in fos_data
        assert isinstance(fos_data["majors"], list)

        # 7. R7 Requirements Matrix empty state
        res_matrix = client.get("/api/portfolio/requirements-matrix")
        assert res_matrix.status_code == 200
        matrix_data = res_matrix.json()
        assert matrix_data["matrix"] == []
        assert matrix_data["colleges"] == []
        assert matrix_data["summary_counts"] == {}
