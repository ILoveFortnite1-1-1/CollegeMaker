"""Source Precedence Merge Engine."""
from typing import Any, List, Optional, Tuple, TypeVar
from server.models.canonical import (
    CanonicalCollege,
    ConfidenceLevel,
    MetricField,
    SOURCE_PRECEDENCE_RANKS,
    SourceType,
)
from server.models.ledger import LedgerEvent

T = TypeVar("T")


def should_incoming_overwrite(
    existing_source_type: SourceType,
    incoming_source_type: SourceType,
    existing_retrieved_at: Optional[str] = None,
    incoming_retrieved_at: Optional[str] = None,
) -> bool:
    """Determine if incoming data has higher authority or is a newer update of equal authority."""
    existing_rank = SOURCE_PRECEDENCE_RANKS.get(existing_source_type, 0)
    incoming_rank = SOURCE_PRECEDENCE_RANKS.get(incoming_source_type, 0)

    if incoming_rank > existing_rank:
        return True
    if incoming_rank == existing_rank:
        if incoming_retrieved_at and existing_retrieved_at:
            return incoming_retrieved_at >= existing_retrieved_at
        return True
    return False


def merge_metric_field(
    existing: Optional[MetricField[T]],
    incoming: Optional[MetricField[T]],
    field_path: str,
    college_id: str,
    college_name: str,
    run_id: str,
) -> Tuple[Optional[MetricField[T]], Optional[LedgerEvent]]:
    """Merge two MetricFields following source precedence rules and produce an audit event if mutated."""
    if incoming is None or incoming.value is None:
        return existing, None
    if existing is None or existing.value is None:
        event = LedgerEvent(
            college_id=college_id,
            college_name=college_name,
            run_id=run_id,
            field_path=field_path,
            old_value=None,
            new_value=incoming.value,
            source_ids=[incoming.source],
            source_type=incoming.source_type,
            confidence=incoming.confidence,
            status="committed",
            observed_at=incoming.retrieved_at,
        )
        return incoming, event

    if should_incoming_overwrite(
        existing.source_type,
        incoming.source_type,
        existing.retrieved_at,
        incoming.retrieved_at,
    ):
        if existing.value != incoming.value:
            event = LedgerEvent(
                college_id=college_id,
                college_name=college_name,
                run_id=run_id,
                field_path=field_path,
                old_value=existing.value,
                new_value=incoming.value,
                source_ids=[incoming.source],
                source_type=incoming.source_type,
                confidence=incoming.confidence,
                status="committed",
                observed_at=incoming.retrieved_at,
            )
            return incoming, event
        return incoming, None

    # Existing has higher precedence; reject incoming overwrite
    return existing, None


def merge_college_records(
    existing: CanonicalCollege,
    incoming: CanonicalCollege,
    run_id: str = "merge_run",
) -> Tuple[CanonicalCollege, List[LedgerEvent]]:
    """Deep merge incoming college updates into existing record with strict source precedence enforcement."""
    events: List[LedgerEvent] = []
    merged = existing.model_copy(deep=True)

    # 1. Undergrad size
    merged.undergrad_size, evt = merge_metric_field(
        merged.undergrad_size, incoming.undergrad_size, "undergrad_size", existing.id, existing.name, run_id
    )
    if evt:
        events.append(evt)

    # 2. Admissions
    for field_name in [
        "acceptance_rate",
        "sat_reading_25",
        "sat_reading_75",
        "sat_math_25",
        "sat_math_75",
        "sat_total_25",
        "sat_total_75",
        "act_25",
        "act_75",
        "application_fee",
    ]:
        exist_val = getattr(merged.admissions, field_name)
        incom_val = getattr(incoming.admissions, field_name)
        new_val, evt = merge_metric_field(
            exist_val, incom_val, f"admissions.{field_name}", existing.id, existing.name, run_id
        )
        setattr(merged.admissions, field_name, new_val)
        if evt:
            events.append(evt)

    # 3. Costs
    for field_name in [
        "tuition_in_state",
        "tuition_out_of_state",
        "room_and_board",
        "books_supplies",
        "net_price_average",
        "net_price_income_0_30k",
        "net_price_income_30k_48k",
        "net_price_income_48k_75k",
        "net_price_income_75k_110k",
        "net_price_income_110k_plus",
    ]:
        exist_val = getattr(merged.costs, field_name)
        incom_val = getattr(incoming.costs, field_name)
        new_val, evt = merge_metric_field(
            exist_val, incom_val, f"costs.{field_name}", existing.id, existing.name, run_id
        )
        setattr(merged.costs, field_name, new_val)
        if evt:
            events.append(evt)

    # 4. Outcomes
    for field_name in [
        "completion_rate_4yr",
        "completion_rate_6yr",
        "retention_rate_ft",
        "median_earnings_10yr",
        "median_debt_grad",
    ]:
        exist_val = getattr(merged.outcomes, field_name)
        incom_val = getattr(incoming.outcomes, field_name)
        new_val, evt = merge_metric_field(
            exist_val, incom_val, f"outcomes.{field_name}", existing.id, existing.name, run_id
        )
        setattr(merged.outcomes, field_name, new_val)
        if evt:
            events.append(evt)

    # 5. Faculty-to-student ratio
    merged.faculty_to_student_ratio, evt = merge_metric_field(
        merged.faculty_to_student_ratio,
        incoming.faculty_to_student_ratio,
        "faculty_to_student_ratio",
        existing.id,
        existing.name,
        run_id,
    )
    if evt:
        events.append(evt)

    # 6. Qualitative enrichment merge
    if incoming.qualitative and incoming.qualitative.enrichment_status in ["complete", "partial"]:
        qual = incoming.qualitative
        if qual.strengths and qual.strengths != merged.qualitative.strengths:
            events.append(
                LedgerEvent(
                    college_id=existing.id,
                    college_name=existing.name,
                    run_id=run_id,
                    field_path="qualitative.strengths",
                    old_value=merged.qualitative.strengths,
                    new_value=qual.strengths,
                    source_ids=[qual.enrichment_model or "Gemini 2.5 Flash"],
                    source_type=SourceType.AI_EXTRACTED,
                    confidence=ConfidenceLevel.QUALITATIVE,
                    status="committed",
                )
            )
            merged.qualitative.strengths = qual.strengths

        if qual.upsides and qual.upsides != merged.qualitative.upsides:
            events.append(
                LedgerEvent(
                    college_id=existing.id,
                    college_name=existing.name,
                    run_id=run_id,
                    field_path="qualitative.upsides",
                    old_value=merged.qualitative.upsides,
                    new_value=qual.upsides,
                    source_ids=[qual.enrichment_model or "Gemini 2.5 Flash"],
                    source_type=SourceType.AI_EXTRACTED,
                    confidence=ConfidenceLevel.QUALITATIVE,
                    status="committed",
                )
            )
            merged.qualitative.upsides = qual.upsides

        if qual.tradeoffs and qual.tradeoffs != merged.qualitative.tradeoffs:
            events.append(
                LedgerEvent(
                    college_id=existing.id,
                    college_name=existing.name,
                    run_id=run_id,
                    field_path="qualitative.tradeoffs",
                    old_value=merged.qualitative.tradeoffs,
                    new_value=qual.tradeoffs,
                    source_ids=[qual.enrichment_model or "Gemini 2.5 Flash"],
                    source_type=SourceType.AI_EXTRACTED,
                    confidence=ConfidenceLevel.QUALITATIVE,
                    status="committed",
                )
            )
            merged.qualitative.tradeoffs = qual.tradeoffs

        if qual.campus_culture_summary:
            merged.qualitative.campus_culture_summary = qual.campus_culture_summary
        if qual.academic_reputation_summary:
            merged.qualitative.academic_reputation_summary = qual.academic_reputation_summary
        if qual.notable_alumni:
            merged.qualitative.notable_alumni = qual.notable_alumni
        merged.qualitative.last_enriched_at = qual.last_enriched_at
        merged.qualitative.enrichment_model = qual.enrichment_model
        merged.qualitative.enrichment_status = qual.enrichment_status

    # 7. Evidence claims
    if incoming.evidence_claims:
        existing_claim_texts = {c.claim for c in merged.evidence_claims}
        for claim in incoming.evidence_claims:
            if claim.claim not in existing_claim_texts:
                merged.evidence_claims.append(claim)

    return merged, events
