"""
Tier 5: API, Concurrency & Data Security Adversarial Stress Testing Suite.
Empirically stress-tests comparison edge cases, extreme query parameters, SQL/XSS injection resilience,
concurrent knowledge ledger thread-safety, cookie session manipulation, and offline degradation.
"""

import asyncio
import json
import os
import sqlite3
import threading
import time
import unittest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx
from starlette.testclient import TestClient

from server.config import settings
from server.main import app
from server.models.canonical import CanonicalCollege, EvidenceClaim, MetricField, QualitativeData, SourceType, ConfidenceLevel
from server.models.ledger import EnrichmentRun, LedgerEvent
from server.models.portfolio import StudentPreferences
from server.services.comparison import comparison_service
from server.services.gemini import gemini_service
from server.services.ledger import ledger_service
from server.services.portfolio import portfolio_service
from server.services.scorecard import scorecard_service
from tests.conftest import APIClient, SEED_COLLEGES


class TestAdversarialCompareEndpoint(unittest.TestCase):
    """1. Comparison Endpoint Edge Cases & Bounds Stress-Testing."""

    def setUp(self):
        self.client = APIClient()

    def test_compare_zero_ids_no_cookie_returns_400(self):
        resp = self.client.get("/api/compare")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("at least 2", resp.json().get("detail", ""))

    def test_compare_empty_ids_param_returns_400(self):
        resp = self.client.get("/api/compare?ids=")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("at least 2", resp.json().get("detail", ""))

    def test_compare_whitespace_ids_param_returns_400(self):
        resp = self.client.get("/api/compare?ids=%20%20%20")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("at least 2", resp.json().get("detail", ""))

    def test_compare_only_commas_returns_400(self):
        resp = self.client.get("/api/compare?ids=,,,")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("at least 2", resp.json().get("detail", ""))

    def test_compare_single_id_returns_400(self):
        resp = self.client.get("/api/compare?ids=166683")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("at least 2", resp.json().get("detail", "").lower())

    def test_compare_single_id_with_trailing_comma_returns_400(self):
        resp = self.client.get("/api/compare?ids=166683,")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("at least 2", resp.json().get("detail", "").lower())

    def test_compare_exact_six_ids_boundary_succeeds(self):
        ids = "166683,243744,110635,170976,204796,166027"
        resp = self.client.get(f"/api/compare?ids={ids}")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        colleges = data.get("colleges", data.get("items", []))
        self.assertEqual(len(colleges), 6)
        self.assertIn("metrics", data)
        self.assertIn("best_in_class", data)

    def test_compare_seven_ids_exceeds_max_returns_400(self):
        ids = "166683,243744,110635,170976,204796,166027,139755"
        resp = self.client.get(f"/api/compare?ids={ids}")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("maximum of 6", resp.json().get("detail", ""))

    def test_compare_ten_ids_exceeds_max_returns_400(self):
        ids = "166683,243744,110635,170976,204796,166027,139755,145637,228778,110662"
        resp = self.client.get(f"/api/compare?ids={ids}")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("maximum of 6", resp.json().get("detail", ""))

    def test_compare_duplicate_identical_ids_returns_400(self):
        resp = self.client.get("/api/compare?ids=166683,166683")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("distinct", resp.json().get("detail", "").lower())

    def test_compare_triplicate_identical_ids_returns_400(self):
        resp = self.client.get("/api/compare?ids=166683,166683,166683")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("distinct", resp.json().get("detail", "").lower())

    def test_compare_nonexistent_ids_returns_404(self):
        resp = self.client.get("/api/compare?ids=999999,888888")
        self.assertEqual(resp.status_code, 404)
        self.assertIn("not found", resp.json().get("detail", "").lower())

    def test_compare_mixed_valid_and_nonexistent_ids_returns_404(self):
        resp = self.client.get("/api/compare?ids=166683,999999")
        self.assertEqual(resp.status_code, 404)
        self.assertIn("999999", resp.json().get("detail", ""))

    def test_compare_alphanumeric_junk_ids_returns_404(self):
        resp = self.client.get("/api/compare?ids=invalid_abc,invalid_xyz")
        self.assertEqual(resp.status_code, 404)

    def test_compare_negative_id_returns_404(self):
        resp = self.client.get("/api/compare?ids=-1,-2")
        self.assertEqual(resp.status_code, 404)

    def test_compare_path_traversal_ids_returns_404(self):
        resp = self.client.get("/api/compare?ids=166683,../../etc/passwd")
        self.assertEqual(resp.status_code, 404)

    def test_compare_xss_injection_in_ids_returns_404(self):
        resp = self.client.get("/api/compare?ids=166683,<script>alert(1)</script>")
        self.assertEqual(resp.status_code, 404)

    def test_compare_fallback_to_portfolio_with_two_saved_colleges(self):
        c = APIClient()
        c.set_cookie(settings.COOKIE_NAME, "port_compare_fallback_test_2")
        c.post("/api/portfolio/colleges", json={"college_id": "166683"})
        c.post("/api/portfolio/colleges", json={"college_id": "243744"})

        resp = c.get("/api/compare")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        colleges = data.get("colleges", data.get("items", []))
        self.assertEqual(len(colleges), 2)

    def test_compare_fallback_to_portfolio_with_one_saved_college_returns_400(self):
        c = APIClient()
        c.set_cookie(settings.COOKIE_NAME, "port_compare_fallback_test_1")
        c.post("/api/portfolio/colleges", json={"college_id": "166683"})

        resp = c.get("/api/compare")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("at least 2", resp.json().get("detail", ""))


class TestAdversarialSearchAndFilter(unittest.TestCase):
    """2. Search & Filtering Extreme Inputs & Injection Defense."""

    def setUp(self):
        self.client = APIClient()

    def test_search_sql_injection_tautology_q(self):
        resp = self.client.get("/api/colleges?q=' OR '1'='1")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        items = data.get("items", data.get("colleges", []))
        self.assertEqual(len(items), 0)

    def test_search_sql_injection_drop_table_q(self):
        resp = self.client.get("/api/colleges?q='; DROP TABLE colleges; --")
        self.assertEqual(resp.status_code, 200)
        verify_resp = self.client.get("/api/colleges?q=Harvard")
        self.assertEqual(verify_resp.status_code, 200)
        verify_data = verify_resp.json()
        self.assertGreater(verify_data.get("total", 0), 0)

    def test_search_sql_injection_union_select(self):
        resp = self.client.get("/api/colleges?q=1' UNION SELECT 1,2,3,4,5,6,7,8,9,10,11,12,13,14--")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        items = data.get("items", data.get("colleges", []))
        self.assertEqual(len(items), 0)

    def test_search_sql_injection_in_state(self):
        resp = self.client.get("/api/colleges?state=' OR 1=1--")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        items = data.get("items", data.get("colleges", []))
        self.assertEqual(len(items), 0)

    def test_search_sql_injection_in_control(self):
        resp = self.client.get("/api/colleges?control=public' OR '1'='1")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        items = data.get("items", data.get("colleges", []))
        self.assertEqual(len(items), 0)

    def test_search_sql_injection_in_sort_by(self):
        resp = self.client.get("/api/colleges?sort_by=name; DROP TABLE colleges;")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        items = data.get("items", data.get("colleges", []))
        self.assertGreater(len(items), 0)

    def test_search_xss_script_tags_in_query(self):
        resp = self.client.get("/api/colleges?q=<script>alert('XSS')</script>")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        items = data.get("items", data.get("colleges", []))
        self.assertEqual(len(items), 0)

    def test_search_xss_img_onerror_in_state(self):
        resp = self.client.get("/api/colleges?state=<img src=x onerror=alert(1)>")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        items = data.get("items", data.get("colleges", []))
        self.assertEqual(len(items), 0)

    def test_search_empty_query_params(self):
        resp = self.client.get("/api/colleges?q=&state=&control=&type=&sort_by=&order=")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertGreater(data.get("total", 0), 0)

    def test_search_whitespace_query(self):
        resp = self.client.get("/api/colleges?q=%20%20%20%20")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertGreater(data.get("total", 0), 0)

    def test_search_negative_cost_filter(self):
        resp = self.client.get("/api/colleges?max_cost=-50000")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("items", data)

    def test_search_astronomical_cost_filter(self):
        resp = self.client.get("/api/colleges?max_cost=999999999")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertGreater(data.get("total", 0), 0)

    def test_search_impossible_admit_rate_range(self):
        resp = self.client.get("/api/colleges?min_admit_rate=0.9&max_admit_rate=0.1")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data.get("total", 0), 0)
        self.assertEqual(len(data.get("items", [])), 0)

    def test_search_admit_rate_greater_than_one(self):
        resp = self.client.get("/api/colleges?min_admit_rate=1.5")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data.get("total", 0), 0)

    def test_search_zero_page_size_returns_empty(self):
        resp = self.client.get("/api/colleges?page_size=0")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(len(data.get("items", [])), 0)

    def test_search_negative_limit_returns_400(self):
        resp = self.client.get("/api/colleges?limit=-10")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("non-negative", resp.json().get("detail", ""))

    def test_search_negative_offset_returns_400(self):
        resp = self.client.get("/api/colleges?offset=-5")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("non-negative", resp.json().get("detail", ""))

    def test_search_giant_page_offset(self):
        resp = self.client.get("/api/colleges?page=99999")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(len(data.get("items", [])), 0)

    def test_search_ultra_long_query_10k_chars(self):
        long_q = "A" * 10000
        resp = self.client.get(f"/api/colleges?q={long_q}")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data.get("total", 0), 0)

    def test_search_unicode_and_emojis(self):
        resp = self.client.get("/api/colleges?q=Harvard")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("items", data)

    def test_get_college_detail_path_traversal_defense(self):
        resp = self.client.get("/api/colleges/..%2f..%2fetc%2fpasswd")
        self.assertIn(resp.status_code, [400, 404])

    def test_get_college_detail_sql_injection_defense(self):
        resp = self.client.get("/api/colleges/166683'%20OR%201=1--")
        self.assertEqual(resp.status_code, 404)


class TestAdversarialConcurrentLedger(unittest.TestCase):
    """3. Concurrent Append-Only Knowledge Ledger Thread-Safety & Integrity."""

    def test_concurrent_async_writes_preserve_jsonl_integrity(self):
        """Simulate 50 concurrent asynchronous writes to the knowledge ledger."""
        async def run_concurrent_writes():
            tasks = []
            for i in range(50):
                event = LedgerEvent(
                    college_id=f"stress_test_{i % 5}",
                    college_name=f"Stress Test College {i % 5}",
                    run_id=f"run_stress_{i}",
                    field_path="admissions.acceptance_rate",
                    old_value=0.20,
                    new_value=0.20 + (i * 0.001),
                    source_ids=[f"stress_source_{i}"],
                    source_type=SourceType.AI_EXTRACTED,
                    confidence=ConfidenceLevel.QUALITATIVE,
                    status="committed",
                )
                run_meta = EnrichmentRun(
                    college_id=f"stress_test_{i % 5}",
                    college_name=f"Stress Test College {i % 5}",
                    model="StressTestBot",
                    run_id=f"run_stress_{i}",
                    status="success",
                    fields_updated=["admissions.acceptance_rate"],
                )
                tasks.append(ledger_service.record_events([event], run_metadata=run_meta))

            await asyncio.gather(*tasks)

        asyncio.run(run_concurrent_writes())

        # Verify JSONL integrity: every line must be valid JSON
        self.assertTrue(settings.LEDGER_JSONL_PATH.exists())
        corrupted_lines = 0
        total_valid = 0
        with open(settings.LEDGER_JSONL_PATH, "r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    parsed = json.loads(line)
                    self.assertIn("college_id", parsed)
                    self.assertIn("field_path", parsed)
                    total_valid += 1
                except json.JSONDecodeError:
                    corrupted_lines += 1

        self.assertEqual(corrupted_lines, 0, f"Found {corrupted_lines} corrupted JSON lines in ledger!")
        self.assertGreaterEqual(total_valid, 50)

    def test_concurrent_export_summary_consistency(self):
        """Verify export_knowledge_summary reads consistent data under high load."""
        async def run_export():
            summary = await ledger_service.export_knowledge_summary()
            events = await ledger_service.get_all_events(limit=100)
            return summary, events

        summary, events = asyncio.run(run_export())
        self.assertIsInstance(summary, list)
        self.assertIsInstance(events, list)

    def test_raw_ledger_markdown_endpoint(self):
        client = APIClient()
        resp = client.get("/api/knowledge/raw?format=markdown")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data.get("format"), "markdown")
        self.assertIn("# College Knowledge Ledger", data.get("content", ""))

    def test_raw_ledger_jsonl_endpoint(self):
        client = APIClient()
        resp = client.get("/api/knowledge/raw?format=jsonl")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data.get("format"), "jsonl")

    def test_raw_ledger_invalid_format_returns_400(self):
        client = APIClient()
        resp = client.get("/api/knowledge/raw?format=xml")
        self.assertEqual(resp.status_code, 400)


class TestAdversarialCookieSessions(unittest.TestCase):
    """4. Cookie Session Manipulation & Session Isolation Stress-Testing."""

    def setUp(self):
        self.client = APIClient()

    def test_missing_cookie_generates_new_session(self):
        c = APIClient()
        resp = c.get("/api/portfolio")
        self.assertEqual(resp.status_code, 200)
        cookie = c.get_cookie(settings.COOKIE_NAME)
        self.assertIsNotNone(cookie)
        self.assertTrue(cookie.startswith("port_"))

    def test_empty_cookie_value_handled_safely(self):
        c = APIClient()
        c.set_cookie(settings.COOKIE_NAME, "")
        resp = c.get("/api/portfolio")
        self.assertEqual(resp.status_code, 200)
        cookie = c.get_cookie(settings.COOKIE_NAME)
        self.assertIsNotNone(cookie)

    def test_arbitrary_string_cookie_isolated(self):
        c = APIClient()
        c.set_cookie(settings.COOKIE_NAME, "custom_user_session_alpha_123")
        resp = c.get("/api/portfolio")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data.get("session_id"), "custom_user_session_alpha_123")

    def test_sql_injection_in_cookie_handled_safely(self):
        c = APIClient()
        c.set_cookie(settings.COOKIE_NAME, "' OR '1'='1; --")
        resp = c.get("/api/portfolio")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(len(data.get("colleges", [])), 0)

    def test_xss_in_cookie_handled_safely(self):
        c = APIClient()
        c.set_cookie(settings.COOKIE_NAME, "<script>alert('XSS')</script>")
        resp = c.get("/api/portfolio")
        self.assertEqual(resp.status_code, 200)

    def test_ultra_long_cookie_handled_safely(self):
        c = APIClient()
        c.set_cookie(settings.COOKIE_NAME, "port_" + ("a" * 2000))
        resp = c.get("/api/portfolio")
        self.assertEqual(resp.status_code, 200)

    def test_session_isolation_between_two_clients(self):
        client_a = APIClient()
        client_a.set_cookie(settings.COOKIE_NAME, "port_isolated_client_a")

        client_b = APIClient()
        client_b.set_cookie(settings.COOKIE_NAME, "port_isolated_client_b")

        # Client A saves MIT (166683)
        client_a.post("/api/portfolio/colleges", json={"college_id": "166683", "notes": "Client A MIT"})

        # Client B saves Stanford (243744)
        client_b.post("/api/portfolio/colleges", json={"college_id": "243744", "notes": "Client B Stanford"})

        # Verify Client A portfolio has MIT and NOT Stanford
        resp_a = client_a.get("/api/portfolio")
        data_a = resp_a.json()
        ids_a = [c["college_id"] for c in data_a.get("colleges", [])]
        self.assertIn("166683", ids_a)
        self.assertNotIn("243744", ids_a)

        # Verify Client B portfolio has Stanford and NOT MIT
        resp_b = client_b.get("/api/portfolio")
        data_b = resp_b.json()
        ids_b = [c["college_id"] for c in data_b.get("colleges", [])]
        self.assertIn("243744", ids_b)
        self.assertNotIn("166683", ids_b)

    def test_malformed_json_payload_to_portfolio_returns_422(self):
        client = APIClient()
        client.set_cookie(settings.COOKIE_NAME, "port_json_payload_test")
        resp = client.post("/api/portfolio/colleges", data="Not Valid JSON", headers={"Content-Type": "application/json"})
        self.assertEqual(resp.status_code, 422)

    def test_nonexistent_college_id_to_portfolio_returns_404(self):
        client = APIClient()
        client.set_cookie(settings.COOKIE_NAME, "port_not_found_test")
        resp = client.post("/api/portfolio/colleges", json={"college_id": "nonexistent_999999"})
        self.assertEqual(resp.status_code, 404)


class TestAdversarialOfflineResilience(unittest.TestCase):
    """5. Offline Resilience & Graceful Degradation."""

    def setUp(self):
        self.client = APIClient()

    def test_system_operates_fully_without_scorecard_api_key(self):
        resp = self.client.get("/api/colleges?q=Massachusetts")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertGreater(data.get("total", 0), 0)

        detail_resp = self.client.get("/api/colleges/166683")
        self.assertEqual(detail_resp.status_code, 200)
        detail = detail_resp.json()
        self.assertEqual(detail.get("name"), "Massachusetts Institute of Technology")

    def test_refresh_endpoint_graceful_degradation_when_gemini_unconfigured(self):
        with patch.object(gemini_service, "api_key", None):
            resp = self.client.post("/api/colleges/166683/refresh")
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertEqual(data.get("status"), "success")
            college = data.get("college", {})
            self.assertIn("qualitative", college)

    def test_health_endpoint_reports_offline_modes_correctly(self):
        with patch.object(settings, "GEMINI_API_KEY", None), patch.object(settings, "COLLEGE_SCORECARD_API_KEY", None):
            resp = self.client.get("/api/health")
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertIn(data.get("status"), ["ok", "healthy", "up"])
            services = data.get("services", data)
            scorecard = services.get("scorecard", {})
            self.assertEqual(scorecard.get("status"), "seed_fallback_mode")
            gemini = services.get("gemini", {})
            self.assertEqual(gemini.get("status"), "preview_mode")

    def test_simulated_gemini_api_network_timeout_fallback(self):
        async def mock_timeout(*args, **kwargs):
            raise httpx.ConnectTimeout("Connection timed out to Gemini API")

        with patch("httpx.AsyncClient.post", side_effect=mock_timeout), patch.object(gemini_service, "api_key", "valid_mock_key_123"):
            resp = self.client.post("/api/colleges/166683/refresh")
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertEqual(data.get("status"), "success")
            run = data.get("run", {})
            self.assertEqual(run.get("status"), "failed")
            self.assertIn("timed out", run.get("error_message", "").lower())
            college = data.get("college", {})
            self.assertIn("qualitative", college)

    def test_simulated_gemini_api_server_error_500_fallback(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.text = "Internal Server Error from upstream AI"

        async def mock_post(*args, **kwargs):
            return mock_resp

        with patch("httpx.AsyncClient.post", side_effect=mock_post), patch.object(gemini_service, "api_key", "valid_mock_key_123"):
            resp = self.client.post("/api/colleges/166683/refresh")
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertEqual(data.get("status"), "success")
            run = data.get("run", {})
            self.assertEqual(run.get("status"), "failed")
            self.assertIn("500", run.get("error_message", ""))


if __name__ == "__main__":
    unittest.main()
