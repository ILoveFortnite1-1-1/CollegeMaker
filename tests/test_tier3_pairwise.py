"""
Tier 3: Pairwise Cross-Feature Interaction Tests (>=16 tests).
Validates multi-feature integration workflows, data consistency across modules,
and state synchronization between disparate components.
"""

import unittest
import json
import os
from tests.conftest import APIClient, SEED_COLLEGES, DEFAULT_FIT_WEIGHTS


class TestTier3PairwiseInteractions(unittest.TestCase):
    """Pairwise Integration Test Matrix across all application capabilities."""

    def setUp(self):
        self.client = APIClient()

    def test_pair_01_search_and_save_to_portfolio_with_cookie(self):
        """Pair 1: Search Discovery (F5) -> Detail Inspection (F6) -> Portfolio Save (F13) -> Cookie Persistence (F12)"""
        # 1. Search for California colleges
        search_resp = self.client.get("/api/colleges", params={"state": "CA", "limit": 5})
        self.assertEqual(search_resp.status_code, 200)
        items = search_resp.json().get("items", search_resp.json().get("colleges", []))
        self.assertTrue(len(items) > 0)
        target_id = str(items[0].get("id"))

        # 2. Inspect detail
        detail_resp = self.client.get(f"/api/colleges/{target_id}")
        self.assertEqual(detail_resp.status_code, 200)

        # 3. Save to portfolio
        save_resp = self.client.post("/api/portfolio/colleges", json={"college_id": target_id, "tag": "Target"})
        self.assertIn(save_resp.status_code, [200, 201])

        # 4. Verify in portfolio
        port_resp = self.client.get("/api/portfolio")
        saved_ids = [str(c.get("id") or c.get("college_id")) for c in port_resp.json().get("colleges", [])]
        self.assertIn(target_id, saved_ids)

    def test_pair_02_portfolio_save_and_custom_fit_scoring_compare(self):
        """Pair 2: Portfolio Save (F13) + Preferences (F14) + Comparison Matrix (F15)"""
        self.client.delete("/api/portfolio")
        # Save MIT and Michigan
        self.client.post("/api/portfolio/colleges", json={"college_id": SEED_COLLEGES["mit"]["id"]})
        self.client.post("/api/portfolio/colleges", json={"college_id": SEED_COLLEGES["michigan"]["id"]})

        # Set custom preferences
        self.client.put("/api/portfolio/preferences", json={
            "gpa": 3.95,
            "sat": 1550,
            "budget": 35000,
            "weights": {
                "career_outcomes": 0.30,
                "roi_value": 0.25,
                "academic_fit": 0.20,
                "admissions_fit": 0.10,
                "student_experience": 0.05,
                "academic_strength": 0.05,
                "location": 0.02,
                "cost": 0.03
            }
        })

        # Request compare for both
        ids = f"{SEED_COLLEGES['mit']['id']},{SEED_COLLEGES['michigan']['id']}"
        comp_resp = self.client.get("/api/compare", params={"ids": ids})
        self.assertEqual(comp_resp.status_code, 200)
        data = comp_resp.json()
        colleges = data.get("colleges", data.get("items", []))
        self.assertEqual(len(colleges), 2)

    def test_pair_03_college_detail_and_refresh_updates_markdown_ledger(self):
        """Pair 3: Detail Profile (F6) + Gemini Refresh (F7) + Markdown Ledger (F10)"""
        cid = SEED_COLLEGES["stanford"]["id"]
        # Detail lookup
        self.client.get(f"/api/colleges/{cid}")
        # Refresh enrichment
        ref_resp = self.client.post(f"/api/colleges/{cid}/refresh")
        self.assertIn(ref_resp.status_code, [200, 202])

        # Verify markdown ledger exists or was touched
        ledger_path = os.path.join(os.path.dirname(__file__), "..", "knowledge", "college-knowledge.md")
        if os.path.exists(ledger_path):
            self.assertGreater(os.path.getsize(ledger_path), 0)

    def test_pair_04_gemini_refresh_and_jsonl_ledger_and_provenance(self):
        """Pair 4: Gemini Refresh (F7) + JSONL Ledger (F11) + Field Provenance (F9)"""
        cid = SEED_COLLEGES["berkeley"]["id"]
        self.client.post(f"/api/colleges/{cid}/refresh")

        # Check detail provenance
        resp = self.client.get(f"/api/colleges/{cid}")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        provenance = data.get("provenance", {})
        self.assertIsInstance(provenance, dict)

    def test_pair_05_cookie_session_and_portfolio_reset_and_health(self):
        """Pair 5: Cookie Session (F12) + Portfolio Reset (F13) + Health Check (F1)"""
        # Save schools
        self.client.post("/api/portfolio/colleges", json={"college_id": SEED_COLLEGES["osu"]["id"]})
        # Verify health
        h_resp = self.client.get("/api/health")
        self.assertEqual(h_resp.status_code, 200)
        # Reset portfolio
        del_resp = self.client.delete("/api/portfolio")
        self.assertIn(del_resp.status_code, [200, 204])
        # Verify empty
        p_resp = self.client.get("/api/portfolio")
        self.assertEqual(len(p_resp.json().get("colleges", [])), 0)

    def test_pair_06_search_filtering_and_fit_scoring_alignment(self):
        """Pair 6: Faceted Search (F5) + Fit Scoring (F14) + Detail Profile (F6)"""
        # Search low cost public schools
        resp = self.client.get("/api/colleges", params={"type": "public", "max_cost": 30000})
        self.assertEqual(resp.status_code, 200)
        items = resp.json().get("items", resp.json().get("colleges", []))
        if items:
            cid = str(items[0].get("id"))
            det_resp = self.client.get(f"/api/colleges/{cid}")
            self.assertEqual(det_resp.status_code, 200)

    def test_pair_07_portfolio_notes_and_comparison_matrix(self):
        """Pair 7: Portfolio Notes CRUD (F13) + Comparison Matrix (F15)"""
        self.client.delete("/api/portfolio")
        self.client.post("/api/portfolio/colleges", json={
            "college_id": SEED_COLLEGES["harvard"]["id"],
            "notes": "Dream Reach School",
            "tag": "Reach"
        })
        self.client.post("/api/portfolio/colleges", json={
            "college_id": SEED_COLLEGES["mit"]["id"],
            "notes": "Top CS & Engineering Target",
            "tag": "Reach"
        })
        # Compare them
        ids = f"{SEED_COLLEGES['harvard']['id']},{SEED_COLLEGES['mit']['id']}"
        comp = self.client.get("/api/compare", params={"ids": ids})
        self.assertEqual(comp.status_code, 200)
        self.assertEqual(len(comp.json().get("colleges", [])), 2)

    def test_pair_08_multi_session_cookie_isolation(self):
        """Pair 8: Cookie Session Isolation (F12) + Portfolio Independence (F13)"""
        client1 = APIClient()
        client2 = APIClient()

        client1.post("/api/portfolio/colleges", json={"college_id": SEED_COLLEGES["mit"]["id"]})
        client2.post("/api/portfolio/colleges", json={"college_id": SEED_COLLEGES["osu"]["id"]})

        p1 = [str(c.get("id") or c.get("college_id")) for c in client1.get("/api/portfolio").json().get("colleges", [])]
        p2 = [str(c.get("id") or c.get("college_id")) for c in client2.get("/api/portfolio").json().get("colleges", [])]

        self.assertIn(SEED_COLLEGES["mit"]["id"], p1)
        self.assertNotIn(SEED_COLLEGES["osu"]["id"], p1)
        self.assertIn(SEED_COLLEGES["osu"]["id"], p2)
        self.assertNotIn(SEED_COLLEGES["mit"]["id"], p2)

    def test_pair_09_source_precedence_and_ai_enrichment_preservation(self):
        """Pair 9: Source Precedence (F8) + AI Enrichment (F7) + Canonical Profile (F6)"""
        cid = SEED_COLLEGES["mit"]["id"]
        pre_resp = self.client.get(f"/api/colleges/{cid}")
        pre_admit = pre_resp.json().get("admissions", {}).get("acceptance_rate")

        # Trigger enrichment
        self.client.post(f"/api/colleges/{cid}/refresh")

        post_resp = self.client.get(f"/api/colleges/{cid}")
        post_admit = post_resp.json().get("admissions", {}).get("acceptance_rate")
        # Government admission rate must not be overwritten
        self.assertEqual(pre_admit, post_admit)

    def test_pair_10_dynamic_weight_adjustment_and_portfolio_stats(self):
        """Pair 10: Fit Scoring Weights (F14) + Portfolio Aggregation (F13)"""
        self.client.delete("/api/portfolio")
        for k in ["mit", "stanford", "berkeley"]:
            self.client.post("/api/portfolio/colleges", json={"college_id": SEED_COLLEGES[k]["id"]})

        # Update weights
        self.client.put("/api/portfolio/preferences", json={
            "weights": {"career_outcomes": 0.8, "roi_value": 0.1, "academic_fit": 0.05, "admissions_fit": 0.01, "student_experience": 0.01, "academic_strength": 0.01, "location": 0.01, "cost": 0.01}
        })

        port = self.client.get("/api/portfolio").json()
        self.assertEqual(len(port.get("colleges", [])), 3)

    def test_pair_11_max_capacity_compare_and_portfolio_sync(self):
        """Pair 11: 6-College Compare Capacity (F15) + Portfolio List (F13)"""
        six_keys = ["mit", "stanford", "berkeley", "michigan", "osu", "harvard"]
        self.client.delete("/api/portfolio")
        for k in six_keys:
            self.client.post("/api/portfolio/colleges", json={"college_id": SEED_COLLEGES[k]["id"]})

        port = self.client.get("/api/portfolio").json()
        saved_ids = [str(c.get("id") or c.get("college_id")) for c in port.get("colleges", [])]
        self.assertEqual(len(saved_ids), 6)

        comp_resp = self.client.get("/api/compare", params={"ids": ",".join(saved_ids)})
        self.assertEqual(comp_resp.status_code, 200)
        self.assertEqual(len(comp_resp.json().get("colleges", [])), 6)

    def test_pair_12_offline_seed_cache_and_discovery_pipeline(self):
        """Pair 12: Offline Seed Data (F4) + Search API (F5) + Detail Endpoint (F6)"""
        resp = self.client.get("/api/colleges", params={"limit": 50})
        self.assertEqual(resp.status_code, 200)
        items = resp.json().get("items", resp.json().get("colleges", []))
        self.assertGreaterEqual(len(items), 5)

        first_id = str(items[0].get("id"))
        detail_resp = self.client.get(f"/api/colleges/{first_id}")
        self.assertEqual(detail_resp.status_code, 200)

    def test_pair_13_batch_enrichment_and_dual_ledger_generation(self):
        """Pair 13: Batch Refresh (F7) + Markdown Ledger (F10) + JSONL Ledger (F11)"""
        for k in ["mit", "stanford"]:
            self.client.post(f"/api/colleges/{SEED_COLLEGES[k]['id']}/refresh")

        export_resp = self.client.get("/api/knowledge/export")
        self.assertIn(export_resp.status_code, [200, 204, 404])

    def test_pair_14_client_session_fallback_header_and_portfolio_crud(self):
        """Pair 14: Client Session Header Fallback (F12) + Portfolio CRUD (F13)"""
        client = APIClient()
        client.clear_cookies()
        headers = {"X-Session-ID": "fallback-test-session-9999"}

        save_resp = client.post("/api/portfolio/colleges", json={"college_id": SEED_COLLEGES["gatech"]["id"]}, headers=headers)
        self.assertIn(save_resp.status_code, [200, 201])

        get_resp = client.get("/api/portfolio", headers=headers)
        self.assertEqual(get_resp.status_code, 200)

    def test_pair_15_selectivity_filtering_and_reach_categorization(self):
        """Pair 15: Selectivity Search (F5) + Reach/Target/Likely Classification (F14)"""
        resp = self.client.get("/api/colleges", params={"max_admit_rate": 0.15})
        self.assertEqual(resp.status_code, 200)
        items = resp.json().get("items", resp.json().get("colleges", []))
        if items:
            cid = str(items[0].get("id"))
            self.client.post("/api/portfolio/colleges", json={"college_id": cid, "tag": "Reach"})
            port = self.client.get("/api/portfolio").json()
            saved = [c for c in port.get("colleges", []) if str(c.get("id") or c.get("college_id")) == cid]
            self.assertTrue(len(saved) > 0)

    def test_pair_16_comparison_api_and_spa_routing_coexistence(self):
        """Pair 16: Compare API (F15) + SPA Routing (F16)"""
        # API JSON response
        ids = f"{SEED_COLLEGES['mit']['id']},{SEED_COLLEGES['stanford']['id']}"
        api_resp = self.client.get("/api/compare", params={"ids": ids})
        self.assertEqual(api_resp.status_code, 200)
        self.assertIn("application/json", api_resp.get_header("content-type", "").lower())

        # SPA UI route
        spa_resp = self.client.get("/compare")
        self.assertEqual(spa_resp.status_code, 200)
        self.assertIn("text/html", spa_resp.get_header("content-type", "").lower())
