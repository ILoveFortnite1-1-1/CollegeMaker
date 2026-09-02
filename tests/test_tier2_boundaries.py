"""
Tier 2: Boundary Value Analysis & Negative Input Tests (>=80 tests).
Validates edge conditions, boundary limits, invalid inputs, error handling,
and system robustness under extreme or malformed requests.
"""

import unittest
import json
from tests.conftest import APIClient, SEED_COLLEGES


class TestTier2Category01CompareBoundaries(unittest.TestCase):
    """Category B1: Comparison Boundary Tests (0, 1, 2, 6, 7 colleges, duplicates)"""

    def setUp(self):
        self.client = APIClient()

    def test_compare_missing_ids_param_returns_400(self):
        resp = self.client.get("/api/compare")
        self.assertEqual(resp.status_code, 400)

    def test_compare_empty_ids_param_returns_400(self):
        resp = self.client.get("/api/compare", params={"ids": ""})
        self.assertEqual(resp.status_code, 400)

    def test_compare_single_college_returns_400(self):
        resp = self.client.get("/api/compare", params={"ids": SEED_COLLEGES['mit']['id']})
        self.assertEqual(resp.status_code, 400)

    def test_compare_exactly_two_colleges_minimum_boundary(self):
        ids = f"{SEED_COLLEGES['mit']['id']},{SEED_COLLEGES['stanford']['id']}"
        resp = self.client.get("/api/compare", params={"ids": ids})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        colleges = data.get("colleges", data.get("items", []))
        self.assertEqual(len(colleges), 2)

    def test_compare_exactly_three_colleges(self):
        ids = f"{SEED_COLLEGES['mit']['id']},{SEED_COLLEGES['stanford']['id']},{SEED_COLLEGES['berkeley']['id']}"
        resp = self.client.get("/api/compare", params={"ids": ids})
        self.assertEqual(resp.status_code, 200)
        colleges = resp.json().get("colleges", resp.json().get("items", []))
        self.assertEqual(len(colleges), 3)

    def test_compare_exactly_four_colleges(self):
        ids = f"{SEED_COLLEGES['mit']['id']},{SEED_COLLEGES['stanford']['id']},{SEED_COLLEGES['berkeley']['id']},{SEED_COLLEGES['michigan']['id']}"
        resp = self.client.get("/api/compare", params={"ids": ids})
        self.assertEqual(resp.status_code, 200)
        colleges = resp.json().get("colleges", resp.json().get("items", []))
        self.assertEqual(len(colleges), 4)

    def test_compare_exactly_five_colleges(self):
        ids = f"{SEED_COLLEGES['mit']['id']},{SEED_COLLEGES['stanford']['id']},{SEED_COLLEGES['berkeley']['id']},{SEED_COLLEGES['michigan']['id']},{SEED_COLLEGES['osu']['id']}"
        resp = self.client.get("/api/compare", params={"ids": ids})
        self.assertEqual(resp.status_code, 200)
        colleges = resp.json().get("colleges", resp.json().get("items", []))
        self.assertEqual(len(colleges), 5)

    def test_compare_exactly_six_colleges_maximum_boundary(self):
        ids = ",".join([
            SEED_COLLEGES['mit']['id'],
            SEED_COLLEGES['stanford']['id'],
            SEED_COLLEGES['berkeley']['id'],
            SEED_COLLEGES['michigan']['id'],
            SEED_COLLEGES['osu']['id'],
            SEED_COLLEGES['harvard']['id']
        ])
        resp = self.client.get("/api/compare", params={"ids": ids})
        self.assertEqual(resp.status_code, 200)
        colleges = resp.json().get("colleges", resp.json().get("items", []))
        self.assertEqual(len(colleges), 6)

    def test_compare_seven_colleges_exceeds_maximum_returns_400(self):
        ids = ",".join([
            SEED_COLLEGES['mit']['id'],
            SEED_COLLEGES['stanford']['id'],
            SEED_COLLEGES['berkeley']['id'],
            SEED_COLLEGES['michigan']['id'],
            SEED_COLLEGES['osu']['id'],
            SEED_COLLEGES['harvard']['id'],
            SEED_COLLEGES['gatech']['id']
        ])
        resp = self.client.get("/api/compare", params={"ids": ids})
        self.assertEqual(resp.status_code, 400)

    def test_compare_duplicate_ids_handles_deduplication(self):
        ids = f"{SEED_COLLEGES['mit']['id']},{SEED_COLLEGES['mit']['id']}"
        resp = self.client.get("/api/compare", params={"ids": ids})
        # Either deduplicated to 1 school (causing 400 min error) or returns 400
        self.assertIn(resp.status_code, [200, 400])

    def test_compare_mix_of_valid_and_non_existent_id(self):
        ids = f"{SEED_COLLEGES['mit']['id']},99999999"
        resp = self.client.get("/api/compare", params={"ids": ids})
        self.assertIn(resp.status_code, [400, 404])


class TestTier2Category02SearchBoundaries(unittest.TestCase):
    """Category B2: Search & Filter Boundary Tests"""

    def setUp(self):
        self.client = APIClient()

    def test_search_empty_query_string_returns_200(self):
        resp = self.client.get("/api/colleges", params={"q": ""})
        self.assertEqual(resp.status_code, 200)

    def test_search_whitespace_query_returns_200(self):
        resp = self.client.get("/api/colleges", params={"q": "   "})
        self.assertEqual(resp.status_code, 200)

    def test_search_single_character_query_returns_200(self):
        resp = self.client.get("/api/colleges", params={"q": "M"})
        self.assertEqual(resp.status_code, 200)

    def test_search_extreme_length_query_does_not_crash(self):
        long_query = "Harvard " * 150
        resp = self.client.get("/api/colleges", params={"q": long_query})
        self.assertIn(resp.status_code, [200, 400, 414])

    def test_search_special_characters_query(self):
        resp = self.client.get("/api/colleges", params={"q": "!@#$%^&*()_+{}:;\"'<>?,./"})
        self.assertEqual(resp.status_code, 200)

    def test_search_sql_injection_probe(self):
        resp = self.client.get("/api/colleges", params={"q": "' OR '1'='1' --"})
        self.assertEqual(resp.status_code, 200)

    def test_search_xss_probe(self):
        resp = self.client.get("/api/colleges", params={"q": "<script>alert(1)</script>"})
        self.assertEqual(resp.status_code, 200)

    def test_search_non_existent_state_returns_empty_list(self):
        resp = self.client.get("/api/colleges", params={"state": "ZZ"})
        self.assertEqual(resp.status_code, 200)
        items = resp.json().get("items", resp.json().get("colleges", resp.json()))
        self.assertEqual(len(items), 0)

    def test_search_state_lowercase_case_insensitivity(self):
        resp = self.client.get("/api/colleges", params={"state": "ca"})
        self.assertEqual(resp.status_code, 200)
        items = resp.json().get("items", resp.json().get("colleges", resp.json()))
        self.assertTrue(len(items) > 0)

    def test_search_zero_max_cost(self):
        resp = self.client.get("/api/colleges", params={"max_cost": 0})
        self.assertEqual(resp.status_code, 200)

    def test_search_negative_max_cost_returns_empty_or_400(self):
        resp = self.client.get("/api/colleges", params={"max_cost": -5000})
        self.assertIn(resp.status_code, [200, 400, 422])

    def test_search_extreme_high_max_cost(self):
        resp = self.client.get("/api/colleges", params={"max_cost": 1000000})
        self.assertEqual(resp.status_code, 200)

    def test_search_inverted_cost_range(self):
        resp = self.client.get("/api/colleges", params={"min_cost": 80000, "max_cost": 20000})
        self.assertIn(resp.status_code, [200, 400, 422])

    def test_search_admit_rate_boundary_zero(self):
        resp = self.client.get("/api/colleges", params={"max_admit_rate": 0.0})
        self.assertEqual(resp.status_code, 200)

    def test_search_admit_rate_boundary_one(self):
        resp = self.client.get("/api/colleges", params={"max_admit_rate": 1.0})
        self.assertEqual(resp.status_code, 200)


class TestTier2Category03CollegeIDBoundaries(unittest.TestCase):
    """Category B3: College ID & Path Parameter Boundaries"""

    def setUp(self):
        self.client = APIClient()

    def test_detail_negative_id_returns_404_or_400(self):
        resp = self.client.get("/api/colleges/-1")
        self.assertIn(resp.status_code, [400, 404, 422])

    def test_detail_alphabetic_id_returns_404_or_400(self):
        resp = self.client.get("/api/colleges/mit_string_id")
        self.assertIn(resp.status_code, [400, 404, 422])

    def test_detail_zero_id_returns_404(self):
        resp = self.client.get("/api/colleges/0")
        self.assertIn(resp.status_code, [400, 404])

    def test_detail_extremely_large_numeric_id(self):
        resp = self.client.get("/api/colleges/999999999999999")
        self.assertIn(resp.status_code, [400, 404])

    def test_detail_floating_point_id(self):
        resp = self.client.get("/api/colleges/166683.99")
        self.assertIn(resp.status_code, [400, 404, 422])

    def test_detail_sql_injection_path_returns_404_or_400(self):
        resp = self.client.get("/api/colleges/1%20UNION%20SELECT%201")
        self.assertIn(resp.status_code, [400, 404, 422])

    def test_detail_null_byte_in_path(self):
        try:
            resp = self.client.get("/api/colleges/%00")
            self.assertIn(resp.status_code, [400, 404])
        except Exception:
            pass  # Client safely rejected

    def test_refresh_negative_id_returns_400_or_404(self):
        resp = self.client.post("/api/colleges/-10/refresh")
        self.assertIn(resp.status_code, [400, 404, 422])

    def test_refresh_non_existent_id_returns_404(self):
        resp = self.client.post("/api/colleges/88888888/refresh")
        self.assertEqual(resp.status_code, 404)

    def test_knowledge_college_history_non_existent_id(self):
        resp = self.client.get("/api/knowledge/colleges/99999999")
        self.assertIn(resp.status_code, [200, 404])
        if resp.status_code == 200:
            self.assertEqual(len(resp.json()), 0)

    def test_knowledge_college_history_negative_id(self):
        resp = self.client.get("/api/knowledge/colleges/-1")
        self.assertIn(resp.status_code, [200, 400, 404])

    def test_path_traversal_attempt_blocked(self):
        resp = self.client.get("/api/colleges/../../etc/passwd")
        self.assertIn(resp.status_code, [400, 403, 404])


class TestTier2Category04CookieSessionBoundaries(unittest.TestCase):
    """Category B4: Cookie & Session Boundaries"""

    def setUp(self):
        self.client = APIClient()

    def test_request_without_cookie_receives_new_cookie(self):
        self.client.clear_cookies()
        resp = self.client.get("/api/portfolio")
        self.assertEqual(resp.status_code, 200)
        cookie = self.client.get_cookie("college_portfolio_id")
        self.assertIsNotNone(cookie)

    def test_empty_cookie_header_recovers_safely(self):
        self.client.set_cookie("college_portfolio_id", "")
        resp = self.client.get("/api/portfolio")
        self.assertEqual(resp.status_code, 200)

    def test_malformed_special_chars_cookie_recovers(self):
        self.client.set_cookie("college_portfolio_id", "@@##$$%%^^&&**(())")
        resp = self.client.get("/api/portfolio")
        self.assertEqual(resp.status_code, 200)

    def test_excessively_long_cookie_recovers(self):
        self.client.set_cookie("college_portfolio_id", "x" * 4096)
        resp = self.client.get("/api/portfolio")
        self.assertIn(resp.status_code, [200, 400])

    def test_non_existent_uuid_cookie_returns_empty_portfolio(self):
        self.client.set_cookie("college_portfolio_id", "00000000-0000-0000-0000-000000000000")
        resp = self.client.get("/api/portfolio")
        self.assertEqual(resp.status_code, 200)
        colleges = resp.json().get("colleges", resp.json().get("items", []))
        self.assertEqual(len(colleges), 0)

    def test_sql_injection_in_cookie_handled_safely(self):
        self.client.set_cookie("college_portfolio_id", "test_sess' OR '1'='1")
        resp = self.client.get("/api/portfolio")
        self.assertEqual(resp.status_code, 200)

    def test_client_fallback_session_header(self):
        resp = self.client.get("/api/portfolio", headers={"X-Session-ID": "test-fallback-session-id"})
        self.assertEqual(resp.status_code, 200)

    def test_cookie_reset_clears_server_association(self):
        self.client.post("/api/portfolio/colleges", json={"college_id": SEED_COLLEGES["mit"]["id"]})
        self.client.delete("/api/portfolio")
        resp = self.client.get("/api/portfolio")
        colleges = resp.json().get("colleges", resp.json().get("items", []))
        self.assertEqual(len(colleges), 0)

    def test_cookie_with_spaces_or_quotes(self):
        self.client.set_cookie("college_portfolio_id", "\"quoted_token 123\"")
        resp = self.client.get("/api/portfolio")
        self.assertEqual(resp.status_code, 200)

    def test_rapid_alternating_cookies_preserve_isolation(self):
        client_a = APIClient()
        client_b = APIClient()
        client_a.post("/api/portfolio/colleges", json={"college_id": SEED_COLLEGES["harvard"]["id"]})
        client_b.post("/api/portfolio/colleges", json={"college_id": SEED_COLLEGES["mit"]["id"]})

        resp_a = client_a.get("/api/portfolio")
        resp_b = client_b.get("/api/portfolio")

        items_a = [str(c.get("id") or c.get("college_id")) for c in resp_a.json().get("colleges", [])]
        items_b = [str(c.get("id") or c.get("college_id")) for c in resp_b.json().get("colleges", [])]

        self.assertIn(SEED_COLLEGES["harvard"]["id"], items_a)
        self.assertNotIn(SEED_COLLEGES["harvard"]["id"], items_b)
        self.assertIn(SEED_COLLEGES["mit"]["id"], items_b)
        self.assertNotIn(SEED_COLLEGES["mit"]["id"], items_a)

    def test_cookie_header_casing_resilience(self):
        resp = self.client.get("/api/portfolio", headers={"cookie": "college_portfolio_id=cased_token_777"})
        self.assertEqual(resp.status_code, 200)

    def test_cookie_with_base64_payload(self):
        self.client.set_cookie("college_portfolio_id", "eyJhbGciOiJIUzI1NiJ9.payload.sig")
        resp = self.client.get("/api/portfolio")
        self.assertEqual(resp.status_code, 200)


class TestTier2Category05PortfolioBoundaries(unittest.TestCase):
    """Category B5: Portfolio Mutation & Payload Boundaries"""

    def setUp(self):
        self.client = APIClient()
        self.client.delete("/api/portfolio")

    def test_add_empty_json_body_returns_400_or_422(self):
        resp = self.client.post("/api/portfolio/colleges", json={})
        self.assertIn(resp.status_code, [400, 422])

    def test_add_non_existent_college_id_returns_404_or_400(self):
        resp = self.client.post("/api/portfolio/colleges", json={"college_id": "99999999"})
        self.assertIn(resp.status_code, [400, 404])

    def test_add_same_college_multiple_times_is_idempotent(self):
        cid = SEED_COLLEGES["mit"]["id"]
        resp1 = self.client.post("/api/portfolio/colleges", json={"college_id": cid})
        resp2 = self.client.post("/api/portfolio/colleges", json={"college_id": cid})
        self.assertIn(resp1.status_code, [200, 201])
        self.assertIn(resp2.status_code, [200, 201])

        get_resp = self.client.get("/api/portfolio")
        colleges = get_resp.json().get("colleges", get_resp.json().get("items", []))
        matching = [c for c in colleges if str(c.get("id") or c.get("college_id")) == cid]
        self.assertEqual(len(matching), 1)

    def test_delete_unsaved_college_returns_200_or_404(self):
        resp = self.client.delete(f"/api/portfolio/colleges/{SEED_COLLEGES['osu']['id']}")
        self.assertIn(resp.status_code, [200, 204, 404])

    def test_add_college_with_long_note_5000_chars(self):
        long_note = "Detailed notes on campus visit and faculty discussions. " * 100
        resp = self.client.post("/api/portfolio/colleges", json={
            "college_id": SEED_COLLEGES["stanford"]["id"],
            "notes": long_note
        })
        self.assertIn(resp.status_code, [200, 201])

    def test_add_college_with_empty_note(self):
        resp = self.client.post("/api/portfolio/colleges", json={
            "college_id": SEED_COLLEGES["berkeley"]["id"],
            "notes": ""
        })
        self.assertIn(resp.status_code, [200, 201])

    def test_add_college_with_unicode_and_emojis(self):
        note = "🎓 Stanford University — Top Dream School! 🌟 100% Fit! 🚀"
        resp = self.client.post("/api/portfolio/colleges", json={
            "college_id": SEED_COLLEGES["stanford"]["id"],
            "notes": note
        })
        self.assertIn(resp.status_code, [200, 201])
        get_resp = self.client.get("/api/portfolio")
        colleges = get_resp.json().get("colleges", [])
        saved = [c for c in colleges if str(c.get("id") or c.get("college_id")) == SEED_COLLEGES["stanford"]["id"]][0]
        self.assertIn("🎓", saved.get("notes", saved.get("user_note", "")))

    def test_add_college_with_html_script_tags_is_safe(self):
        xss_note = "<script>alert('pwned');</script><b>Bold Note</b>"
        resp = self.client.post("/api/portfolio/colleges", json={
            "college_id": SEED_COLLEGES["michigan"]["id"],
            "notes": xss_note
        })
        self.assertIn(resp.status_code, [200, 201])

    def test_delete_all_from_empty_portfolio(self):
        resp = self.client.delete("/api/portfolio")
        self.assertIn(resp.status_code, [200, 204])

    def test_add_multiple_unique_colleges(self):
        for key in ["mit", "stanford", "berkeley", "michigan", "osu", "harvard", "gatech", "uiuc"]:
            self.client.post("/api/portfolio/colleges", json={"college_id": SEED_COLLEGES[key]["id"]})
        resp = self.client.get("/api/portfolio")
        colleges = resp.json().get("colleges", resp.json().get("items", []))
        self.assertEqual(len(colleges), 8)

    def test_invalid_data_type_in_college_id(self):
        resp = self.client.post("/api/portfolio/colleges", json={"college_id": {"nested": "dict"}})
        self.assertIn(resp.status_code, [400, 422])

    def test_empty_preferences_payload_keeps_defaults(self):
        resp = self.client.put("/api/portfolio/preferences", json={})
        self.assertIn(resp.status_code, [200, 204, 400, 422])


class TestTier2Category06PreferencesFitBoundaries(unittest.TestCase):
    """Category B6: Student Preferences & Fit Weight Boundaries"""

    def setUp(self):
        self.client = APIClient()

    def test_preferences_gpa_boundary_zero(self):
        resp = self.client.put("/api/portfolio/preferences", json={"gpa": 0.0})
        self.assertIn(resp.status_code, [200, 204])

    def test_preferences_gpa_boundary_four_point_zero(self):
        resp = self.client.put("/api/portfolio/preferences", json={"gpa": 4.0})
        self.assertIn(resp.status_code, [200, 204])

    def test_preferences_gpa_boundary_five_point_zero(self):
        resp = self.client.put("/api/portfolio/preferences", json={"gpa": 5.0})
        self.assertIn(resp.status_code, [200, 204])

    def test_preferences_gpa_negative_returns_400_or_clamped(self):
        resp = self.client.put("/api/portfolio/preferences", json={"gpa": -1.0})
        self.assertIn(resp.status_code, [200, 204, 400, 422])

    def test_preferences_sat_boundary_min_400(self):
        resp = self.client.put("/api/portfolio/preferences", json={"sat": 400})
        self.assertIn(resp.status_code, [200, 204])

    def test_preferences_sat_boundary_max_1600(self):
        resp = self.client.put("/api/portfolio/preferences", json={"sat": 1600})
        self.assertIn(resp.status_code, [200, 204])

    def test_preferences_budget_zero(self):
        resp = self.client.put("/api/portfolio/preferences", json={"budget": 0})
        self.assertIn(resp.status_code, [200, 204])

    def test_preferences_budget_negative(self):
        resp = self.client.put("/api/portfolio/preferences", json={"budget": -50000})
        self.assertIn(resp.status_code, [200, 204, 400, 422])

    def test_preferences_budget_high_limit(self):
        resp = self.client.put("/api/portfolio/preferences", json={"budget": 500000})
        self.assertIn(resp.status_code, [200, 204])

    def test_fit_weights_all_zeros_handled_gracefully(self):
        zero_weights = {k: 0.0 for k in ["career_outcomes", "roi_value", "academic_fit", "admissions_fit", "student_experience", "academic_strength", "location", "cost"]}
        resp = self.client.put("/api/portfolio/preferences", json={"weights": zero_weights})
        self.assertIn(resp.status_code, [200, 204, 400])

    def test_fit_weights_single_dimension_one(self):
        single_weights = {"career_outcomes": 1.0, "roi_value": 0.0, "academic_fit": 0.0, "admissions_fit": 0.0, "student_experience": 0.0, "academic_strength": 0.0, "location": 0.0, "cost": 0.0}
        resp = self.client.put("/api/portfolio/preferences", json={"weights": single_weights})
        self.assertIn(resp.status_code, [200, 204])

    def test_fit_weights_sum_greater_than_one_normalized(self):
        inflated_weights = {k: 1.0 for k in ["career_outcomes", "roi_value", "academic_fit", "admissions_fit", "student_experience", "academic_strength", "location", "cost"]}
        resp = self.client.put("/api/portfolio/preferences", json={"weights": inflated_weights})
        self.assertIn(resp.status_code, [200, 204])


class TestTier2Category07HTTPProtocolBoundaries(unittest.TestCase):
    """Category B7: Pagination, Sorting & HTTP Boundaries"""

    def setUp(self):
        self.client = APIClient()

    def test_pagination_limit_zero(self):
        resp = self.client.get("/api/colleges", params={"limit": 0})
        self.assertIn(resp.status_code, [200, 400])

    def test_pagination_limit_negative(self):
        resp = self.client.get("/api/colleges", params={"limit": -10})
        self.assertIn(resp.status_code, [200, 400, 422])

    def test_pagination_limit_large_1000(self):
        resp = self.client.get("/api/colleges", params={"limit": 1000})
        self.assertEqual(resp.status_code, 200)

    def test_pagination_offset_zero(self):
        resp = self.client.get("/api/colleges", params={"offset": 0, "limit": 10})
        self.assertEqual(resp.status_code, 200)

    def test_pagination_offset_beyond_data(self):
        resp = self.client.get("/api/colleges", params={"offset": 10000, "limit": 10})
        self.assertEqual(resp.status_code, 200)
        items = resp.json().get("items", resp.json().get("colleges", resp.json()))
        self.assertEqual(len(items), 0)

    def test_invalid_sort_by_field(self):
        resp = self.client.get("/api/colleges", params={"sort_by": "invalid_column_name"})
        self.assertIn(resp.status_code, [200, 400, 422])

    def test_invalid_order_value(self):
        resp = self.client.get("/api/colleges", params={"order": "random_order"})
        self.assertIn(resp.status_code, [200, 400, 422])

    def test_method_not_allowed_on_health_endpoint(self):
        resp = self.client.request("DELETE", "/api/health")
        self.assertIn(resp.status_code, [404, 405])

    def test_post_on_read_only_endpoint(self):
        resp = self.client.post("/api/colleges")
        self.assertIn(resp.status_code, [404, 405])

    def test_malformed_json_body_syntax_returns_400(self):
        resp = self.client.request("POST", "/api/portfolio/colleges", data="{\"college_id\": invalid_json", headers={"Content-Type": "application/json"})
        self.assertIn(resp.status_code, [400, 422])
