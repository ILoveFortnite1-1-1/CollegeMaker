"""Comprehensive Tests for Feature R2: Deadline Calendar."""
from datetime import date, timedelta
import pytest
from server.models.portfolio import (
    ApplicationTracker,
    PortfolioItem,
    StudentPortfolio,
)
from server.services.calendar_service import calendar_service
from tests.conftest import APIClient, SEED_COLLEGES


def test_calendar_service_aggregation_and_upcoming():
    """Verify calendar service aggregates deadlines and filters next 14 days."""
    today = date(2025, 1, 15)

    tracker1 = ApplicationTracker(
        priority_deadline="2025-01-20",  # +5 days (upcoming 14)
        regular_deadline="2025-02-15",   # +31 days
        fafsa_deadline="2025-01-18",     # +3 days (upcoming 14)
        css_profile_deadline="2025-01-10", # -5 days (past)
        scholarship_deadlines={"Merit Award": "2025-01-25"}, # +10 days (upcoming 14)
    )

    item1 = PortfolioItem(
        college_id="166683",
        college_name="MIT",
        tracker=tracker1,
    )

    portfolio = StudentPortfolio(portfolio_id="test_cal_1", colleges=[item1])
    result = calendar_service.get_portfolio_calendar(portfolio, reference_date=today)

    assert result["total_events"] == 5
    assert result["colleges_with_deadlines"] == 1

    # Check chronological ordering
    dates = [e["date"] for e in result["events"]]
    assert dates == sorted(dates)

    # Check upcoming 14 days (should include Jan 18, Jan 20, Jan 25)
    upcoming = result["upcoming_14_days"]
    assert len(upcoming) == 3
    upcoming_dates = [e["date"] for e in upcoming]
    assert "2025-01-18" in upcoming_dates
    assert "2025-01-20" in upcoming_dates
    assert "2025-01-25" in upcoming_dates
    assert "2025-01-10" not in upcoming_dates  # past
    assert "2025-02-15" not in upcoming_dates  # beyond 14 days


def test_calendar_service_empty_portfolio():
    """Verify empty portfolio returns empty events without errors."""
    portfolio = StudentPortfolio(portfolio_id="empty_cal", colleges=[])
    result = calendar_service.get_portfolio_calendar(portfolio)
    assert result["events"] == []
    assert result["upcoming_14_days"] == []
    assert result["total_events"] == 0
    assert result["colleges_with_deadlines"] == 0


def test_calendar_api_endpoint():
    """Verify GET /api/portfolio/calendar returns valid deadline calendar payload."""
    client = APIClient()
    cid = SEED_COLLEGES["mit"]["id"]
    client.post("/api/portfolio/colleges", json={"college_id": cid})

    # Update tracker with deadlines
    today = date.today()
    in_5_days = (today + timedelta(days=5)).isoformat()
    in_20_days = (today + timedelta(days=20)).isoformat()

    client.put(
        f"/api/portfolio/colleges/{cid}/tracker",
        json={
            "priority_deadline": in_5_days,
            "regular_deadline": in_20_days,
            "fafsa_deadline": in_5_days,
        },
    )

    resp = client.get("/api/portfolio/calendar")
    assert resp.status_code == 200
    data = resp.json()

    assert "events" in data
    assert "upcoming_14_days" in data
    assert data["total_events"] >= 3
    assert data["colleges_with_deadlines"] >= 1

    # In 5 days events must be in upcoming_14_days
    upcoming_titles = [e["title"] for e in data["upcoming_14_days"]]
    assert any("Priority" in t for t in upcoming_titles)
    assert any("FAFSA" in t for t in upcoming_titles)
