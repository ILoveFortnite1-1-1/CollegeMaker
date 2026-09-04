"""Comprehensive Tests for Feature R7: Per-School Requirements Checklist."""
import pytest
from server.models.portfolio import ApplicationTracker, ChecklistItem
from server.services.portfolio_store import portfolio_store
from tests.conftest import APIClient, SEED_COLLEGES


def test_checklist_item_model_defaults():
    """Verify ChecklistItem default values and field validation."""
    item = ChecklistItem(name="2 Teacher Recommendations")
    assert item.name == "2 Teacher Recommendations"
    assert item.required is True
    assert item.completed is False
    assert item.deadline is None
    assert item.id.startswith("chk_")

    # Custom item with deadline
    custom = ChecklistItem(
        name="Art Portfolio",
        required=True,
        completed=True,
        deadline="2025-01-15",
    )
    assert custom.completed is True
    assert custom.deadline == "2025-01-15"


def test_checklist_crud_api_lifecycle():
    """Verify adding, updating, toggling, and getting checklist items via API."""
    client = APIClient()
    cid = SEED_COLLEGES["mit"]["id"]

    # 1. Save college
    client.post("/api/portfolio/colleges", json={"college_id": cid})

    # 2. Get initial checklist (defaults should be initialized)
    init_res = client.get(f"/api/portfolio/tracker/{cid}/checklist")
    assert init_res.status_code == 200
    init_items = init_res.json()["items"]
    assert len(init_items) >= 5

    # 3. Add custom requirement
    add_payload = {
        "name": "Maker Portfolio & Video Pitch",
        "required": True,
        "completed": False,
        "deadline": "2024-11-01",
    }
    add_res = client.post(f"/api/portfolio/tracker/{cid}/checklist", json=add_payload)
    assert add_res.status_code == 200
    created = add_res.json()
    item_id = created["id"]
    assert created["name"] == add_payload["name"]
    assert created["completed"] is False

    # 4. Toggle completion status
    update_res = client.put(
        f"/api/portfolio/tracker/{cid}/checklist/{item_id}",
        json={"completed": True},
    )
    assert update_res.status_code == 200
    updated = update_res.json()
    assert updated["completed"] is True

    # 5. Verify checklist contains updated item
    list_res = client.get(f"/api/portfolio/tracker/{cid}/checklist")
    assert list_res.status_code == 200
    items = list_res.json()["items"]
    custom_in_list = next((it for it in items if it["id"] == item_id), None)
    assert custom_in_list is not None
    assert custom_in_list["completed"] is True

    # 6. Delete item
    del_res = client.delete(f"/api/portfolio/tracker/{cid}/checklist/{item_id}")
    assert del_res.status_code == 200
    assert del_res.json()["deleted"] is True


def test_requirements_cross_school_matrix():
    """Verify GET /api/portfolio/requirements-matrix constructs cross-school summary table."""
    client = APIClient()
    c1 = SEED_COLLEGES["mit"]["id"]
    c2 = SEED_COLLEGES["stanford"]["id"]

    client.post("/api/portfolio/colleges", json={"college_id": c1})
    client.post("/api/portfolio/colleges", json={"college_id": c2})

    # Add custom requirement to Stanford
    client.post(
        f"/api/portfolio/tracker/{c2}/checklist",
        json={"name": "Special Department Essay", "required": True, "completed": False},
    )

    # Fetch matrix
    matrix_res = client.get("/api/portfolio/requirements-matrix")
    assert matrix_res.status_code == 200
    data = matrix_res.json()

    assert "matrix" in data
    assert "colleges" in data
    assert "summary_counts" in data
    assert len(data["colleges"]) == 2

    # Check summary counts for common items
    assert "Official High School Transcript" in data["summary_counts"]
    assert data["summary_counts"]["Official High School Transcript"] == 2
    assert data["summary_counts"]["Special Department Essay"] == 1


def test_checklist_nonexistent_college_returns_404():
    """Verify adding checklist item to unsaved/nonexistent college returns 404."""
    client = APIClient()
    res = client.post(
        "/api/portfolio/tracker/nonexistent_88888/checklist",
        json={"name": "Audition Tape"},
    )
    assert res.status_code == 404


def test_toggle_requirement_all_one_click():
    """Verify 1-click marking a requirement done across all saved colleges."""
    client = APIClient()
    c1 = SEED_COLLEGES["mit"]["id"]
    c2 = SEED_COLLEGES["stanford"]["id"]

    client.post("/api/portfolio/colleges", json={"college_id": c1})
    client.post("/api/portfolio/colleges", json={"college_id": c2})

    req_name = "Official High School Transcript"

    # Mark done for all schools in 1 click
    res = client.post(
        "/api/portfolio/requirements-matrix/toggle-all",
        json={"requirement_name": req_name, "completed": True},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["requirement_name"] == req_name
    assert data["completed"] is True
    assert data["updated_colleges"] == 2

    # Verify matrix shows all done
    matrix_res = client.get("/api/portfolio/requirements-matrix")
    assert matrix_res.status_code == 200
    matrix_data = matrix_res.json()
    row = next(r for r in matrix_data["matrix"] if r["requirement_name"] == req_name)
    assert row["completed_count"] == 2
    assert row["total_schools_requiring"] == 2

    # Toggle off in 1 click
    res_toggle = client.post(
        "/api/portfolio/requirements-matrix/toggle-all",
        json={"requirement_name": req_name, "completed": False},
    )
    assert res_toggle.status_code == 200
    assert res_toggle.json()["completed"] is False

    matrix_res2 = client.get("/api/portfolio/requirements-matrix")
    matrix_data2 = matrix_res2.json()
    row2 = next(r for r in matrix_data2["matrix"] if r["requirement_name"] == req_name)
    assert row2["completed_count"] == 0


def test_toggle_everything_one_click():
    """Verify 1-click marking ALL requirements across ALL saved colleges as done."""
    client = APIClient()
    c1 = SEED_COLLEGES["mit"]["id"]
    c2 = SEED_COLLEGES["stanford"]["id"]

    client.post("/api/portfolio/colleges", json={"college_id": c1})
    client.post("/api/portfolio/colleges", json={"college_id": c2})

    # 1-click mark ALL done
    res = client.post(
        "/api/portfolio/requirements-matrix/toggle-everything",
        json={"completed": True},
    )
    assert res.status_code == 200
    assert res.json()["completed"] is True

    # Verify matrix
    matrix_res = client.get("/api/portfolio/requirements-matrix")
    matrix_data = matrix_res.json()
    for row in matrix_data["matrix"]:
        if row["total_schools_requiring"] > 0:
            assert row["completed_count"] == row["total_schools_requiring"]


def test_toggle_college_checklist_bulk_one_click():
    """Verify 1-click marking all requirements for a single college as done."""
    client = APIClient()
    c1 = SEED_COLLEGES["mit"]["id"]
    client.post("/api/portfolio/colleges", json={"college_id": c1})

    res = client.post(
        f"/api/portfolio/tracker/{c1}/checklist/bulk",
        json={"completed": True},
    )
    assert res.status_code == 200
    assert res.json()["completed"] is True

    list_res = client.get(f"/api/portfolio/tracker/{c1}/checklist")
    assert list_res.status_code == 200
    items = list_res.json()["items"]
    assert all(it["completed"] is True for it in items)

