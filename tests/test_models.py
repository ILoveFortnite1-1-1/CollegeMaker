"""Unit tests for Canonical, Portfolio, and Ledger Models."""
import pytest
from server.models.canonical import (
    CanonicalCollege,
    ConfidenceLevel,
    Location,
    MetricField,
    SOURCE_PRECEDENCE_RANKS,
    SourceType,
)
from server.models.ledger import EnrichmentRun, LedgerEvent
from server.models.portfolio import FitWeights, StudentPortfolio, StudentPreferences


def test_metric_field_defaults():
    field = MetricField(value=50000)
    assert field.value == 50000
    assert field.source_type == SourceType.GOVERNMENT
    assert field.confidence == ConfidenceLevel.REPORTED
    assert field.status == "verified"
    assert field.year == 2023


def test_source_precedence_hierarchy_ranking():
    assert SOURCE_PRECEDENCE_RANKS[SourceType.GOVERNMENT] > SOURCE_PRECEDENCE_RANKS[SourceType.OFFICIAL_INSTITUTIONAL]
    assert SOURCE_PRECEDENCE_RANKS[SourceType.OFFICIAL_INSTITUTIONAL] > SOURCE_PRECEDENCE_RANKS[SourceType.REPUTABLE_SECONDARY]
    assert SOURCE_PRECEDENCE_RANKS[SourceType.REPUTABLE_SECONDARY] > SOURCE_PRECEDENCE_RANKS[SourceType.AI_EXTRACTED]
    assert SOURCE_PRECEDENCE_RANKS[SourceType.AI_EXTRACTED] > SOURCE_PRECEDENCE_RANKS[SourceType.MODEL_ESTIMATE]
    assert SOURCE_PRECEDENCE_RANKS[SourceType.MODEL_ESTIMATE] > SOURCE_PRECEDENCE_RANKS[SourceType.USER]


def test_fit_weights_normalization():
    weights = FitWeights(
        career=25.0,
        roi=20.0,
        academic=15.0,
        admissions=10.0,
        experience=10.0,
        strength=10.0,
        location=5.0,
        cost=5.0,
    )
    norm = weights.normalized()
    assert sum(norm.values()) == pytest.approx(1.0)
    assert norm["career"] == pytest.approx(0.25)
    assert norm["roi"] == pytest.approx(0.20)
    assert norm["cost"] == pytest.approx(0.05)


def test_fit_weights_partial_normalization():
    weights = FitWeights(career=50.0, roi=50.0)
    norm = weights.normalized(available_dimensions=["career", "roi"])
    assert sum(norm.values()) == pytest.approx(1.0)
    assert norm["career"] == pytest.approx(0.5)
    assert norm["roi"] == pytest.approx(0.5)


def test_ledger_event_generation():
    evt = LedgerEvent(
        college_id="166027",
        college_name="MIT",
        run_id="run_123",
        field_path="qualitative.strengths",
        old_value=None,
        new_value=["World-leading STEM"],
        source_ids=["Gemini 2.5 Flash"],
        source_type=SourceType.AI_EXTRACTED,
        confidence=ConfidenceLevel.QUALITATIVE,
    )
    assert evt.event_id.startswith("evt_")
    assert evt.college_id == "166027"
    assert evt.status == "committed"


def test_student_portfolio_model():
    portfolio = StudentPortfolio(
        portfolio_id="port_test_123",
        preferences=StudentPreferences(gpa=3.9, sat_score=1500, home_state="MA"),
    )
    assert portfolio.portfolio_id == "port_test_123"
    assert portfolio.preferences.gpa == 3.9
    assert portfolio.preferences.sat_score == 1500
    assert len(portfolio.colleges) == 0
