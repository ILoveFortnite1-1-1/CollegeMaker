"""Comprehensive Tests for Feature R3: Essay Tracker."""
import pytest
from server.models.portfolio import EssayEntry
from server.services.portfolio_store import portfolio_store
from tests.conftest import APIClient, SEED_COLLEGES


def test_essay_entry_model_properties():
    """Verify EssayEntry validation, reuse_count, and alias synchronization."""
    essay = EssayEntry(
        prompt="Tell us about a challenge you overcame.",
        word_limit=650,
        current_word_count=350,
        draft_status="Drafting",
        colleges=["166683", "243744", "110635"],
    )
    assert essay.reuse_count == 3
    assert essay.draft_status == "Drafting"
    d = essay.to_dict()
    assert d["reuse_count"] == 3
    assert d["word_count"] == 350
    assert len(d["college_ids"]) == 3


def test_essay_crud_end_to_end_api():
    """Verify full CRUD lifecycle via REST API endpoints."""
    client = APIClient()

    # 1. Initially empty
    list_res0 = client.get("/api/portfolio/essays")
    assert list_res0.status_code == 200
    assert list_res0.json()["count"] == 0

    # 2. Create new essay
    create_payload = {
        "title": "Common App Personal Statement",
        "prompt": "Share your story and background.",
        "word_limit": 650,
        "current_word_count": 150,
        "draft_status": "Drafting",
        "colleges": [SEED_COLLEGES["mit"]["id"], SEED_COLLEGES["stanford"]["id"]],
    }
    create_res = client.post("/api/portfolio/essays", json=create_payload)
    assert create_res.status_code == 200
    created = create_res.json()
    essay_id = created["id"]
    assert essay_id.startswith("essay_")
    assert created["prompt"] == create_payload["prompt"]
    assert created["reuse_count"] == 2

    # 3. List essays - now contains 1
    list_res1 = client.get("/api/portfolio/essays")
    assert list_res1.status_code == 200
    data1 = list_res1.json()
    assert data1["count"] == 1
    assert data1["essays"][0]["id"] == essay_id
    assert data1["essays"][0]["reuse_count"] == 2

    # 4. Update essay
    update_payload = {
        "current_word_count": 620,
        "draft_status": "Final",
        "title": "Common App Essay (Final Polish)",
    }
    update_res = client.put(f"/api/portfolio/essays/{essay_id}", json=update_payload)
    assert update_res.status_code == 200
    updated = update_res.json()
    assert updated["current_word_count"] == 620
    assert updated["draft_status"] == "Final"
    assert updated["title"] == "Common App Essay (Final Polish)"

    # 5. Delete essay
    del_res = client.delete(f"/api/portfolio/essays/{essay_id}")
    assert del_res.status_code == 200
    assert del_res.json()["deleted"] is True

    # 6. Verify empty again
    list_res2 = client.get("/api/portfolio/essays")
    assert list_res2.status_code == 200
    assert list_res2.json()["count"] == 0


def test_essay_update_nonexistent_returns_404():
    """Verify updating nonexistent essay ID returns 404."""
    client = APIClient()
    res = client.put("/api/portfolio/essays/nonexistent_123", json={"current_word_count": 100})
    assert res.status_code == 404


def test_essay_delete_nonexistent_returns_404():
    """Verify deleting nonexistent essay ID returns 404."""
    client = APIClient()
    res = client.delete("/api/portfolio/essays/nonexistent_123")
    assert res.status_code == 404


def test_essay_supplemental_vs_common_app_separation():
    """Verify distinguishing supplemental essays from generic common app personal statement."""
    client = APIClient()

    # 1. Create Common App Main Essay
    res_ca = client.post(
        "/api/portfolio/essays",
        json={
            "title": "Common App Personal Statement",
            "prompt": "Some students have a background...",
            "word_limit": 650,
            "essay_type": "Common App",
            "is_common_app": True,
        },
    )
    assert res_ca.status_code == 200
    ca_data = res_ca.json()
    assert ca_data["is_common_app"] is True
    assert ca_data["essay_type"] == "Common App"

    # 2. Create School-Specific Supplemental Essay
    res_supp = client.post(
        "/api/portfolio/essays",
        json={
            "title": "Why Stanford - Intellectual Vitality",
            "prompt": "Reflect on an idea or experience...",
            "word_limit": 250,
            "essay_type": "Supplemental",
            "colleges": [SEED_COLLEGES["stanford"]["id"]],
        },
    )
    assert res_supp.status_code == 200
    supp_data = res_supp.json()
    assert supp_data["is_common_app"] is False
    assert supp_data["essay_type"] == "Supplemental"
    assert len(supp_data["colleges"]) == 1
