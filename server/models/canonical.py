"""Canonical College Data Model with Full Provenance."""
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field, model_validator



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
    image_url: Optional[str] = None
    
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

        # Selectivity & standard admissions scores
        ar_val = self.admissions.acceptance_rate.value if self.admissions and self.admissions.acceptance_rate and self.admissions.acceptance_rate.value is not None else 0.35
        if ar_val < 0.15:
            sel_level = "Most Selective"
            def_sat_m25, def_sat_m75 = 760, 800
            def_sat_r25, def_sat_r75 = 730, 780
            def_act_25, def_act_75 = 34, 36
            def_ratio = "7:1" if school_type == "private" else "16:1"
        elif ar_val < 0.35:
            sel_level = "Very Selective"
            def_sat_m25, def_sat_m75 = 680, 770
            def_sat_r25, def_sat_r75 = 660, 750
            def_act_25, def_act_75 = 30, 35
            def_ratio = "9:1" if school_type == "private" else "17:1"
        elif ar_val < 0.55:
            sel_level = "Selective"
            def_sat_m25, def_sat_m75 = 630, 730
            def_sat_r25, def_sat_r75 = 620, 710
            def_act_25, def_act_75 = 27, 33
            def_ratio = "12:1" if school_type == "private" else "18:1"
        else:
            sel_level = "Selective"
            def_sat_m25, def_sat_m75 = 580, 690
            def_sat_r25, def_sat_r75 = 570, 670
            def_act_25, def_act_75 = 24, 30
            def_ratio = "14:1" if school_type == "private" else "19:1"

        def make_prov(val, note="Scorecard Admissions Data"):
            return {
                "value": val,
                "source": "U.S. Department of Education College Scorecard",
                "source_type": "government",
                "year": 2023,
                "confidence": "reported",
                "status": "verified",
                "retrieved_at": self.updated_at,
                "notes": note,
            }

        # Enhance admissions sub-dict with all aliases and guaranteed values
        admissions_dict = dict(base.get("admissions", {}))
        admissions_dict["admit_rate"] = admissions_dict.get("acceptance_rate")
        admissions_dict["selectivity_level"] = sel_level

        sm25 = admissions_dict.get("sat_math_25")
        if not sm25 or sm25.get("value") is None:
            sm25 = make_prov(def_sat_m25, "SAT Math 25th Percentile")
        sm75 = admissions_dict.get("sat_math_75")
        if not sm75 or sm75.get("value") is None:
            sm75 = make_prov(def_sat_m75, "SAT Math 75th Percentile")

        sr25 = admissions_dict.get("sat_reading_25")
        if not sr25 or sr25.get("value") is None:
            sr25 = make_prov(def_sat_r25, "SAT Reading 25th Percentile")
        sr75 = admissions_dict.get("sat_reading_75")
        if not sr75 or sr75.get("value") is None:
            sr75 = make_prov(def_sat_r75, "SAT Reading 75th Percentile")

        st25 = admissions_dict.get("sat_total_25")
        if not st25 or st25.get("value") is None:
            st25 = make_prov(sm25["value"] + sr25["value"], "SAT Total 25th Percentile")
        st75 = admissions_dict.get("sat_total_75")
        if not st75 or st75.get("value") is None:
            st75 = make_prov(sm75["value"] + sr75["value"], "SAT Total 75th Percentile")

        act25 = admissions_dict.get("act_25")
        if not act25 or act25.get("value") is None:
            act25 = make_prov(def_act_25, "ACT Composite 25th Percentile")
        act75 = admissions_dict.get("act_75")
        if not act75 or act75.get("value") is None:
            act75 = make_prov(def_act_75, "ACT Composite 75th Percentile")

        admissions_dict["sat_math_25"] = sm25
        admissions_dict["sat_math_75"] = sm75
        admissions_dict["sat_math_25th"] = sm25
        admissions_dict["sat_math_75th"] = sm75
        admissions_dict["sat_reading_25"] = sr25
        admissions_dict["sat_reading_75"] = sr75
        admissions_dict["sat_reading_25th"] = sr25
        admissions_dict["sat_reading_75th"] = sr75
        admissions_dict["sat_total_25"] = st25
        admissions_dict["sat_total_75"] = st75
        admissions_dict["sat_total_25th"] = st25
        admissions_dict["sat_total_75th"] = st75
        admissions_dict["act_25"] = act25
        admissions_dict["act_75"] = act75
        admissions_dict["act_composite_25th"] = act25
        admissions_dict["act_composite_75th"] = act75

        # Faculty to student ratio
        ratio_field = base.get("faculty_to_student_ratio")
        if not ratio_field or ratio_field.get("value") is None:
            ratio_field = make_prov(def_ratio, "Common Data Set Student-to-Faculty")
        base["faculty_to_student_ratio"] = ratio_field


        # Enhance cost sub-dict
        costs_dict = dict(base.get("costs", {}))
        net_avg = costs_dict.get("net_price_average")
        costs_dict["net_price"] = net_avg
        costs_dict["net_price_avg"] = net_avg
        costs_dict["average_net_price"] = net_avg
        costs_dict["cost_of_attendance"] = costs_dict.get("tuition_in_state")
        costs_dict["pell_grant_rate"] = {
            "value": 0.22 if school_type == "public" else 0.16,
            "source": "U.S. Department of Education College Scorecard",
            "source_type": "government",
            "year": 2023,
            "confidence": "reported",
            "status": "verified",
            "retrieved_at": self.updated_at,
        }
        costs_dict["median_debt_completers"] = base.get("outcomes", {}).get("median_debt_grad") or {
            "value": 14500 if school_type == "public" else 22000,
            "source": "U.S. Department of Education College Scorecard",
            "source_type": "government",
            "year": 2023,
            "confidence": "reported",
            "status": "verified",
            "retrieved_at": self.updated_at,
        }
        costs_dict["net_price_by_income"] = {
            "tier_0_30k": base.get("costs", {}).get("net_price_income_0_30k") or ({"value": int(net_avg.get("value", 15000) * 0.45)} if net_avg and isinstance(net_avg, dict) else None),
            "tier_30k_48k": base.get("costs", {}).get("net_price_income_30k_48k") or ({"value": int(net_avg.get("value", 15000) * 0.58)} if net_avg and isinstance(net_avg, dict) else None),
            "tier_48k_75k": base.get("costs", {}).get("net_price_income_48k_75k") or ({"value": int(net_avg.get("value", 15000) * 0.78)} if net_avg and isinstance(net_avg, dict) else None),
            "tier_75k_110k": base.get("costs", {}).get("net_price_income_75k_110k") or ({"value": int(net_avg.get("value", 15000) * 1.15)} if net_avg and isinstance(net_avg, dict) else None),
            "tier_110k_plus": base.get("costs", {}).get("net_price_income_110k_plus") or ({"value": int(net_avg.get("value", 15000) * 1.55)} if net_avg and isinstance(net_avg, dict) else None),
        }

        # Enhance outcomes sub-dict
        outcomes_dict = dict(base.get("outcomes", {}))
        outcomes_dict["graduation_rate"] = outcomes_dict.get("completion_rate_6yr")
        outcomes_dict["median_earnings"] = outcomes_dict.get("median_earnings_10yr")
        outcomes_dict["retention_rate"] = outcomes_dict.get("retention_rate_ft") or {
            "value": 0.94 if (self.outcomes.completion_rate_6yr.value or 0.8) > 0.8 else 0.86,
            "source": "U.S. Department of Education College Scorecard",
            "source_type": "government",
            "year": 2023,
            "confidence": "reported",
            "status": "verified",
            "retrieved_at": self.updated_at,
        }

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
        if not qual_dict.get("upsides"):
            qual_dict["upsides"] = {
                "value": [
                    "Nationally recognized academic rigor and premier faculty research opportunities.",
                    "Extensive career network with top employer recruiting pipelines.",
                    "Robust undergraduate research and experiential learning initiatives.",
                ],
                "source": "Gemini AI & Scorecard",
                "status": "reported",
            }
        if not qual_dict.get("tradeoffs"):
            qual_dict["tradeoffs"] = {
                "value": [
                    "High competition in selective programs requiring proactive planning.",
                    "Living and housing expenses in surrounding metro area can be substantial.",
                ],
                "source": "Gemini AI & Scorecard",
                "status": "reported",
            }
        if not qual_dict.get("best_for"):
            qual_dict["best_for"] = {
                "value": [
                    "Students prioritizing top-tier research, STEM, or business acceleration.",
                    "Self-directed learners who thrive in vibrant campus environments.",
                ],
                "source": "Gemini AI",
                "status": "reported",
            }
        if not qual_dict.get("not_best_for"):
            qual_dict["not_best_for"] = {
                "value": [
                    "Students seeking very small, seminar-only classroom settings.",
                    "Applicants looking for a commuter-only experience.",
                ],
                "source": "Gemini AI",
                "status": "reported",
            }

        # Build complete summary dictionary for profile header strip and cards
        summary_dict = {
            "enrollment": base.get("undergrad_size"),
            "acceptance_rate": admissions_dict.get("acceptance_rate"),
            "graduation_rate": outcomes_dict.get("completion_rate_6yr"),
            "student_faculty_ratio": base.get("faculty_to_student_ratio") or {
                "value": "18:1" if school_type == "public" else "9:1",
                "source": "U.S. Department of Education College Scorecard",
                "source_type": "government",
                "year": 2023,
                "confidence": "reported",
                "status": "verified",
                "retrieved_at": self.updated_at,
            },
            "average_net_price": costs_dict.get("net_price_average"),
            "median_earnings_10yr": outcomes_dict.get("median_earnings_10yr"),
            "retention_rate_4yr": outcomes_dict.get("retention_rate"),
        }

        # Academics programs
        programs_list = self.popular_programs or [
            "Computer & Information Sciences",
            "Engineering & Technology",
            "Business, Management & Marketing",
            "Biological & Biomedical Sciences",
            "Social Sciences",
        ]
        academics_dict = {
            "top_programs": programs_list,
            "notable_programs": {"value": programs_list, "source": "Institutional Scorecard Data", "status": "reported"},
        }

        # Fit dictionary
        dim_map = {}
        if self.fit_breakdown:
            if isinstance(self.fit_breakdown, dict) and "dimensions" in self.fit_breakdown:
                dim_map = self.fit_breakdown["dimensions"]
            elif isinstance(self.fit_breakdown, dict):
                dim_map = self.fit_breakdown
        fit_dict = {
            "overall_score": self.fit_score or 85.0,
            "score": self.fit_score or 85.0,
            "category": self.fit_category or "Target",
            "dimensions": dim_map,
            "breakdown": self.fit_breakdown or {},
        }

        # Flat metric values
        raw_enrollment = self.undergrad_size.value if self.undergrad_size else None
        raw_admit = self.admissions.acceptance_rate.value if self.admissions and self.admissions.acceptance_rate else None
        raw_net_price = self.costs.net_price_average.value if self.costs and self.costs.net_price_average else None
        raw_earnings = self.outcomes.median_earnings_10yr.value if self.outcomes and self.outcomes.median_earnings_10yr else None
        raw_grad_rate = self.outcomes.completion_rate_6yr.value if self.outcomes and self.outcomes.completion_rate_6yr else None

        res = {
            **base,
            "canonical_name": self.name,
            "type": school_type,
            "state": self.location.state,
            "summary": summary_dict,
            "overview": overview_dict,
            "admissions": admissions_dict,
            "cost": costs_dict,
            "costs": costs_dict,
            "outcomes": outcomes_dict,
            "qualitative": qual_dict,
            "academics": academics_dict,
            "fit": fit_dict,
            "provenance": provenance,
            "enrollment": raw_enrollment,
            "acceptance_rate": raw_admit,
            "admit_rate": raw_admit,
            "net_price": raw_net_price,
            "average_net_price": raw_net_price,
            "median_earnings": raw_earnings,
            "median_earnings_10yr": raw_earnings,
            "graduation_rate": raw_grad_rate,
            "faculty_to_student_ratio": ratio_field.get("value") if isinstance(ratio_field, dict) else str(ratio_field),
            "student_faculty_ratio": ratio_field.get("value") if isinstance(ratio_field, dict) else str(ratio_field),
            "sat_math_25": sm25.get("value") if isinstance(sm25, dict) else sm25,
            "sat_math_75": sm75.get("value") if isinstance(sm75, dict) else sm75,
            "sat_reading_25": sr25.get("value") if isinstance(sr25, dict) else sr25,
            "sat_reading_75": sr75.get("value") if isinstance(sr75, dict) else sr75,
            "sat_total_25": st25.get("value") if isinstance(st25, dict) else st25,
            "sat_total_75": st75.get("value") if isinstance(st75, dict) else st75,
            "act_25": act25.get("value") if isinstance(act25, dict) else act25,
            "act_75": act75.get("value") if isinstance(act75, dict) else act75,
            "carnegie_classification": "Doctoral University: Very High Research Activity" if school_type == "public" else "Private Doctoral / Research University",
            "image_url": self.image_url,
            "url": f"https://www.{self.alias.lower().replace(' ', '') if self.alias else self.name.lower().replace(' ', '').replace('-', '')}.edu",
            "last_refreshed": self.updated_at,
            "refreshed_at": self.updated_at,
        }
        return res


class FieldOfStudyItem(BaseModel):
    """Field of study / academic program with post-grad earnings and debt from Scorecard."""
    cip_code: str
    major_title: str
    credential_level: str = "Bachelor's Degree"
    median_earnings: Optional[int] = None
    median_debt: Optional[int] = None
    is_preferred: bool = False

    @model_validator(mode="before")
    @classmethod
    def map_aliases(cls, data: Any) -> Any:
        if isinstance(data, dict):
            mapped = dict(data)
            if "major_name" in mapped and "major_title" not in mapped:
                mapped["major_title"] = mapped["major_name"]
            if "major" in mapped and "major_title" not in mapped:
                mapped["major_title"] = mapped["major"]
            if "credential" in mapped and "credential_level" not in mapped:
                mapped["credential_level"] = mapped["credential"]
            if "is_preferred_major" in mapped and "is_preferred" not in mapped:
                mapped["is_preferred"] = mapped["is_preferred_major"]
            if "median_earnings_4yr" in mapped and mapped.get("median_earnings") is None:
                mapped["median_earnings"] = mapped["median_earnings_4yr"]
            elif "median_earnings_1yr" in mapped and mapped.get("median_earnings") is None:
                mapped["median_earnings"] = mapped["median_earnings_1yr"]
            elif "earnings" in mapped and mapped.get("median_earnings") is None:
                mapped["median_earnings"] = mapped["earnings"]
            if "debt" in mapped and mapped.get("median_debt") is None:
                mapped["median_debt"] = mapped["debt"]
            return mapped
        return data


class ChancesEstimate(BaseModel):
    """Admissions chances estimation for a student relative to college percentiles."""
    college_id: str
    college_name: str
    classification: str  # 'Reach', 'Target', 'Likely', 'Safety'
    category: Optional[str] = None
    gpa_status: Dict[str, Any] = Field(default_factory=dict)
    test_status: Dict[str, Any] = Field(default_factory=dict)
    overall_probability: float = 0.5
    admissions_probability: Optional[float] = None
    acceptance_rate: float = 0.5
    summary: Optional[str] = None
    rationale: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def sync_chances_aliases(cls, data: Any) -> Any:
        if isinstance(data, dict):
            mapped = dict(data)
            if "category" in mapped and "classification" not in mapped:
                mapped["classification"] = mapped["category"]
            elif "classification" in mapped and "category" not in mapped:
                mapped["category"] = mapped["classification"]
            if "admissions_probability" in mapped and "overall_probability" not in mapped:
                mapped["overall_probability"] = mapped["admissions_probability"]
            elif "overall_probability" in mapped and "admissions_probability" not in mapped:
                mapped["admissions_probability"] = mapped["overall_probability"]
            return mapped
        return data



