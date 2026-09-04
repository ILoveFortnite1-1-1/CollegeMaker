"""Comprehensive Tests for Feature R6: Alumni Outcomes Deep Dive (Field of Study)."""
import pytest
from server.models.canonical import FieldOfStudyItem
from server.services.college_service import college_service
from server.services.scorecard_client import scorecard_client
from tests.conftest import APIClient, SEED_COLLEGES


def test_field_of_study_item_model():
    """Verify FieldOfStudyItem model creation and alias handling."""
    item = FieldOfStudyItem(
        cip_code="1107",
        major_title="Computer Science",
        credential_level="Bachelor's Degree",
        median_earnings=105000,
        median_debt=24000,
        is_preferred=True,
    )
    assert item.cip_code == "1107"
    assert item.major_title == "Computer Science"
    assert item.median_earnings == 105000
    assert item.is_preferred is True

    # Test alias mapping
    item2 = FieldOfStudyItem(
        cip_code="1419",
        major_name="Mechanical Engineering",
        earnings=92000,
        debt=25000,
        is_preferred_major=False,
    )
    assert item2.major_title == "Mechanical Engineering"
    assert item2.median_earnings == 92000
    assert item2.median_debt == 25000
    assert item2.is_preferred is False


@pytest.mark.asyncio
async def test_scorecard_client_returns_sorted_programs():
    """Verify scorecard_client returns programs sorted by median earnings descending."""
    cid = SEED_COLLEGES["mit"]["id"]
    programs = await scorecard_client.get_field_of_study_programs(cid)
    assert len(programs) > 0

    earnings = [p.median_earnings for p in programs if p.median_earnings is not None]
    assert earnings == sorted(earnings, reverse=True)


@pytest.mark.asyncio
async def test_college_service_marks_preferred_majors():
    """Verify college_service flags preferred majors according to student preferences."""
    cid = SEED_COLLEGES["berkeley"]["id"]
    preferred = ["Computer Science", "Economics"]

    result = await college_service.get_field_of_study(cid, preferred_majors=preferred)
    assert result["college_id"] == cid
    assert "majors" in result
    assert len(result["majors"]) > 0

    # At least one major must be flagged preferred
    preferred_items = [m for m in result["majors"] if m["is_preferred"]]
    assert len(preferred_items) >= 1
    pref_titles = [m["major_title"] for m in preferred_items]
    assert any("Computer Science" in t for t in pref_titles)


def test_field_of_study_api_endpoint():
    """Verify GET /api/colleges/{college_id}/field-of-study returns valid JSON payload."""
    client = APIClient()
    stanford_id = SEED_COLLEGES["stanford"]["id"]

    # Set preferred major in session
    client.put("/api/portfolio/preferences", json={"preferred_majors": ["Mechanical Engineering"]})

    res = client.get(f"/api/colleges/{stanford_id}/field-of-study")
    assert res.status_code == 200
    data = res.json()

    assert data["college_id"] == stanford_id
    assert "majors" in data
    assert len(data["majors"]) > 0

    # Preferred major must be marked
    me_item = next((m for m in data["majors"] if "Mechanical" in m["major_title"]), None)
    assert me_item is not None
    assert me_item["is_preferred"] is True


def test_field_of_study_nonexistent_college_returns_404():
    """Verify querying field-of-study for nonexistent college ID returns 404."""
    client = APIClient()
    res = client.get("/api/colleges/nonexistent_999999/field-of-study")
    assert res.status_code == 404
