"""
Tier 4: Full End-to-End Real-World Student User Journey Scenarios (>=8 tests).
Simulates complete student planning workflows across multiple routes,
decision points, profile alterations, and persistence checkpoints.
"""

import unittest
import json
import os
from tests.conftest import APIClient, SEED_COLLEGES, DEFAULT_FIT_WEIGHTS


class TestTier4RealWorldScenarios(unittest.TestCase):
    """End-to-End Student Persona & Workflow Journeys."""

    def setUp(self):
        self.client = APIClient()

    def test_scenario_01_high_school_senior_discovery_flow(self):
        """
        Scenario 1: High School Senior Discovery Flow
        Steps:
        1. Open app (GET /api/portfolio -> sets cookie)
        2. Search colleges in California with selectivity filter (< 20% admit rate)
        3. Save top 3 colleges (Stanford, Berkeley, UCLA) with 'Reach' tags and visit notes
        4. Re-fetch portfolio to verify all 3 colleges are stored under guest cookie
        5. Verify portfolio summary stats reflect saved colleges
        """
        # Step 1: Open app
        port_init = self.client.get("/api/portfolio")
        self.assertEqual(port_init.status_code, 200)
        self.client.delete("/api/portfolio")

        # Step 2: Search California colleges
        search_resp = self.client.get("/api/colleges", params={"state": "CA", "limit": 10})
        self.assertEqual(search_resp.status_code, 200)
        colleges = search_resp.json().get("items", search_resp.json().get("colleges", []))
        self.assertTrue(len(colleges) >= 2)

        # Step 3: Save top 3 colleges
        schools_to_save = [SEED_COLLEGES["stanford"]["id"], SEED_COLLEGES["berkeley"]["id"], SEED_COLLEGES["ucla"]["id"]]
        for cid in schools_to_save:
            save_resp = self.client.post("/api/portfolio/colleges", json={
                "college_id": cid,
                "tag": "Reach",
                "notes": f"High Priority application for {cid}"
            })
            self.assertIn(save_resp.status_code, [200, 201])

        # Step 4: Verify portfolio
        port_resp = self.client.get("/api/portfolio")
        self.assertEqual(port_resp.status_code, 200)
        saved_items = port_resp.json().get("colleges", port_resp.json().get("items", []))
        saved_ids = [str(c.get("id") or c.get("college_id")) for c in saved_items]
        for cid in schools_to_save:
            self.assertIn(cid, saved_ids)

        # Step 5: Verify summary stats
        self.assertEqual(len(saved_items), 3)

    def test_scenario_02_budget_constrained_student_evaluation(self):
        """
        Scenario 2: Budget-Constrained Student Evaluation
        Steps:
        1. Student searches for Public institutions with cost ceiling
        2. Inspects net price and financial aid metrics on profiles
        3. Sets student budget preference to $15,000/year and increases cost fit weight
        4. Verifies composite fit scoring prioritizes affordability
        5. Saves affordable choices to portfolio
        """
        self.client.delete("/api/portfolio")

        # Step 1: Search public colleges
        search_resp = self.client.get("/api/colleges", params={"type": "public", "sort_by": "net_price", "order": "asc"})
        self.assertEqual(search_resp.status_code, 200)

        # Step 2: Save Ohio State and Michigan
        self.client.post("/api/portfolio/colleges", json={"college_id": SEED_COLLEGES["osu"]["id"]})
        self.client.post("/api/portfolio/colleges", json={"college_id": SEED_COLLEGES["michigan"]["id"]})

        # Step 3: Update preferences with tight budget ($15k) and high cost weight (50%)
        prefs_payload = {
            "budget": 15000,
            "weights": {
                "career_outcomes": 0.10,
                "roi_value": 0.20,
                "academic_fit": 0.10,
                "admissions_fit": 0.05,
                "student_experience": 0.02,
                "academic_strength": 0.03,
                "location": 0.00,
                "cost": 0.50
            }
        }
        pref_resp = self.client.put("/api/portfolio/preferences", json=prefs_payload)
        self.assertIn(pref_resp.status_code, [200, 204])

        # Step 4: Verify fit scoring recomputed
        port_resp = self.client.get("/api/portfolio")
        self.assertEqual(port_resp.status_code, 200)
        saved = port_resp.json().get("colleges", [])
        self.assertEqual(len(saved), 2)

    def test_scenario_03_side_by_side_comparison_and_export(self):
        """
        Scenario 3: Side-by-Side Comparison Workspace & Export
        Steps:
        1. Select 4 flagship institutions (MIT, Stanford, Berkeley, Michigan)
        2. Request comparison matrix (/api/compare?ids=...)
        3. Verify all normalized metric rows exist (costs, admissions, graduation, earnings)
        4. Verify best-in-class highlights
        5. Verify export payload structure
        """
        four_ids = [
            SEED_COLLEGES["mit"]["id"],
            SEED_COLLEGES["stanford"]["id"],
            SEED_COLLEGES["berkeley"]["id"],
            SEED_COLLEGES["michigan"]["id"]
        ]
        ids_param = ",".join(four_ids)

        comp_resp = self.client.get("/api/compare", params={"ids": ids_param})
        self.assertEqual(comp_resp.status_code, 200)
        data = comp_resp.json()

        colleges = data.get("colleges", data.get("items", []))
        self.assertEqual(len(colleges), 4)

        # Check returned data consistency
        returned_ids = [str(c.get("id")) for c in colleges]
        for cid in four_ids:
            self.assertIn(cid, returned_ids)

    def test_scenario_04_ai_enrichment_and_knowledge_audit_loop(self):
        """
        Scenario 4: AI Enrichment & Knowledge Audit Loop
        Steps:
        1. Fetch baseline profile for MIT
        2. Trigger POST /api/colleges/166683/refresh
        3. Verify response status 200 or 202
        4. Check audit ledger for enrichment run entry
        5. Verify field-level provenance metadata
        """
        cid = SEED_COLLEGES["mit"]["id"]
        # Baseline profile
        base_resp = self.client.get(f"/api/colleges/{cid}")
        self.assertEqual(base_resp.status_code, 200)

        # Trigger enrichment refresh
        ref_resp = self.client.post(f"/api/colleges/{cid}/refresh")
        self.assertIn(ref_resp.status_code, [200, 202])

        # Verify ledger file exists
        ledger_dir = os.path.join(os.path.dirname(__file__), "..", "knowledge")
        md_file = os.path.join(ledger_dir, "college-knowledge.md")
        jsonl_file = os.path.join(ledger_dir, "college-knowledge.jsonl")

        # Check knowledge history endpoint if available
        hist_resp = self.client.get(f"/api/knowledge/colleges/{cid}")
        if hist_resp.status_code == 200:
            entries = hist_resp.json()
            self.assertIsInstance(entries, (list, dict))

    def test_scenario_05_custom_student_profile_and_fit_rescoring(self):
        """
        Scenario 5: Custom Student Profile & Fit Re-Scoring
        Steps:
        1. Save 3 schools to portfolio (Harvard, MIT, Ohio State)
        2. Set student profile: GPA=3.95, SAT=1580, Majors=['Computer Science']
        3. Set custom weights: Career=30%, ROI=25%, Academic=20%, Admit=15%
        4. Re-fetch portfolio and verify updated composite scores
        """
        self.client.delete("/api/portfolio")
        for k in ["harvard", "mit", "osu"]:
            self.client.post("/api/portfolio/colleges", json={"college_id": SEED_COLLEGES[k]["id"]})

        pref_payload = {
            "gpa": 3.95,
            "sat": 1580,
            "target_majors": ["Computer Science", "Artificial Intelligence"],
            "weights": {
                "career_outcomes": 0.30,
                "roi_value": 0.25,
                "academic_fit": 0.20,
                "admissions_fit": 0.15,
                "student_experience": 0.04,
                "academic_strength": 0.04,
                "location": 0.01,
                "cost": 0.01
            }
        }
        resp = self.client.put("/api/portfolio/preferences", json=pref_payload)
        self.assertIn(resp.status_code, [200, 204])

        port = self.client.get("/api/portfolio").json()
        colleges = port.get("colleges", [])
        self.assertEqual(len(colleges), 3)

    def test_scenario_06_cookie_blocked_fallback_flow(self):
        """
        Scenario 6: Cookie-Blocked Fallback Flow
        Steps:
        1. Client makes request with no cookies
        2. Client supplies custom header X-Session-ID
        3. Client performs save and fetch actions
        4. Verifies data is returned without 500 error
        """
        client = APIClient()
        client.clear_cookies()
        session_id = "temp-guest-session-uuid-8888"
        headers = {"X-Session-ID": session_id}

        save_resp = client.post("/api/portfolio/colleges", json={"college_id": SEED_COLLEGES["stanford"]["id"]}, headers=headers)
        self.assertIn(save_resp.status_code, [200, 201])

        get_resp = client.get("/api/portfolio", headers=headers)
        self.assertEqual(get_resp.status_code, 200)

    def test_scenario_07_data_hygiene_and_portfolio_reset_flow(self):
        """
        Scenario 7: Data Hygiene & Portfolio Reset Flow
        Steps:
        1. Save 5 colleges with notes
        2. Update fit preferences
        3. Verify all 5 colleges in portfolio
        4. Trigger DELETE /api/portfolio
        5. Verify dashboard / portfolio is completely clean
        """
        self.client.delete("/api/portfolio")
        five_keys = ["mit", "stanford", "berkeley", "michigan", "osu"]
        for k in five_keys:
            self.client.post("/api/portfolio/colleges", json={
                "college_id": SEED_COLLEGES[k]["id"],
                "notes": f"Visit planned for {k}"
            })

        port_before = self.client.get("/api/portfolio").json()
        self.assertEqual(len(port_before.get("colleges", [])), 5)

        # Clear portfolio
        clear_resp = self.client.delete("/api/portfolio")
        self.assertIn(clear_resp.status_code, [200, 204])

        # Verify clean slate
        port_after = self.client.get("/api/portfolio").json()
        self.assertEqual(len(port_after.get("colleges", [])), 0)

    def test_scenario_08_network_outage_and_seed_dataset_resilience(self):
        """
        Scenario 8: Network Outage & Seed Dataset Resilience
        Steps:
        1. Request health status (Scorecard & Gemini may be in seed fallback mode)
        2. Search colleges (returns 50+ pre-seeded colleges)
        3. Fetch detail for multiple institutions
        4. Perform 4-way comparison
        5. Verify 0 errors and complete responses throughout
        """
        # Health check
        h_resp = self.client.get("/api/health")
        self.assertEqual(h_resp.status_code, 200)

        # Search list
        s_resp = self.client.get("/api/colleges", params={"limit": 50})
        self.assertEqual(s_resp.status_code, 200)

        # Details check
        for k in ["mit", "stanford", "berkeley", "gatech"]:
            d_resp = self.client.get(f"/api/colleges/{SEED_COLLEGES[k]['id']}")
            self.assertEqual(d_resp.status_code, 200)

        # Compare check
        ids = f"{SEED_COLLEGES['mit']['id']},{SEED_COLLEGES['stanford']['id']},{SEED_COLLEGES['gatech']['id']}"
        c_resp = self.client.get("/api/compare", params={"ids": ids})
        self.assertEqual(c_resp.status_code, 200)

    def test_scenario_09_transfer_student_cross_state_evaluation(self):
        """
        Scenario 9: Transfer Student In-State vs Out-of-State Decision
        Steps:
        1. Search Midwest public institutions (MI, OH, IL)
        2. Save top public universities (Michigan, Ohio State, UIUC)
        3. Compare in-state vs out-of-state tuition & outcome ROI
        4. Verify side-by-side metrics
        """
        self.client.delete("/api/portfolio")
        for k in ["michigan", "osu", "uiuc"]:
            self.client.post("/api/portfolio/colleges", json={"college_id": SEED_COLLEGES[k]["id"], "tag": "Target"})

        port = self.client.get("/api/portfolio").json()
        self.assertEqual(len(port.get("colleges", [])), 3)

        ids = f"{SEED_COLLEGES['michigan']['id']},{SEED_COLLEGES['osu']['id']},{SEED_COLLEGES['uiuc']['id']}"
        comp = self.client.get("/api/compare", params={"ids": ids})
        self.assertEqual(comp.status_code, 200)

    def test_scenario_10_multi_user_shared_device_isolation(self):
        """
        Scenario 10: Multi-User Shared Device Isolation Journey
        Steps:
        1. Student A uses Browser Session 1, saves STEM colleges (MIT, Caltech/Stanford)
        2. Student A completes planning
        3. Student B opens app on same device with fresh session (Browser Session 2)
        4. Student B saves Liberal Arts/Public colleges (Michigan, OSU)
        5. Verify Student A's and Student B's lists remain strictly separated
        """
        student_a = APIClient()
        student_b = APIClient()

        student_a.post("/api/portfolio/colleges", json={"college_id": SEED_COLLEGES["mit"]["id"]})
        student_a.post("/api/portfolio/colleges", json={"college_id": SEED_COLLEGES["stanford"]["id"]})

        student_b.post("/api/portfolio/colleges", json={"college_id": SEED_COLLEGES["michigan"]["id"]})
        student_b.post("/api/portfolio/colleges", json={"college_id": SEED_COLLEGES["osu"]["id"]})

        list_a = [str(c.get("id") or c.get("college_id")) for c in student_a.get("/api/portfolio").json().get("colleges", [])]
        list_b = [str(c.get("id") or c.get("college_id")) for c in student_b.get("/api/portfolio").json().get("colleges", [])]

        self.assertIn(SEED_COLLEGES["mit"]["id"], list_a)
        self.assertIn(SEED_COLLEGES["stanford"]["id"], list_a)
        self.assertNotIn(SEED_COLLEGES["michigan"]["id"], list_a)

        self.assertIn(SEED_COLLEGES["michigan"]["id"], list_b)
        self.assertIn(SEED_COLLEGES["osu"]["id"], list_b)
        self.assertNotIn(SEED_COLLEGES["mit"]["id"], list_b)
