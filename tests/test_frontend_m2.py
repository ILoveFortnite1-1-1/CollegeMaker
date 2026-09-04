"""Frontend Milestone 2 Verification Test Suite.

Verifies static file mounting, HTML navigation structure, SPA route registration,
API client methods, and component/page exports for features R1 through R7.
"""
import re
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from server.main import app

CLIENT_DIR = Path("client")
JS_DIR = CLIENT_DIR / "js"
PAGES_DIR = JS_DIR / "pages"
COMPONENTS_DIR = JS_DIR / "components"


@pytest.fixture
def client():
    return TestClient(app)


class TestFrontendStaticFiles:
    """Verify that all newly created frontend files are properly served by FastAPI."""

    def test_root_index_html(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        assert "text/html" in resp.headers.get("content-type", "")
        assert "College Portfolio" in resp.text

    def test_static_css_served(self, client):
        resp = client.get("/css/styles.css")
        assert resp.status_code == 200
        assert "tag-safety" in resp.text
        assert "chances-gauge-widget" in resp.text
        assert "outcomes-deep-dive" in resp.text
        assert "requirements-matrix-widget" in resp.text

    def test_new_components_served(self, client):
        components = [
            "/js/components/chances-gauge.js",
            "/js/components/outcomes-chart.js",
            "/js/components/requirements-matrix.js",
        ]
        for url in components:
            resp = client.get(url)
            assert resp.status_code == 200, f"Failed to fetch {url}"
            assert "javascript" in resp.headers.get("content-type", "")

    def test_new_pages_served(self, client):
        pages = [
            "/js/pages/aid-comparison.js",
            "/js/pages/calendar.js",
            "/js/pages/essays.js",
            "/js/pages/what-if.js",
        ]
        for url in pages:
            resp = client.get(url)
            assert resp.status_code == 200, f"Failed to fetch {url}"
            assert "javascript" in resp.headers.get("content-type", "")


class TestNavigationStructure:
    """Verify navigation links in client/index.html for desktop and mobile menus."""

    def test_desktop_nav_links(self):
        index_path = CLIENT_DIR / "index.html"
        assert index_path.exists()
        content = index_path.read_text(encoding="utf-8")

        # Must contain all 7 features' routes in navigation
        assert 'href="#/aid"' in content
        assert 'href="#/calendar"' in content
        assert 'href="#/essays"' in content
        assert 'href="#/what-if"' in content
        assert 'href="#/tracker"' in content
        assert 'href="#/compare"' in content
        assert 'href="#/colleges"' in content

        # Check data-route attributes
        assert 'data-route="aid"' in content
        assert 'data-route="calendar"' in content
        assert 'data-route="essays"' in content
        assert 'data-route="what-if"' in content

    def test_mobile_nav_links(self):
        index_path = CLIENT_DIR / "index.html"
        content = index_path.read_text(encoding="utf-8")

        # Mobile drawer contains links
        mobile_section = re.search(r'<nav class="mobile-nav-links">(.*?)</nav>', content, re.DOTALL)
        assert mobile_section is not None
        mobile_html = mobile_section.group(1)

        assert 'href="#/aid"' in mobile_html
        assert 'href="#/calendar"' in mobile_html
        assert 'href="#/essays"' in mobile_html
        assert 'href="#/what-if"' in mobile_html
        assert 'href="#/tracker"' in mobile_html


class TestAppRoutingRegistration:
    """Verify SPA hash routes registered in client/js/app.js."""

    def test_app_imports_and_routes(self):
        app_path = JS_DIR / "app.js"
        assert app_path.exists()
        content = app_path.read_text(encoding="utf-8")

        # Imports
        assert "AidComparisonPage" in content
        assert "CalendarPage" in content
        assert "EssaysPage" in content
        assert "WhatIfPage" in content

        # Routes dictionary
        assert "'aid': AidComparisonPage" in content
        assert "'calendar': CalendarPage" in content
        assert "'essays': EssaysPage" in content
        assert "'what-if': WhatIfPage" in content


class TestApiClientMethods:
    """Verify API methods in client/js/api.js."""

    def test_api_methods_exist(self):
        api_path = JS_DIR / "api.js"
        assert api_path.exists()
        content = api_path.read_text(encoding="utf-8")

        # R1 Aid
        assert "async getAidComparison(" in content
        assert "async saveAidOffer(" in content
        assert "async deleteAidOffer(" in content

        # R2 Calendar
        assert "async getCalendar(" in content

        # R3 Essays
        assert "async getEssays(" in content
        assert "async createEssay(" in content
        assert "async updateEssay(" in content
        assert "async deleteEssay(" in content

        # R4 Chances
        assert "async getCollegeChances(" in content
        assert "async getPortfolioChances(" in content

        # R5 What-If
        assert "async simulateScenario(" in content

        # R6 Alumni Outcomes
        assert "async getCollegeFieldOfStudy(" in content

        # R7 Requirements Checklist
        assert "async getCollegeChecklist(" in content
        assert "async addChecklistItem(" in content
        assert "async updateChecklistItem(" in content
        assert "async deleteChecklistItem(" in content
        assert "async getRequirementsMatrix(" in content


class TestComponentImplementations:
    """Verify component function exports and logic."""

    def test_chances_gauge_component(self):
        path = COMPONENTS_DIR / "chances-gauge.js"
        assert path.exists()
        content = path.read_text(encoding="utf-8")

        assert "export function renderChancesGauge(" in content
        assert "Reach" in content or "reach" in content
        assert "Target" in content or "target" in content
        assert "Likely" in content or "likely" in content
        assert "Safety" in content or "safety" in content
        assert "student-score-pin" in content

    def test_outcomes_chart_component(self):
        path = COMPONENTS_DIR / "outcomes-chart.js"
        assert path.exists()
        content = path.read_text(encoding="utf-8")

        assert "export function renderOutcomesChart(" in content
        assert "export function renderOutcomesTableRows(" in content
        assert "export function initOutcomesInteractions(" in content
        assert "outcomes-bar-chart" in content
        assert "outcomes-table" in content
        assert "isPreferred" in content or "is_preferred" in content

    def test_requirements_matrix_component(self):
        path = COMPONENTS_DIR / "requirements-matrix.js"
        assert path.exists()
        content = path.read_text(encoding="utf-8")

        assert "export function renderRequirementsMatrix(" in content
        assert "export function bindRequirementsMatrixEvents(" in content
        assert "matrix-table" in content
        assert "summary-chip" in content
        assert "matrix-cell-btn" in content


class TestPageImplementations:
    """Verify page modules export async render(container, state) and handle empty/full states."""

    def test_aid_comparison_page(self):
        path = PAGES_DIR / "aid-comparison.js"
        assert path.exists()
        content = path.read_text(encoding="utf-8")

        assert "export const AidComparisonPage = {" in content
        assert "async render(container, state" in content
        assert "bindEvents(" in content
        assert "aid-matrix-table" in content
        assert "aid-offer-modal" in content
        assert "four_year_total_cost" in content
        assert "estimated_monthly_payment" in content

    def test_calendar_page(self):
        path = PAGES_DIR / "calendar.js"
        assert path.exists()
        content = path.read_text(encoding="utf-8")

        assert "export const CalendarPage = {" in content
        assert "async render(container, state" in content
        assert "renderMonthGrid(" in content
        assert "calendar-table" in content
        assert "upcoming-deadlines-list" in content
        assert "btn-prev-month" in content
        assert "btn-next-month" in content

    def test_essays_page(self):
        path = PAGES_DIR / "essays.js"
        assert path.exists()
        content = path.read_text(encoding="utf-8")

        assert "export const EssaysPage = {" in content
        assert "async render(container, state" in content
        assert "renderEssayCard(" in content
        assert "essay-modal" in content
        assert "reuse-badge" in content
        assert "filter-status-btn" in content

    def test_what_if_page(self):
        path = PAGES_DIR / "what-if.js"
        assert path.exists()
        content = path.read_text(encoding="utf-8")

        assert "export const WhatIfPage = {" in content
        assert "async render(container, state" in content
        assert "renderComparisonView(" in content
        assert "renderFitRing" in content
        assert "sim-college-select" in content
        assert "sim-range-aid" in content
        assert "sim-range-budget" in content


class TestExistingPageEnhancements:
    """Verify that existing pages have been properly upgraded with R4, R6, R7."""

    def test_profile_page_enhancements(self):
        path = PAGES_DIR / "profile.js"
        content = path.read_text(encoding="utf-8")

        assert "renderChancesGauge" in content
        assert "renderOutcomesChart" in content
        assert "initOutcomesInteractions" in content
        assert "tab-admissions" in content
        assert "tab-academics" in content
        assert "outcomes-deep-dive-card" in content

    def test_dashboard_page_enhancements(self):
        path = PAGES_DIR / "dashboard.js"
        content = path.read_text(encoding="utf-8")

        assert "getPortfolioChances" in content
        assert "Admissions Chances" in content
        assert "Safety" in content
        assert "Reach" in content
        assert "Target" in content
        assert "Likely" in content

    def test_tracker_page_enhancements(self):
        path = PAGES_DIR / "tracker.js"
        content = path.read_text(encoding="utf-8")

        assert "renderRequirementsMatrix" in content
        assert "bindRequirementsMatrixEvents" in content
        assert "requirements-matrix-section" in content
