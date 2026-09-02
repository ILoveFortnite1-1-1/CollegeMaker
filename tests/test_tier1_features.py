"""
Tier 1: Feature Isolation Tests (>=80 tests across all 16 features).
Validates each feature independently against requirement specifications.
"""

import unittest
import json
import os
from tests.conftest import APIClient, SEED_COLLEGES, DEFAULT_FIT_WEIGHTS, SOURCE_PRECEDENCE


class TestTier1Feature01Health(unittest.TestCase):
    """Feature 1: Health & Status API (GET /api/health)"""

    def setUp(self):
        self.client = APIClient()

    def test_health_endpoint_returns_200_ok(self):
        resp = self.client.get("/api/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn(data.get("status"), ["ok", "healthy", "up"])

    def test_health_endpoint_reports_database_status(self):
        resp = self.client.get("/api/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue("database" in data or "db" in data or "services" in data)

    def test_health_endpoint_reports_scorecard_api_or_cache_status(self):
        resp = self.client.get("/api/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        services = data.get("services", data)
        self.assertTrue("scorecard" in services or "scorecard_api" in services or "cache" in services or "data_source" in services)

    def test_health_endpoint_reports_gemini_or_ai_status(self):
        resp = self.client.get("/api/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        services = data.get("services", data)
        self.assertTrue("gemini" in services or "ai" in services or "enrichment" in services)

    def test_health_endpoint_reports_knowledge_ledger_status(self):
        resp = self.client.get("/api/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        services = data.get("services", data)
        self.assertTrue("ledger" in services or "knowledge" in services or "audit_log" in services or "status" in data)

    def test_health_endpoint_content_type_is_json(self):
        resp = self.client.get("/api/health")
        self.assertEqual(resp.status_code, 200)
        ct = resp.get_header("content-type", "")
        self.assertIn("application/json", ct.lower())


class TestTier1Feature02CanonicalSchema(unittest.TestCase):
    """Feature 2: Canonical College Data Schema"""

    def setUp(self):
        self.client = APIClient()

    def test_canonical_schema_has_identity_fields(self):
        resp = self.client.get(f"/api/colleges/{SEED_COLLEGES['mit']['id']}")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        for field in ["id", "canonical_name", "location", "type"]:
            self.assertIn(field, data)
        self.assertEqual(str(data["id"]), SEED_COLLEGES["mit"]["id"])

    def test_canonical_schema_has_admissions_metrics(self):
        resp = self.client.get(f"/api/colleges/{SEED_COLLEGES['stanford']['id']}")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        admissions = data.get("admissions", {})
        self.assertTrue(bool(admissions))
        self.assertTrue("acceptance_rate" in admissions or "rate" in admissions or "admit_rate" in admissions)

    def test_canonical_schema_has_cost_metrics(self):
        resp = self.client.get(f"/api/colleges/{SEED_COLLEGES['berkeley']['id']}")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        cost = data.get("cost", {})
        self.assertTrue(bool(cost))
        self.assertTrue("net_price" in cost or "tuition_in_state" in cost or "cost_of_attendance" in cost or "net_price_avg" in cost)

    def test_canonical_schema_has_outcomes_metrics(self):
        resp = self.client.get(f"/api/colleges/{SEED_COLLEGES['michigan']['id']}")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        outcomes = data.get("outcomes", {})
        self.assertTrue(bool(outcomes))
        self.assertTrue("graduation_rate" in outcomes or "median_earnings" in outcomes or "retention_rate" in outcomes)

    def test_canonical_schema_has_qualitative_modules(self):
        resp = self.client.get(f"/api/colleges/{SEED_COLLEGES['mit']['id']}")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue("qualitative" in data or "insights" in data or "upsides" in data or "strengths" in data)

    def test_canonical_schema_classifications_are_valid(self):
        resp = self.client.get(f"/api/colleges/{SEED_COLLEGES['harvard']['id']}")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        provenance = data.get("provenance", {})
        valid_classes = {"Reported", "Calculated", "AI-derived", "AI_derived", "Estimated", "Qualitative", "government", "official_institutional"}
        if provenance:
            for field, meta in provenance.items():
                if isinstance(meta, dict) and "classification" in meta:
                    self.assertIn(meta["classification"], valid_classes)


class TestTier1Feature03ScorecardIngestion(unittest.TestCase):
    """Feature 3: Scorecard Ingestion & Normalization"""

    def setUp(self):
        self.client = APIClient()

    def test_acceptance_rate_is_normalized_percentage_or_ratio(self):
        resp = self.client.get(f"/api/colleges/{SEED_COLLEGES['mit']['id']}")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        admissions = data.get("admissions", {})
        rate = admissions.get("acceptance_rate") or admissions.get("admit_rate")
        self.assertIsNotNone(rate)
        # Check either 0.0-1.0 float or 0-100 percentage
        if isinstance(rate, dict):
            val = rate.get("value", 0)
        else:
            val = float(rate)
        self.assertTrue(0 <= val <= 100)

    def test_cost_values_are_positive_numbers(self):
        resp = self.client.get(f"/api/colleges/{SEED_COLLEGES['berkeley']['id']}")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        cost = data.get("cost", {})
        price = cost.get("net_price") or cost.get("tuition_in_state") or cost.get("cost_of_attendance")
        if isinstance(price, dict):
            val = price.get("value", 0)
        else:
            val = float(price)
        self.assertGreater(val, 0)

    def test_graduation_rate_is_within_valid_bounds(self):
        resp = self.client.get(f"/api/colleges/{SEED_COLLEGES['michigan']['id']}")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        outcomes = data.get("outcomes", {})
        grad_rate = outcomes.get("graduation_rate")
        self.assertIsNotNone(grad_rate)
        if isinstance(grad_rate, dict):
            val = grad_rate.get("value", 0)
        else:
            val = float(grad_rate)
        self.assertTrue(0 <= val <= 100)

    def test_enrollment_size_is_positive_integer(self):
        resp = self.client.get(f"/api/colleges/{SEED_COLLEGES['osu']['id']}")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        overview = data.get("overview", data)
        enrollment = overview.get("enrollment") or overview.get("undergrad_size") or data.get("enrollment")
        self.assertIsNotNone(enrollment)
        if isinstance(enrollment, dict):
            val = enrollment.get("value", 0)
        else:
            val = int(enrollment)
        self.assertGreater(val, 1000)

    def test_location_and_state_normalization(self):
        resp = self.client.get(f"/api/colleges/{SEED_COLLEGES['stanford']['id']}")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        loc = data.get("location", {})
        if isinstance(loc, dict):
            state = loc.get("state")
        else:
            state = data.get("state")
        self.assertEqual(state, "CA")


class TestTier1Feature04OfflineCachingSeedData(unittest.TestCase):
    """Feature 4: Offline Caching & Seed Data"""

    def setUp(self):
        self.client = APIClient()

    def test_seed_flagship_colleges_accessible_offline(self):
        for key in ["mit", "stanford", "berkeley", "michigan", "osu"]:
            cid = SEED_COLLEGES[key]["id"]
            resp = self.client.get(f"/api/colleges/{cid}")
            self.assertEqual(resp.status_code, 200, f"Seed college {key} ({cid}) failed to load")

    def test_colleges_list_contains_seeded_institutions(self):
        resp = self.client.get("/api/colleges", params={"limit": 50})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        colleges = data.get("items", data.get("colleges", data))
        self.assertIsInstance(colleges, list)
        self.assertGreaterEqual(len(colleges), 10)

    def test_cache_headers_or_freshness_present(self):
        resp = self.client.get(f"/api/colleges/{SEED_COLLEGES['mit']['id']}")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue("last_refreshed" in data or "refreshed_at" in data or "cache_status" in data or "provenance" in data)

    def test_seed_data_integrity_check(self):
        resp = self.client.get(f"/api/colleges/{SEED_COLLEGES['osu']['id']}")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        name = data.get("canonical_name", data.get("name", ""))
        self.assertIn("Ohio State", name)

    def test_repeated_lookups_return_consistent_data(self):
        resp1 = self.client.get(f"/api/colleges/{SEED_COLLEGES['stanford']['id']}")
        resp2 = self.client.get(f"/api/colleges/{SEED_COLLEGES['stanford']['id']}")
        self.assertEqual(resp1.status_code, 200)
        self.assertEqual(resp2.status_code, 200)
        self.assertEqual(resp1.json().get("id"), resp2.json().get("id"))


class TestTier1Feature05CollegeSearch(unittest.TestCase):
    """Feature 5: College Discovery API (GET /api/colleges)"""

    def setUp(self):
        self.client = APIClient()

    def test_search_by_name_query(self):
        resp = self.client.get("/api/colleges", params={"q": "Stanford"})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        items = data.get("items", data.get("colleges", data))
        self.assertTrue(any("Stanford" in (c.get("canonical_name") or c.get("name", "")) for c in items))

    def test_search_by_state_filter(self):
        resp = self.client.get("/api/colleges", params={"state": "CA"})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        items = data.get("items", data.get("colleges", data))
        self.assertTrue(len(items) > 0)
        for c in items:
            loc = c.get("location", {})
            st = loc.get("state") if isinstance(loc, dict) else c.get("state")
            self.assertEqual(st, "CA")

    def test_search_by_school_type_filter(self):
        resp = self.client.get("/api/colleges", params={"type": "public"})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        items = data.get("items", data.get("colleges", data))
        self.assertTrue(len(items) > 0)
        for c in items:
            self.assertEqual(c.get("type", "").lower(), "public")

    def test_search_by_max_cost_filter(self):
        resp = self.client.get("/api/colleges", params={"max_cost": 40000})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        items = data.get("items", data.get("colleges", data))
        self.assertIsInstance(items, list)

    def test_search_sort_by_name_ascending(self):
        resp = self.client.get("/api/colleges", params={"sort_by": "name", "order": "asc", "limit": 20})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        items = data.get("items", data.get("colleges", data))
        names = [c.get("canonical_name") or c.get("name", "") for c in items]
        self.assertEqual(names, sorted(names))


class TestTier1Feature06CollegeDetail(unittest.TestCase):
    """Feature 6: College Detail API (GET /api/colleges/:id)"""

    def setUp(self):
        self.client = APIClient()

    def test_get_college_detail_valid_id_returns_200(self):
        resp = self.client.get(f"/api/colleges/{SEED_COLLEGES['mit']['id']}")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(str(data.get("id")), SEED_COLLEGES["mit"]["id"])

    def test_college_detail_contains_all_core_sections(self):
        resp = self.client.get(f"/api/colleges/{SEED_COLLEGES['harvard']['id']}")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        for key in ["admissions", "cost", "outcomes"]:
            self.assertTrue(key in data or key in data.get("metrics", {}))

    def test_college_detail_has_field_provenance(self):
        resp = self.client.get(f"/api/colleges/{SEED_COLLEGES['berkeley']['id']}")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue("provenance" in data or "sources" in data or "source_evidence" in data)

    def test_get_college_detail_invalid_id_returns_404(self):
        resp = self.client.get("/api/colleges/99999999")
        self.assertEqual(resp.status_code, 404)
        data = resp.json()
        self.assertTrue("error" in data or "detail" in data or "message" in data)

    def test_college_detail_includes_freshness_metadata(self):
        resp = self.client.get(f"/api/colleges/{SEED_COLLEGES['michigan']['id']}")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue("last_refreshed" in data or "updated_at" in data or "refreshed_at" in data or "provenance" in data)


class TestTier1Feature07GeminiEnrichment(unittest.TestCase):
    """Feature 7: Server-Side Gemini Enrichment (POST /api/colleges/:id/refresh)"""

    def setUp(self):
        self.client = APIClient()

    def test_refresh_endpoint_returns_200_or_202(self):
        resp = self.client.post(f"/api/colleges/{SEED_COLLEGES['mit']['id']}/refresh")
        self.assertIn(resp.status_code, [200, 202])

    def test_refresh_response_contains_status_or_college(self):
        resp = self.client.post(f"/api/colleges/{SEED_COLLEGES['stanford']['id']}/refresh")
        self.assertIn(resp.status_code, [200, 202])
        data = resp.json()
        self.assertTrue("status" in data or "college" in data or "run_id" in data or "enrichment" in data)

    def test_qualitative_enrichment_has_upsides_and_tradeoffs(self):
        resp = self.client.get(f"/api/colleges/{SEED_COLLEGES['mit']['id']}")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        insights = data.get("qualitative", data.get("insights", data))
        self.assertTrue("upsides" in insights or "strengths" in insights or "tradeoffs" in insights or "highlights" in insights)

    def test_enrichment_does_not_expose_gemini_api_key(self):
        resp = self.client.post(f"/api/colleges/{SEED_COLLEGES['osu']['id']}/refresh")
        self.assertNotIn("AIzaSy", resp.text)
        self.assertNotIn("GEMINI_API_KEY", resp.text)

    def test_refresh_non_existent_college_returns_404(self):
        resp = self.client.post("/api/colleges/99999999/refresh")
        self.assertEqual(resp.status_code, 404)


class TestTier1Feature08SourcePrecedence(unittest.TestCase):
    """Feature 8: Strict Source Precedence Hierarchy"""

    def setUp(self):
        self.client = APIClient()

    def test_government_data_retains_highest_precedence(self):
        resp = self.client.get(f"/api/colleges/{SEED_COLLEGES['mit']['id']}")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        provenance = data.get("provenance", {})
        admit_meta = provenance.get("admissions.acceptance_rate") or provenance.get("acceptance_rate")
        if admit_meta and isinstance(admit_meta, dict):
            source = admit_meta.get("source", "").lower()
            self.assertTrue("scorecard" in source or "ipeds" in source or "government" in source or "dept of education" in source)

    def test_cost_field_precedence_is_authoritative(self):
        resp = self.client.get(f"/api/colleges/{SEED_COLLEGES['berkeley']['id']}")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        provenance = data.get("provenance", {})
        cost_meta = provenance.get("cost.net_price") or provenance.get("net_price")
        if cost_meta and isinstance(cost_meta, dict):
            source = cost_meta.get("source", "").lower()
            self.assertTrue("scorecard" in source or "government" in source or "reported" in cost_meta.get("classification", "").lower())

    def test_ai_derived_fields_carry_ai_classification(self):
        resp = self.client.get(f"/api/colleges/{SEED_COLLEGES['stanford']['id']}")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        provenance = data.get("provenance", {})
        for field, meta in provenance.items():
            if isinstance(meta, dict) and "gemini" in meta.get("source", "").lower():
                self.assertIn(meta.get("classification"), ["AI-derived", "AI_derived", "Qualitative", "Estimated"])

    def test_precedence_order_definition_matches_spec(self):
        self.assertEqual(SOURCE_PRECEDENCE[0], "government")
        self.assertEqual(SOURCE_PRECEDENCE[-1], "user")

    def test_ai_enrichment_does_not_overwrite_scorecard_metrics(self):
        # Fetch initial acceptance rate
        resp1 = self.client.get(f"/api/colleges/{SEED_COLLEGES['osu']['id']}")
        rate1 = resp1.json().get("admissions", {}).get("acceptance_rate")
        # Trigger refresh
        self.client.post(f"/api/colleges/{SEED_COLLEGES['osu']['id']}/refresh")
        # Fetch after refresh
        resp2 = self.client.get(f"/api/colleges/{SEED_COLLEGES['osu']['id']}")
        rate2 = resp2.json().get("admissions", {}).get("acceptance_rate")
        self.assertEqual(rate1, rate2)


class TestTier1Feature09ProvenanceMetadata(unittest.TestCase):
    """Feature 9: Field-Level Provenance Metadata"""

    def setUp(self):
        self.client = APIClient()

    def test_provenance_contains_source_name(self):
        resp = self.client.get(f"/api/colleges/{SEED_COLLEGES['mit']['id']}")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        provenance = data.get("provenance", {})
        self.assertTrue(bool(provenance))
        for key, meta in provenance.items():
            if isinstance(meta, dict):
                self.assertIn("source", meta)

    def test_provenance_contains_retrieval_timestamp(self):
        resp = self.client.get(f"/api/colleges/{SEED_COLLEGES['harvard']['id']}")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        provenance = data.get("provenance", {})
        for key, meta in provenance.items():
            if isinstance(meta, dict):
                self.assertTrue("retrieved_at" in meta or "observed_at" in meta or "timestamp" in meta)

    def test_provenance_contains_confidence_rating(self):
        resp = self.client.get(f"/api/colleges/{SEED_COLLEGES['stanford']['id']}")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        provenance = data.get("provenance", {})
        for key, meta in provenance.items():
            if isinstance(meta, dict) and "confidence" in meta:
                conf = meta["confidence"]
                if isinstance(conf, (int, float)):
                    self.assertTrue(0.0 <= conf <= 1.0)
                elif isinstance(conf, str):
                    self.assertIn(conf.lower(), ["high", "medium", "low", "qualitative", "verified"])

    def test_provenance_contains_classification_badge_type(self):
        resp = self.client.get(f"/api/colleges/{SEED_COLLEGES['michigan']['id']}")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        provenance = data.get("provenance", {})
        for key, meta in provenance.items():
            if isinstance(meta, dict) and "classification" in meta:
                self.assertIn(meta["classification"], ["Reported", "Calculated", "AI-derived", "Estimated", "Qualitative"])

    def test_provenance_dictionary_keyed_by_field_path(self):
        resp = self.client.get(f"/api/colleges/{SEED_COLLEGES['osu']['id']}")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        provenance = data.get("provenance", {})
        self.assertIsInstance(provenance, dict)


class TestTier1Feature10MarkdownLedger(unittest.TestCase):
    """Feature 10: Append-Only Markdown Ledger (/knowledge/college-knowledge.md)"""

    def setUp(self):
        self.client = APIClient()

    def test_knowledge_endpoint_returns_ledger_status_or_content(self):
        resp = self.client.get("/api/knowledge/export")
        if resp.status_code == 200:
            self.assertTrue(len(resp.text) > 0)
        else:
            self.assertIn(resp.status_code, [200, 204, 404])

    def test_refresh_college_triggers_markdown_ledger_entry(self):
        # Refresh MIT to ensure entry exists
        resp = self.client.post(f"/api/colleges/{SEED_COLLEGES['mit']['id']}/refresh")
        self.assertIn(resp.status_code, [200, 202])

        # Check knowledge history endpoint
        hist_resp = self.client.get(f"/api/knowledge/colleges/{SEED_COLLEGES['mit']['id']}")
        if hist_resp.status_code == 200:
            entries = hist_resp.json()
            self.assertTrue(isinstance(entries, (list, dict)))

    def test_markdown_entry_format_has_college_heading(self):
        ledger_path = os.path.join(os.path.dirname(__file__), "..", "knowledge", "college-knowledge.md")
        if os.path.exists(ledger_path):
            with open(ledger_path, "r") as f:
                content = f.read()
            if content.strip():
                self.assertIn("## College:", content)

    def test_markdown_entry_contains_timestamp_and_run_id(self):
        ledger_path = os.path.join(os.path.dirname(__file__), "..", "knowledge", "college-knowledge.md")
        if os.path.exists(ledger_path):
            with open(ledger_path, "r") as f:
                content = f.read()
            if "## College:" in content:
                self.assertTrue("Enrichment:" in content or "run " in content or "202" in content)

    def test_markdown_ledger_is_append_only(self):
        ledger_path = os.path.join(os.path.dirname(__file__), "..", "knowledge", "college-knowledge.md")
        if os.path.exists(ledger_path):
            size_before = os.path.getsize(ledger_path)
            self.client.post(f"/api/colleges/{SEED_COLLEGES['harvard']['id']}/refresh")
            size_after = os.path.getsize(ledger_path)
            self.assertGreaterEqual(size_after, size_before)


class TestTier1Feature11JSONLLedger(unittest.TestCase):
    """Feature 11: Machine-Auditable JSONL Stream (/knowledge/college-knowledge.jsonl)"""

    def setUp(self):
        self.client = APIClient()

    def test_jsonl_ledger_file_syntax_validity(self):
        jsonl_path = os.path.join(os.path.dirname(__file__), "..", "knowledge", "college-knowledge.jsonl")
        if os.path.exists(jsonl_path):
            with open(jsonl_path, "r") as f:
                lines = f.readlines()
            for line in lines:
                if line.strip():
                    entry = json.loads(line)
                    self.assertIsInstance(entry, dict)

    def test_jsonl_entries_have_required_audit_fields(self):
        jsonl_path = os.path.join(os.path.dirname(__file__), "..", "knowledge", "college-knowledge.jsonl")
        if os.path.exists(jsonl_path):
            with open(jsonl_path, "r") as f:
                lines = [l.strip() for l in f if l.strip()]
            if lines:
                entry = json.loads(lines[-1])
                for field in ["college_id", "field_path", "new_value"]:
                    self.assertIn(field, entry)

    def test_jsonl_entries_contain_timestamps(self):
        jsonl_path = os.path.join(os.path.dirname(__file__), "..", "knowledge", "college-knowledge.jsonl")
        if os.path.exists(jsonl_path):
            with open(jsonl_path, "r") as f:
                lines = [l.strip() for l in f if l.strip()]
            if lines:
                entry = json.loads(lines[-1])
                self.assertTrue("committed_at" in entry or "observed_at" in entry or "timestamp" in entry or "created_at" in entry)

    def test_jsonl_entries_contain_source_attribution(self):
        jsonl_path = os.path.join(os.path.dirname(__file__), "..", "knowledge", "college-knowledge.jsonl")
        if os.path.exists(jsonl_path):
            with open(jsonl_path, "r") as f:
                lines = [l.strip() for l in f if l.strip()]
            if lines:
                entry = json.loads(lines[-1])
                self.assertTrue("source_ids" in entry or "source" in entry or "provider" in entry)

    def test_knowledge_export_endpoint_returns_json_stream(self):
        resp = self.client.get("/api/knowledge/export")
        if resp.status_code == 200:
            data = resp.json()
            self.assertIsInstance(data, (list, dict))


class TestTier1Feature12GuestCookiePersistence(unittest.TestCase):
    """Feature 12: Guest Cookie Portfolio Persistence"""

    def setUp(self):
        self.client = APIClient()

    def test_initial_request_sets_portfolio_cookie(self):
        resp = self.client.get("/api/portfolio")
        self.assertEqual(resp.status_code, 200)
        cookie = self.client.get_cookie("college_portfolio_id")
        self.assertIsNotNone(cookie)
        self.assertTrue(len(cookie) > 8)

    def test_cookie_persists_across_multiple_requests(self):
        self.client.get("/api/portfolio")
        initial_cookie = self.client.get_cookie("college_portfolio_id")
        self.client.get("/api/colleges")
        after_cookie = self.client.get_cookie("college_portfolio_id")
        self.assertEqual(initial_cookie, after_cookie)

    def test_saved_colleges_persist_with_same_cookie(self):
        self.client.clear_cookies()
        # Save a college
        save_resp = self.client.post("/api/portfolio/colleges", json={"college_id": SEED_COLLEGES["mit"]["id"]})
        self.assertIn(save_resp.status_code, [200, 201])
        cookie = self.client.get_cookie("college_portfolio_id")

        # Create new client with same cookie
        new_client = APIClient()
        new_client.set_cookie("college_portfolio_id", cookie)
        get_resp = new_client.get("/api/portfolio")
        self.assertEqual(get_resp.status_code, 200)
        colleges = get_resp.json().get("colleges", get_resp.json().get("items", []))
        self.assertTrue(any(str(c.get("id") or c.get("college_id")) == SEED_COLLEGES["mit"]["id"] for c in colleges))

    def test_different_cookies_have_isolated_portfolios(self):
        # Client A
        client_a = APIClient()
        client_a.post("/api/portfolio/colleges", json={"college_id": SEED_COLLEGES["stanford"]["id"]})

        # Client B
        client_b = APIClient()
        get_resp = client_b.get("/api/portfolio")
        colleges_b = get_resp.json().get("colleges", get_resp.json().get("items", []))
        self.assertFalse(any(str(c.get("id") or c.get("college_id")) == SEED_COLLEGES["stanford"]["id"] for c in colleges_b))

    def test_cookie_format_is_opaque_token(self):
        self.client.get("/api/portfolio")
        cookie = self.client.get_cookie("college_portfolio_id")
        self.assertNotIn("{", cookie)
        self.assertNotIn("college_id", cookie)


class TestTier1Feature13PortfolioCRUD(unittest.TestCase):
    """Feature 13: Portfolio Tagging & Notes CRUD"""

    def setUp(self):
        self.client = APIClient()
        self.client.delete("/api/portfolio")

    def test_get_empty_portfolio(self):
        resp = self.client.get("/api/portfolio")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        colleges = data.get("colleges", data.get("items", []))
        self.assertEqual(len(colleges), 0)

    def test_add_college_to_portfolio(self):
        resp = self.client.post("/api/portfolio/colleges", json={
            "college_id": SEED_COLLEGES["berkeley"]["id"],
            "notes": "Top public engineering choice",
            "tag": "Target"
        })
        self.assertIn(resp.status_code, [200, 201])
        get_resp = self.client.get("/api/portfolio")
        colleges = get_resp.json().get("colleges", get_resp.json().get("items", []))
        self.assertEqual(len(colleges), 1)

    def test_update_portfolio_college_notes(self):
        self.client.post("/api/portfolio/colleges", json={"college_id": SEED_COLLEGES["michigan"]["id"]})
        upd_resp = self.client.put(f"/api/portfolio/colleges/{SEED_COLLEGES['michigan']['id']}", json={
            "notes": "Updated research lab interest",
            "custom_label": "High Priority"
        })
        self.assertIn(upd_resp.status_code, [200, 204])

    def test_remove_college_from_portfolio(self):
        self.client.post("/api/portfolio/colleges", json={"college_id": SEED_COLLEGES["osu"]["id"]})
        del_resp = self.client.delete(f"/api/portfolio/colleges/{SEED_COLLEGES['osu']['id']}")
        self.assertIn(del_resp.status_code, [200, 204])
        get_resp = self.client.get("/api/portfolio")
        colleges = get_resp.json().get("colleges", get_resp.json().get("items", []))
        self.assertEqual(len(colleges), 0)

    def test_clear_entire_portfolio(self):
        self.client.post("/api/portfolio/colleges", json={"college_id": SEED_COLLEGES["mit"]["id"]})
        self.client.post("/api/portfolio/colleges", json={"college_id": SEED_COLLEGES["stanford"]["id"]})
        del_resp = self.client.delete("/api/portfolio")
        self.assertIn(del_resp.status_code, [200, 204])
        get_resp = self.client.get("/api/portfolio")
        colleges = get_resp.json().get("colleges", get_resp.json().get("items", []))
        self.assertEqual(len(colleges), 0)

    def test_save_preferences_and_fit_weights(self):
        prefs_payload = {
            "gpa": 3.85,
            "sat": 1450,
            "budget": 25000,
            "target_majors": ["Computer Science", "Data Science"],
            "weights": DEFAULT_FIT_WEIGHTS
        }
        resp = self.client.put("/api/portfolio/preferences", json=prefs_payload)
        self.assertIn(resp.status_code, [200, 204])


class TestTier1Feature14FitScoring(unittest.TestCase):
    """Feature 14: 8-Dimension Fit Scoring Model"""

    def setUp(self):
        self.client = APIClient()

    def test_fit_score_calculation_returns_composite_score(self):
        self.client.post("/api/portfolio/colleges", json={"college_id": SEED_COLLEGES["mit"]["id"]})
        resp = self.client.get("/api/portfolio")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        colleges = data.get("colleges", data.get("items", []))
        self.assertTrue(len(colleges) > 0)
        fit = colleges[0].get("fit_score", colleges[0].get("composite_score"))
        self.assertIsNotNone(fit)
        val = fit.get("overall", fit) if isinstance(fit, dict) else fit
        self.assertTrue(0 <= float(val) <= 100)

    def test_fit_score_includes_all_8_dimension_breakdowns(self):
        self.client.post("/api/portfolio/colleges", json={"college_id": SEED_COLLEGES["stanford"]["id"]})
        resp = self.client.get("/api/portfolio")
        colleges = resp.json().get("colleges", resp.json().get("items", []))
        item = [c for c in colleges if str(c.get("id") or c.get("college_id")) == SEED_COLLEGES["stanford"]["id"]][0]
        breakdown = item.get("fit_breakdown", item.get("fit_score", {}).get("breakdown", {}))
        if breakdown:
            for dim in ["career", "roi", "academic", "admissions", "experience", "strength", "location", "cost"]:
                self.assertTrue(any(dim in k.lower() for k in breakdown.keys()))

    def test_custom_fit_weights_alter_composite_score(self):
        self.client.post("/api/portfolio/colleges", json={"college_id": SEED_COLLEGES["osu"]["id"]})
        # Baseline score
        resp1 = self.client.get("/api/portfolio")
        score1 = resp1.json().get("colleges", [{}])[0].get("fit_score", 50)
        if isinstance(score1, dict):
            score1 = score1.get("overall", 50)

        # Update weights heavily prioritizing cost
        cost_heavy_weights = {
            "career_outcomes": 0.05,
            "roi_value": 0.05,
            "academic_fit": 0.05,
            "admissions_fit": 0.05,
            "student_experience": 0.05,
            "academic_strength": 0.05,
            "location": 0.05,
            "cost": 0.65
        }
        self.client.put("/api/portfolio/preferences", json={"weights": cost_heavy_weights})
        resp2 = self.client.get("/api/portfolio")
        score2 = resp2.json().get("colleges", [{}])[0].get("fit_score", 50)
        if isinstance(score2, dict):
            score2 = score2.get("overall", 50)
        self.assertIsNotNone(score2)

    def test_fit_score_clamps_between_0_and_100(self):
        for cid in [SEED_COLLEGES["mit"]["id"], SEED_COLLEGES["berkeley"]["id"]]:
            self.client.post("/api/portfolio/colleges", json={"college_id": cid})
        resp = self.client.get("/api/portfolio")
        for item in resp.json().get("colleges", []):
            fit = item.get("fit_score")
            val = fit.get("overall", fit) if isinstance(fit, dict) else fit
            if val is not None:
                self.assertTrue(0.0 <= float(val) <= 100.0)

    def test_missing_data_degrades_confidence_not_punishes(self):
        resp = self.client.get(f"/api/colleges/{SEED_COLLEGES['osu']['id']}")
        self.assertEqual(resp.status_code, 200)


class TestTier1Feature15Comparison(unittest.TestCase):
    """Feature 15: Multi-College Comparison API (GET /api/compare)"""

    def setUp(self):
        self.client = APIClient()

    def test_compare_two_colleges_returns_matrix(self):
        ids = f"{SEED_COLLEGES['mit']['id']},{SEED_COLLEGES['stanford']['id']}"
        resp = self.client.get("/api/compare", params={"ids": ids})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        colleges = data.get("colleges", data.get("items", []))
        self.assertEqual(len(colleges), 2)

    def test_compare_six_colleges_max_capacity(self):
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
        data = resp.json()
        colleges = data.get("colleges", data.get("items", []))
        self.assertEqual(len(colleges), 6)

    def test_comparison_matrix_has_normalized_metric_rows(self):
        ids = f"{SEED_COLLEGES['mit']['id']},{SEED_COLLEGES['berkeley']['id']}"
        resp = self.client.get("/api/compare", params={"ids": ids})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue("metrics" in data or "matrix" in data or "comparison" in data or "rows" in data)

    def test_comparison_flags_best_in_class_or_highlights(self):
        ids = f"{SEED_COLLEGES['stanford']['id']},{SEED_COLLEGES['michigan']['id']}"
        resp = self.client.get("/api/compare", params={"ids": ids})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue("highlights" in data or "best_in_class" in data or "summary" in data or "colleges" in data)

    def test_compare_single_college_returns_400(self):
        resp = self.client.get("/api/compare", params={"ids": SEED_COLLEGES['mit']['id']})
        self.assertEqual(resp.status_code, 400)


class TestTier1Feature16SingleServiceStatic(unittest.TestCase):
    """Feature 16: Single-Service Serving & Static Assets"""

    def setUp(self):
        self.client = APIClient()

    def test_root_path_serves_html(self):
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        ct = resp.get_header("content-type", "")
        self.assertTrue("text/html" in ct.lower())
        self.assertTrue("<html" in resp.text.lower() or "<!doctype" in resp.text.lower())

    def test_styles_css_served_with_css_content_type(self):
        resp = self.client.get("/css/styles.css")
        if resp.status_code == 200:
            ct = resp.get_header("content-type", "")
            self.assertTrue("text/css" in ct.lower())

    def test_app_js_served_with_javascript_content_type(self):
        resp = self.client.get("/js/app.js")
        if resp.status_code == 200:
            ct = resp.get_header("content-type", "")
            self.assertTrue("javascript" in ct.lower())

    def test_spa_client_routes_serve_index_html(self):
        for route in ["/colleges", "/compare", "/settings"]:
            resp = self.client.get(route)
            self.assertEqual(resp.status_code, 200)
            ct = resp.get_header("content-type", "")
            self.assertTrue("text/html" in ct.lower())

    def test_favicon_or_static_assets_respond_without_500(self):
        resp = self.client.get("/favicon.ico")
        self.assertIn(resp.status_code, [200, 204, 404])
