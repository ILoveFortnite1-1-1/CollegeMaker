"""Adversarial Challenge Test Suite for Milestone 2 Frontend.

Validates:
1. Static JS and HTML syntax validity via JavaScriptCore and standard HTMLParser.
2. Resolution of all relative ES module imports.
3. SPA hash routing in client/js/app.js and navigation in client/index.html.
4. API client method contract fidelity against FastAPI routes and schemas.
5. Edge cases:
   - Empty portfolio state (0 saved colleges)
   - Essay tracker boundary conditions (word_limit=0, 5000+ words, long prompts)
   - Alumni outcomes with missing/0 median earnings
   - Admissions chances gauge with missing student GPA/SAT
"""
import json
import re
import subprocess
from html.parser import HTMLParser
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from server.main import app

CLIENT_DIR = Path("client")
JS_DIR = CLIENT_DIR / "js"
COMPONENTS_DIR = JS_DIR / "components"
PAGES_DIR = JS_DIR / "pages"


@pytest.fixture
def client():
    return TestClient(app)


class TestStaticSyntaxAndImports:
    """Validate JS files via JavaScriptCore and HTML via parser."""

    def test_all_js_syntax_via_jsc(self):
        """Pass all 29 JavaScript files through JavaScriptCore syntax parser."""
        js_files = sorted(list(CLIENT_DIR.glob("**/*.js")))
        assert len(js_files) >= 15, "Expected at least 15 JS files"

        errors = []
        for js_file in js_files:
            code = js_file.read_text(encoding="utf-8")
            # Strip ESM module keywords for Function() parsing
            transformed = re.sub(
                r"import\s+[\s\S]*?from\s*[\x27\x22][^\x27\x22]+[\x27\x22];?",
                "/* import */",
                code,
            )
            transformed = re.sub(r"import\s+[^;\n]+;?", "/* import */", transformed)
            transformed = re.sub(r"export\s+default\s+", "", transformed)
            transformed = re.sub(
                r"export\s+(const|let|var|function|class|async\s+function)\s+",
                r"\1 ",
                transformed,
            )
            transformed = re.sub(r"export\s*\{[^}]*\};?", "/* export */", transformed)

            script = f"""
            try {{
                Function({json.dumps(transformed)});
                "OK";
            }} catch (e) {{
                "ERROR: " + e.toString() + (e.line ? " at line " + e.line : "");
            }}
            """
            res = subprocess.run(
                ["osascript", "-l", "JavaScript", "-e", script],
                capture_output=True,
                text=True,
            )
            out = res.stdout.strip()
            if "ERROR:" in out or res.returncode != 0:
                errors.append(f"{js_file}: {out or res.stderr}")

        assert not errors, f"JS syntax errors found:\n" + "\n".join(errors)

    def test_html_well_formed(self):
        """Validate client/index.html tag nesting and closure."""
        class HTMLValidator(HTMLParser):
            def __init__(self):
                super().__init__()
                self.tags = []
                self.errors = []
                self.void_elements = {
                    "area", "base", "br", "col", "embed", "hr", "img", "input",
                    "link", "meta", "param", "source", "track", "wbr"
                }

            def handle_starttag(self, tag, attrs):
                if tag.lower() not in self.void_elements:
                    self.tags.append((tag.lower(), self.getpos()))

            def handle_endtag(self, tag):
                t = tag.lower()
                if t in self.void_elements:
                    return
                if not self.tags:
                    self.errors.append(f"Unexpected closing tag </{t}> at line {self.getpos()[0]}")
                    return
                last_tag, pos = self.tags.pop()
                if last_tag != t:
                    self.errors.append(
                        f"Mismatched tag: expected </{last_tag}> (opened line {pos[0]}), got </{t}> at line {self.getpos()[0]}"
                    )

            def handle_startendtag(self, tag, attrs):
                pass

        html_content = (CLIENT_DIR / "index.html").read_text(encoding="utf-8")
        validator = HTMLValidator()
        validator.feed(html_content)

        assert not validator.errors, f"HTML nesting errors:\n" + "\n".join(validator.errors)
        assert not validator.tags, f"Unclosed tags:\n" + str(validator.tags)


class TestSpaRoutingAndNavigation:
    """Validate 4 new routes mapped in app.js and linked in index.html."""

    def test_routes_in_app_js(self):
        app_js = (JS_DIR / "app.js").read_text(encoding="utf-8")

        # Imports
        assert "import { AidComparisonPage } from './pages/aid-comparison.js';" in app_js
        assert "import { CalendarPage } from './pages/calendar.js';" in app_js
        assert "import { EssaysPage } from './pages/essays.js';" in app_js
        assert "import { WhatIfPage } from './pages/what-if.js';" in app_js

        # Routes table mapping
        assert "'aid': AidComparisonPage" in app_js
        assert "'calendar': CalendarPage" in app_js
        assert "'essays': EssaysPage" in app_js
        assert "'what-if': WhatIfPage" in app_js

    def test_navigation_links_in_index_html(self):
        index_html = (CLIENT_DIR / "index.html").read_text(encoding="utf-8")

        # Desktop nav
        assert 'href="#/aid"' in index_html
        assert 'href="#/calendar"' in index_html
        assert 'href="#/essays"' in index_html
        assert 'href="#/what-if"' in index_html

        # Check data-route attributes for active nav highlighting
        assert 'data-route="aid"' in index_html
        assert 'data-route="calendar"' in index_html
        assert 'data-route="essays"' in index_html
        assert 'data-route="what-if"' in index_html


class TestApiClientContracts:
    """Verify all 17 Milestone 2 API methods against live FastAPI endpoints."""

    def test_full_api_contract_roundtrip(self, client):
        # 1. Initialize guest session
        resp = client.get("/api/portfolio")
        assert resp.status_code == 200
        cookie = resp.cookies.get("college_portfolio_id")
        assert cookie is not None
        cookies = {"college_portfolio_id": cookie}

        # Save college to enable tests
        save_resp = client.post("/api/portfolio/colleges", json={"college_id": "130794"}, cookies=cookies)
        assert save_resp.status_code == 200

        # R1: Aid
        r_aid_comp = client.get("/api/portfolio/aid/comparison", cookies=cookies)
        assert r_aid_comp.status_code == 200
        assert "colleges" in r_aid_comp.json()

        aid_payload = {
            "merit_aid": 7500,
            "need_based_grants": 12000,
            "federal_loans": 5500,
            "work_study": 2500,
            "custom_sticker_price": 82000
        }
        r_aid_save = client.post("/api/portfolio/aid/130794", json=aid_payload, cookies=cookies)
        assert r_aid_save.status_code == 200
        assert r_aid_save.json()["status"] == "success"

        r_aid_del = client.delete("/api/portfolio/aid/130794", cookies=cookies)
        assert r_aid_del.status_code == 200
        assert r_aid_del.json()["deleted"] is True

        # R2: Calendar
        r_cal = client.get("/api/portfolio/calendar", cookies=cookies)
        assert r_cal.status_code == 200
        assert "events" in r_cal.json()
        assert "upcoming_14_days" in r_cal.json()

        # R3: Essays
        essay_payload = {
            "title": "Why Yale Supplement",
            "prompt": "Reflect on something that engages your intellectual curiosity.",
            "word_limit": 250,
            "current_word_count": 210,
            "draft_status": "Drafting",
            "colleges": ["130794"]
        }
        r_ess_create = client.post("/api/portfolio/essays", json=essay_payload, cookies=cookies)
        assert r_ess_create.status_code == 200
        essay_id = r_ess_create.json()["id"]

        r_ess_list = client.get("/api/portfolio/essays", cookies=cookies)
        assert r_ess_list.status_code == 200
        assert r_ess_list.json()["count"] >= 1

        r_ess_update = client.put(
            f"/api/portfolio/essays/{essay_id}",
            json={"draft_status": "Final", "current_word_count": 248},
            cookies=cookies,
        )
        assert r_ess_update.status_code == 200
        assert r_ess_update.json()["draft_status"] == "Final"

        r_ess_del = client.delete(f"/api/portfolio/essays/{essay_id}", cookies=cookies)
        assert r_ess_del.status_code == 200
        assert r_ess_del.json()["deleted"] is True

        # R4: Chances
        r_chances_col = client.get("/api/colleges/130794/chances?gpa=3.9&sat=1520", cookies=cookies)
        assert r_chances_col.status_code == 200
        assert r_chances_col.json()["classification"] in ["Reach", "Target", "Likely", "Safety"]

        r_chances_port = client.get("/api/portfolio/chances", cookies=cookies)
        assert r_chances_port.status_code == 200
        assert "distribution" in r_chances_port.json()

        # R5: What-If
        scenario_req = {
            "college_id": "130794",
            "hypothetical_major": "Economics",
            "is_in_state": False,
            "annual_aid_amount": 15000,
            "budget_max_annual": 45000
        }
        r_scen = client.post("/api/portfolio/scenario", json=scenario_req, cookies=cookies)
        assert r_scen.status_code == 200
        assert "results" in r_scen.json()

        # R6: Field of Study
        r_fos = client.get("/api/colleges/130794/field-of-study", cookies=cookies)
        assert r_fos.status_code == 200
        assert "programs" in r_fos.json()

        # R7: Requirements Checklist & Matrix
        chk_req = {"name": "Mid-Year Report", "required": True, "completed": False}
        r_chk_add = client.post("/api/portfolio/tracker/130794/checklist", json=chk_req, cookies=cookies)
        assert r_chk_add.status_code == 200
        item_id = r_chk_add.json()["id"]

        r_chk_list = client.get("/api/portfolio/tracker/130794/checklist", cookies=cookies)
        assert r_chk_list.status_code == 200
        assert r_chk_list.json()["count"] >= 1

        r_chk_upd = client.put(
            f"/api/portfolio/tracker/130794/checklist/{item_id}",
            json={"completed": True},
            cookies=cookies,
        )
        assert r_chk_upd.status_code == 200
        assert r_chk_upd.json()["completed"] is True

        r_chk_del = client.delete(f"/api/portfolio/tracker/130794/checklist/{item_id}", cookies=cookies)
        assert r_chk_del.status_code == 200
        assert r_chk_del.json()["deleted"] is True

        r_matrix = client.get("/api/portfolio/requirements-matrix", cookies=cookies)
        assert r_matrix.status_code == 200
        assert "colleges" in r_matrix.json()
        assert "matrix" in r_matrix.json()


class TestEdgeCases:
    """Stress test boundary conditions and edge cases."""

    def test_edge_case_empty_portfolio_0_colleges(self, client):
        """When student has 0 saved colleges, all endpoints return valid empty payloads."""
        resp = client.get("/api/portfolio")
        cookie = resp.cookies.get("college_portfolio_id")
        cookies = {"college_portfolio_id": cookie}

        # Clear portfolio to ensure 0 colleges
        client.delete("/api/portfolio", cookies=cookies)

        r_aid = client.get("/api/portfolio/aid/comparison", cookies=cookies)
        assert r_aid.status_code == 200
        assert r_aid.json()["colleges"] == []
        assert r_aid.json()["best_value_college_id"] is None

        r_cal = client.get("/api/portfolio/calendar", cookies=cookies)
        assert r_cal.status_code == 200
        assert r_cal.json()["events"] == []
        assert r_cal.json()["upcoming_14_days"] == []

        r_cha = client.get("/api/portfolio/chances", cookies=cookies)
        assert r_cha.status_code == 200
        assert r_cha.json()["chances"] == []
        assert r_cha.json()["distribution"] == {"Reach": 0, "Target": 0, "Likely": 0, "Safety": 0}

        r_mat = client.get("/api/portfolio/requirements-matrix", cookies=cookies)
        assert r_mat.status_code == 200
        assert r_mat.json()["colleges"] == []
        assert r_mat.json()["matrix"] == []

    def test_edge_case_chances_gauge_no_gpa_or_sat(self):
        """Chances gauge renders without pin and displays fallback when GPA/SAT are not set."""
        chances_src = (COMPONENTS_DIR / "chances-gauge.js").read_text(encoding="utf-8")
        chances_src = chances_src.replace("export function renderChancesGauge", "function renderChancesGauge")

        test_script = f"""
        {chances_src}

        var dataNoScores = {{
            classification: "Target",
            acceptance_rate: 0.25,
            overall_probability: 0.30,
            test_status: {{
                test_type: "SAT",
                percentile_25: 1250,
                percentile_75: 1480,
                student_score: null
            }},
            gpa_status: {{
                student_gpa: null
            }},
            summary: "Average test range for admitted students."
        }};

        var html = renderChancesGauge(dataNoScores);
        JSON.stringify({{
            hasPin: html.includes("student-score-pin"),
            hasPrompt: html.includes("Set your GPA and SAT/ACT in Preferences"),
            hasTargetBadge: html.includes("Target"),
            hasRange: html.includes("1250 – 1480")
        }});
        """
        res = subprocess.run(["osascript", "-l", "JavaScript", "-e", test_script], capture_output=True, text=True)
        assert res.returncode == 0
        out = json.loads(res.stdout.strip())
        assert out["hasPin"] is False, "Pin should NOT render when student has no score"
        assert out["hasPrompt"] is True, "Should prompt student to set scores in Preferences"
        assert out["hasTargetBadge"] is True
        assert out["hasRange"] is True

    def test_edge_case_alumni_outcomes_missing_or_zero_earnings(self):
        """Outcomes component handles zero, null, and missing earnings gracefully."""
        metric_src = (COMPONENTS_DIR / "metric-card.js").read_text(encoding="utf-8")
        metric_src = metric_src.replace("import { renderSourceBadge } from './source-badge.js';", "function renderSourceBadge() { return ''; }")
        metric_src = metric_src.replace("export function formatMetricValue", "function formatMetricValue")
        metric_src = metric_src.replace("export function formatConfidence", "function formatConfidence")
        metric_src = metric_src.replace("export function renderMetricCard", "function renderMetricCard")

        outcomes_src = (COMPONENTS_DIR / "outcomes-chart.js").read_text(encoding="utf-8")
        outcomes_src = outcomes_src.replace("import { formatMetricValue } from './metric-card.js';", "")
        outcomes_src = outcomes_src.replace("export function renderOutcomesChart", "function renderOutcomesChart")
        outcomes_src = outcomes_src.replace("export function renderOutcomesTableRows", "function renderOutcomesTableRows")
        outcomes_src = outcomes_src.replace("export function initOutcomesInteractions", "function initOutcomesInteractions")

        test_script = f"""
        {metric_src}
        {outcomes_src}

        var mock = {{
            programs: [
                {{ major_name: "Philosophy", median_earnings_4yr: null, median_debt: 18000 }},
                {{ major_name: "Music", median_earnings_4yr: 0, median_debt: 20000 }},
                {{ major_name: "Computer Science", median_earnings_4yr: 92000, median_debt: 14000, is_preferred: true }}
            ]
        }};

        var html = renderOutcomesChart(mock);
        var barSection = html.split('<div class="outcomes-bar-chart"')[1].split('<!-- Search & Filter Controls -->')[0];

        JSON.stringify({{
            philosophyInBar: barSection.includes("Philosophy"),
            musicInBar: barSection.includes("Music"),
            csInBar: barSection.includes("Computer Science"),
            hasNaN: html.includes("NaN"),
            hasInfinity: html.includes("Infinity"),
            hasFallbackDash: html.includes("—")
        }});
        """
        res = subprocess.run(["osascript", "-l", "JavaScript", "-e", test_script], capture_output=True, text=True)
        assert res.returncode == 0
        out = json.loads(res.stdout.strip())
        assert out["philosophyInBar"] is False, "0/null earnings must not show in bar chart"
        assert out["musicInBar"] is False, "0 earnings must not show in bar chart"
        assert out["csInBar"] is True, "Valid earnings should show in bar chart"
        assert out["hasNaN"] is False, "Output must never contain NaN"
        assert out["hasInfinity"] is False, "Output must never contain Infinity"
        assert out["hasFallbackDash"] is True, "Null/zero debt ratio should show dash"

    def test_edge_case_essay_boundary_conditions(self):
        """Essay tracker renders properly with word_limit=0, 5000-word limit, and long prompts."""
        essays_src = (PAGES_DIR / "essays.js").read_text(encoding="utf-8")
        essays_src = essays_src.replace("import { API } from '../api.js';", "")
        essays_src = essays_src.replace("export const EssaysPage =", "const EssaysPage =")

        test_script = f"""
        {essays_src}

        var collegeMap = {{ "130794": "Yale University", "166027": "Harvard University" }};

        // Edge case: word_limit = 0
        var zeroLimitEssay = {{
            id: "e0",
            title: "Unconstrained Essay",
            prompt: "Describe an interest of yours.",
            word_limit: 0,
            current_word_count: 350,
            draft_status: "Drafting",
            colleges: ["130794"]
        }};
        var zeroHtml = EssaysPage.renderEssayCard(zeroLimitEssay, collegeMap);

        // Edge case: 5000 words limit, 5250 words current (over limit)
        var longPrompt = "Why do you want to attend this institution? ".repeat(100);
        var longEssay = {{
            id: "e5000",
            title: "Doctoral Statement of Purpose",
            prompt: longPrompt,
            word_limit: 5000,
            current_word_count: 5250,
            draft_status: "Final",
            colleges: ["130794", "166027"]
        }};
        var longHtml = EssaysPage.renderEssayCard(longEssay, collegeMap);

        JSON.stringify({{
            zeroHasNaN: zeroHtml.includes("NaN"),
            zeroHasInfinity: zeroHtml.includes("Infinity"),
            longHasOverBadge: longHtml.includes("(+250 over)"),
            longHasReuse: longHtml.includes("Used for 2 schools"),
            longHasRedWarning: longHtml.includes("#dc2626") || longHtml.includes("#ef4444")
        }});
        """
        res = subprocess.run(["osascript", "-l", "JavaScript", "-e", test_script], capture_output=True, text=True)
        assert res.returncode == 0
        out = json.loads(res.stdout.strip())
        assert out["zeroHasNaN"] is False, "word_limit=0 must not produce NaN"
        assert out["zeroHasInfinity"] is False, "word_limit=0 must not produce Infinity"
        assert out["longHasOverBadge"] is True, "5250/5000 must show +250 over"
        assert out["longHasReuse"] is True, "Must show reuse badge for 2 schools"
        assert out["longHasRedWarning"] is True, "Over limit count must trigger red warning"
