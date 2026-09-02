"""Knowledge Ledger and Audit Models."""
from datetime import datetime, timezone
from typing import Any, List, Optional
import uuid
from pydantic import BaseModel, Field
from server.models.canonical import ConfidenceLevel, SourceType


class LedgerEvent(BaseModel):
    """An atomic mutation event logged to the audit ledger."""
    event_id: str = Field(default_factory=lambda: f"evt_{uuid.uuid4().hex[:12]}")
    college_id: str
    college_name: str
    run_id: str
    field_path: str
    old_value: Optional[Any] = None
    new_value: Any
    source_ids: List[str] = Field(default_factory=list)
    source_type: SourceType = SourceType.AI_EXTRACTED
    confidence: ConfidenceLevel = ConfidenceLevel.AI_DERIVED
    status: str = "committed"  # committed, rejected, merged
    observed_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    committed_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class EnrichmentRun(BaseModel):
    """Metadata for an AI/data enrichment run."""
    run_id: str = Field(default_factory=lambda: f"run_{uuid.uuid4().hex[:10]}")
    college_id: str
    college_name: str
    model: str = "Gemini 2.5 Flash"
    status: str = "success"  # success, partial, failed, degraded
    fields_updated: List[str] = Field(default_factory=list)
    error_message: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class CollegeKnowledgeEntry(BaseModel):
    """Consolidated knowledge entry for a college."""
    college_id: str
    college_name: str
    last_updated: str
    event_count: int
    latest_enrichment: Optional[EnrichmentRun] = None
    recent_events: List[LedgerEvent] = Field(default_factory=list)


class AuditResponse(BaseModel):
    """Response payload for knowledge audit endpoints."""
    college_id: str
    total_events: int
    events: List[LedgerEvent] = Field(default_factory=list)
    last_run: Optional[EnrichmentRun] = None
