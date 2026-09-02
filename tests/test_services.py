"""Unit and Integration Tests for Core Services."""
import asyncio
import pytest
from server.models.canonical import (
    CanonicalCollege,
    ConfidenceLevel,
    Location,
    MetricField,
    SourceType,
)
from server.models.portfolio import StudentPreferences
from server.services.comparison import comparison_service
from server.services.fit_scorer import fit_scorer
from server.services.gemini import gemini_service
from server.services.ledger import ledger_service
from server.services.portfolio import portfolio_service
from server.services.precedence import (
    merge_college_records,
    merge_metric_field,
    should_incoming_overwrite,
)
from server.services.scorecard import scorecard_service


@pytest.mark.asyncio
async def test_scorecard_service_seed_loading():
    colleges, total = await scorecard_service.search_colleges(page=1, page_size=10)
    assert total >= 50
    assert len(colleges) == 10
    assert any("University" in c.name or "Institute" in c.name for c in colleges)


@pytest.mark.asyncio
async def test_scorecard_service_get_by_id():
    mit = await scorecard_service.get_college_by_id("166683")
    assert mit is not None
    assert "Massachusetts Institute of Technology" in mit.name
    assert mit.location.state == "MA"
    assert mit.admissions.acceptance_rate.value == pytest.approx(0.04)


@pytest.mark.asyncio
async def test_scorecard_service_filtering():
    # Filter by state CA
    ca_colleges, ca_total = await scorecard_service.search_colleges(state="CA")
    assert ca_total > 0
    assert all(c.location.state == "CA" for c in ca_colleges)

    # Filter by public control
    pub_colleges, pub_total = await scorecard_service.search_colleges(control="public")
    assert pub_total > 0
    assert all(c.control == "public" for c in pub_colleges)


def test_source_precedence_merge_rules():
    # Government (Rank 6) vs AI Extracted (Rank 3) -> Incoming AI Extracted should NOT overwrite Government
    assert not should_incoming_overwrite(
        existing_source_type=SourceType.GOVERNMENT,
        incoming_source_type=SourceType.AI_EXTRACTED,
    )

    # Secondary (Rank 4) vs Institutional (Rank 5) -> Incoming Institutional SHOULD overwrite Secondary
    assert should_incoming_overwrite(
        existing_source_type=SourceType.REPUTABLE_SECONDARY,
        incoming_source_type=SourceType.OFFICIAL_INSTITUTIONAL,
    )

    # User (Rank 1) vs AI Extracted (Rank 3) -> Incoming AI Extracted SHOULD overwrite User
    assert should_incoming_overwrite(
        existing_source_type=SourceType.USER,
        incoming_source_type=SourceType.AI_EXTRACTED,
    )


def test_merge_metric_field():
    existing_gov = MetricField(
        value=60000,
        source="Scorecard",
        source_type=SourceType.GOVERNMENT,
        retrieved_at="2026-01-01T00:00:00Z",
    )
    incoming_ai = MetricField(
        value=65000,
        source="Gemini",
        source_type=SourceType.AI_EXTRACTED,
        retrieved_at="2026-02-01T00:00:00Z",
    )

    merged, event = merge_metric_field(
        existing=existing_gov,
        incoming=incoming_ai,
        field_path="costs.tuition_in_state",
        college_id="166027",
        college_name="MIT",
        run_id="run_1",
    )
    # Value should remain government 60000 and event should be None
    assert merged.value == 60000
    assert event is None


@pytest.mark.asyncio
async def test_fit_scorer_evaluation():
    mit = await scorecard_service.get_college_by_id("166027")
    prefs = StudentPreferences(
        gpa=3.95,
        sat_score=1560,
        home_state="MA",
        budget_max_annual=30000,
        preferred_majors=["Computer Science"],
        preferred_location_types=["Urban"],
    )

    analysis = fit_scorer.evaluate_college_fit(mit, prefs)
    assert analysis.overall_score > 0
    assert analysis.overall_score <= 100
    assert analysis.category in ["Reach", "Target", "Likely"]
    assert len(analysis.dimensions) == 8


@pytest.mark.asyncio
async def test_portfolio_service_guest_lifecycle():
    test_pid = "port_unit_test_999"
    # 1. Clear any previous
    await portfolio_service.clear_portfolio(test_pid)

    # 2. Add MIT
    updated = await portfolio_service.add_college(test_pid, "166027", notes="Dream school")
    assert len(updated.colleges) == 1
    assert updated.colleges[0].college_id == "166027"

    # 3. Add Stanford
    updated = await portfolio_service.add_college(test_pid, "243744")
    assert len(updated.colleges) == 2

    # 4. Summary check
    summary = await portfolio_service.get_summary(test_pid)
    assert summary.total_colleges == 2
    assert summary.average_net_price is not None

    # 5. Remove MIT
    updated = await portfolio_service.remove_college(test_pid, "166027")
    assert len(updated.colleges) == 1
    assert updated.colleges[0].college_id == "243744"

    # 6. Clear
    updated = await portfolio_service.clear_portfolio(test_pid)
    assert len(updated.colleges) == 0


@pytest.mark.asyncio
async def test_comparison_service():
    result = await comparison_service.compare_colleges(["166027", "243744"])
    assert len(result["colleges"]) == 2
    assert "Overview" in result["metrics"]
    assert "Admissions" in result["metrics"]
    assert "Costs & Financial Aid" in result["metrics"]
    assert "lowest_net_price" in result["best_in_class"]
    assert len(result["summary"]) > 0


@pytest.mark.asyncio
async def test_knowledge_ledger_atomic_recording():
    from server.models.ledger import LedgerEvent

    evt = LedgerEvent(
        college_id="test_school",
        college_name="Test University",
        run_id="run_test",
        field_path="admissions.acceptance_rate",
        old_value=0.25,
        new_value=0.22,
        source_ids=["Scorecard Ingestion"],
        source_type=SourceType.GOVERNMENT,
        confidence=ConfidenceLevel.REPORTED,
    )

    await ledger_service.record_events([evt])
    events = await ledger_service.get_events_for_college("test_school")
    assert len(events) >= 1
    assert events[-1].field_path == "admissions.acceptance_rate"
    assert events[-1].new_value == 0.22


@pytest.mark.asyncio
async def test_gemini_service_graceful_degradation():
    mit = await scorecard_service.get_college_by_id("166027")
    # In test mode without valid key, should return graceful qualitative data without throwing
    qual, claims, run, events = await gemini_service.enrich_college(mit, force_refresh=True)
    assert qual is not None
    assert len(qual.strengths) > 0
    assert run.status in ["success_seed", "complete", "cached", "degraded", "failed"]
