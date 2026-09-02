"""Canonical College Data Model with Full Provenance."""
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field


class SourceType(str, Enum):
    """Hierarchy of data authority for source precedence."""
    GOVERNMENT = "government"
    OFFICIAL_INSTITUTIONAL = "official_institutional"
    REPUTABLE_SECONDARY = "reputable_secondary"
    AI_EXTRACTED = "ai_extracted"
    MODEL_ESTIMATE = "model_estimate"
    USER = "user"


# Numerical rank for source precedence (higher is more authoritative)
SOURCE_PRECEDENCE_RANKS = {
    SourceType.GOVERNMENT: 6,
    SourceType.OFFICIAL_INSTITUTIONAL: 5,
    SourceType.REPUTABLE_SECONDARY: 4,
    SourceType.AI_EXTRACTED: 3,
    SourceType.MODEL_ESTIMATE: 2,
    SourceType.USER: 1,
}


class ConfidenceLevel(str, Enum):
    """Classification of data confidence."""
    REPORTED = "reported"
    CALCULATED = "calculated"
    AI_DERIVED = "ai_derived"
    ESTIMATED = "estimated"
    QUALITATIVE = "qualitative"


T = TypeVar("T")


class MetricField(BaseModel, Generic[T]):
    """A data field wrapped with authoritative provenance metadata."""
    value: Optional[T] = None
    source: str = "U.S. Department of Education College Scorecard"
    source_type: SourceType = SourceType.GOVERNMENT
    year: Optional[int] = 2023
    confidence: ConfidenceLevel = ConfidenceLevel.REPORTED
    status: str = "verified"  # verified, provisional, cached, estimated
    retrieved_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    notes: Optional[str] = None


class Location(BaseModel):
    """Geographic location information."""
    city: str
    state: str
    zip: Optional[str] = None
    locale: Optional[str] = None
    location_type: str = "Urban"  # Urban, Suburban, Rural, Town
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class CostData(BaseModel):
    """Institutional cost data with per-field provenance."""
    tuition_in_state: MetricField[int]
    tuition_out_of_state: MetricField[int]
    room_and_board: Optional[MetricField[int]] = None
    books_supplies: Optional[MetricField[int]] = None
    net_price_average: MetricField[int]
    net_price_income_0_30k: Optional[MetricField[int]] = None
    net_price_income_30k_48k: Optional[MetricField[int]] = None
    net_price_income_48k_75k: Optional[MetricField[int]] = None
    net_price_income_75k_110k: Optional[MetricField[int]] = None
    net_price_income_110k_plus: Optional[MetricField[int]] = None


class AdmissionsData(BaseModel):
    """Admissions and test score metrics with provenance."""
    acceptance_rate: MetricField[float]  # 0.0 to 1.0
    sat_reading_25: Optional[MetricField[int]] = None
    sat_reading_75: Optional[MetricField[int]] = None
    sat_math_25: Optional[MetricField[int]] = None
    sat_math_75: Optional[MetricField[int]] = None
    sat_total_25: Optional[MetricField[int]] = None
    sat_total_75: Optional[MetricField[int]] = None
    act_25: Optional[MetricField[int]] = None
    act_75: Optional[MetricField[int]] = None
    application_fee: Optional[MetricField[int]] = None


class OutcomesData(BaseModel):
    """Post-graduation career and financial outcomes."""
    completion_rate_4yr: Optional[MetricField[float]] = None
    completion_rate_6yr: MetricField[float]
    retention_rate_ft: Optional[MetricField[float]] = None
    median_earnings_10yr: MetricField[int]
    median_debt_grad: Optional[MetricField[int]] = None


class QualitativeData(BaseModel):
    """AI-enriched or qualitative institutional research."""
    strengths: List[str] = Field(default_factory=list)
    upsides: List[str] = Field(default_factory=list)
    tradeoffs: List[str] = Field(default_factory=list)
    campus_culture_summary: Optional[str] = None
    academic_reputation_summary: Optional[str] = None
    notable_alumni: Optional[List[str]] = Field(default_factory=list)
    last_enriched_at: Optional[str] = None
    enrichment_model: Optional[str] = None
    enrichment_status: str = "not_started"  # not_started, in_progress, complete, failed, degraded
    enrichment_notes: Optional[str] = None


class EvidenceClaim(BaseModel):
    """Specific claim with external citation and verification."""
    claim: str
    field_path: Optional[str] = None
    source: str
    source_type: SourceType = SourceType.REPUTABLE_SECONDARY
    year: Optional[int] = 2024
    url: Optional[str] = None
    verified: bool = True


class CanonicalCollege(BaseModel):
    """Primary canonical representation of a college record."""
    id: str  # College ID / slug (e.g., '166027' or 'mit')
    unitid: Optional[int] = None
    name: str
    alias: Optional[str] = None
    control: str = "public"  # public, private_nonprofit, private_for_profit
    institution_type: str = "4-year"
    location: Location
    undergrad_size: MetricField[int]
    admissions: AdmissionsData
    costs: CostData
    outcomes: OutcomesData
    faculty_to_student_ratio: Optional[MetricField[str]] = None
    popular_programs: List[str] = Field(default_factory=list)
    qualitative: QualitativeData = Field(default_factory=QualitativeData)
    evidence_claims: List[EvidenceClaim] = Field(default_factory=list)
    
    # Dynamic fit scoring (computed in context of a student's profile)
    fit_category: Optional[str] = None  # Reach, Target, Likely
    fit_score: Optional[float] = None
    fit_breakdown: Optional[dict] = None
    
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_api_dict(self) -> dict:
        """Produce dictionary with enriched schema aliases, flat helpers, and provenance mapping."""
        base = self.model_dump()
        is_private = "private" in self.control.lower()
        school_type = "private" if is_private else "public"

        # Build provenance mapping
        provenance = {}
        def add_prov(path, field):
            if field and isinstance(field, dict) and "source" in field:
                src_type = field.get("source_type", "government")
                conf = field.get("confidence", "reported")
                if conf == "reported" or src_type == "government":
                    cls_name = "Reported"
                elif conf == "calculated":
                    cls_name = "Calculated"
                elif conf in ["ai_derived", "AI_derived"] or src_type == "ai_extracted":
                    cls_name = "AI-derived"
                elif conf == "estimated" or src_type == "model_estimate":
                    cls_name = "Estimated"
                else:
                    cls_name = "Qualitative"
                provenance[path] = {
                    "source": field.get("source", "U.S. Department of Education College Scorecard"),
                    "source_type": src_type,
                    "classification": cls_name,
                    "confidence": 0.95 if cls_name == "Reported" else 0.85,
                    "retrieved_at": field.get("retrieved_at", self.updated_at),
                    "year": field.get("year", 2023),
                }

        add_prov("overview.enrollment", base.get("undergrad_size"))
        add_prov("undergrad_size", base.get("undergrad_size"))
        add_prov("admissions.acceptance_rate", base.get("admissions", {}).get("acceptance_rate"))
        add_prov("admissions.sat_total", base.get("admissions", {}).get("sat_total_25"))
        add_prov("cost.net_price", base.get("costs", {}).get("net_price_average"))
        add_prov("cost.tuition_in_state", base.get("costs", {}).get("tuition_in_state"))
        add_prov("cost.tuition_out_of_state", base.get("costs", {}).get("tuition_out_of_state"))
        add_prov("outcomes.graduation_rate", base.get("outcomes", {}).get("completion_rate_6yr"))
        add_prov("outcomes.median_earnings", base.get("outcomes", {}).get("median_earnings_10yr"))
        add_prov("outcomes.retention_rate", base.get("outcomes", {}).get("retention_rate_ft"))
        if self.qualitative and self.qualitative.strengths:
            provenance["qualitative.strengths"] = {
                "source": self.qualitative.enrichment_model or "Gemini 2.5 Flash",
                "source_type": "ai_extracted",
                "classification": "Qualitative",
                "confidence": "qualitative",
                "retrieved_at": self.qualitative.last_enriched_at or self.updated_at,
                "year": 2024,
            }

        # Enhance admissions sub-dict
        admissions_dict = dict(base.get("admissions", {}))
        admissions_dict["admit_rate"] = admissions_dict.get("acceptance_rate")

        # Enhance cost sub-dict
        costs_dict = dict(base.get("costs", {}))
        costs_dict["net_price"] = costs_dict.get("net_price_average")
        costs_dict["net_price_avg"] = costs_dict.get("net_price_average")
        costs_dict["cost_of_attendance"] = costs_dict.get("tuition_in_state")

        # Enhance outcomes sub-dict
        outcomes_dict = dict(base.get("outcomes", {}))
        outcomes_dict["graduation_rate"] = outcomes_dict.get("completion_rate_6yr")
        outcomes_dict["median_earnings"] = outcomes_dict.get("median_earnings_10yr")
        outcomes_dict["retention_rate"] = outcomes_dict.get("retention_rate_ft")

        # Enhance overview sub-dict
        overview_dict = {
            "enrollment": base.get("undergrad_size"),
            "undergrad_size": base.get("undergrad_size"),
            "location": base.get("location"),
            "type": school_type,
            "control": self.control,
            "location_type": self.location.location_type,
        }

        # Enhance qualitative sub-dict
        qual_dict = dict(base.get("qualitative", {}))
        qual_dict["highlights"] = qual_dict.get("strengths", [])

        res = {
            **base,
            "canonical_name": self.name,
            "type": school_type,
            "state": self.location.state,
            "overview": overview_dict,
            "admissions": admissions_dict,
            "cost": costs_dict,
            "costs": costs_dict,
            "outcomes": outcomes_dict,
            "qualitative": qual_dict,
            "provenance": provenance,
            "last_refreshed": self.updated_at,
            "refreshed_at": self.updated_at,
        }
        return res
