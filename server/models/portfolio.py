from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, model_validator
from server.models.canonical import CanonicalCollege, ConfidenceLevel


class FitWeights(BaseModel):
    """Customizable 8-dimension fit weights (standard base sums to 100 or 1.0)."""
    career: float = 25.0
    roi: float = 20.0
    academic: float = 15.0
    admissions: float = 10.0
    experience: float = 10.0
    strength: float = 10.0
    location: float = 5.0
    cost: float = 5.0

    @model_validator(mode="before")
    @classmethod
    def map_aliases(cls, data: Any) -> Any:
        if isinstance(data, dict):
            mapped = dict(data)
            if "career_outcomes" in mapped:
                mapped["career"] = mapped.pop("career_outcomes")
            if "roi_value" in mapped:
                mapped["roi"] = mapped.pop("roi_value")
            if "academic_fit" in mapped:
                mapped["academic"] = mapped.pop("academic_fit")
            if "admissions_fit" in mapped:
                mapped["admissions"] = mapped.pop("admissions_fit")
            if "student_experience" in mapped:
                mapped["experience"] = mapped.pop("student_experience")
            if "academic_strength" in mapped:
                mapped["strength"] = mapped.pop("academic_strength")
            return mapped
        return data

    def normalized(self, available_dimensions: Optional[List[str]] = None) -> Dict[str, float]:
        """Normalize weights to sum to 1.0, optionally filtering by available dimensions."""
        all_weights = {
            "career": max(0.0, float(self.career)),
            "roi": max(0.0, float(self.roi)),
            "academic": max(0.0, float(self.academic)),
            "admissions": max(0.0, float(self.admissions)),
            "experience": max(0.0, float(self.experience)),
            "strength": max(0.0, float(self.strength)),
            "location": max(0.0, float(self.location)),
            "cost": max(0.0, float(self.cost)),
        }
        
        if available_dimensions is not None:
            active_weights = {k: v for k, v in all_weights.items() if k in available_dimensions}
        else:
            active_weights = all_weights
            
        total = sum(active_weights.values())
        if total <= 0:
            n = len(active_weights) or 1
            return {k: 1.0 / n for k in active_weights}
        return {k: v / total for k, v in active_weights.items()}


class StudentPreferences(BaseModel):
    """Student profile and priority preferences."""
    gpa: Optional[float] = None
    sat_score: Optional[int] = None
    sat: Optional[int] = None
    act_score: Optional[int] = None
    home_state: Optional[str] = None
    budget_max_annual: Optional[int] = None
    budget: Optional[int] = None
    family_income_bracket: Optional[str] = None  # e.g. "0_30k", "30k_48k", "48k_75k", "75k_110k", "110k_plus"
    preferred_majors: List[str] = Field(default_factory=list)
    target_majors: Optional[List[str]] = None
    preferred_location_types: List[str] = Field(default_factory=list)  # Urban, Suburban, Rural, Town
    preferred_regions: List[str] = Field(default_factory=list)
    preferred_control: Optional[str] = None  # public, private_nonprofit, any
    weights: FitWeights = Field(default_factory=FitWeights)

    @model_validator(mode="before")
    @classmethod
    def sync_aliases(cls, data: Any) -> Any:
        if isinstance(data, dict):
            mapped = dict(data)
            if "sat" in mapped and "sat_score" not in mapped:
                mapped["sat_score"] = mapped["sat"]
            elif "sat_score" in mapped and "sat" not in mapped:
                mapped["sat"] = mapped["sat_score"]
            if "budget" in mapped and "budget_max_annual" not in mapped:
                mapped["budget_max_annual"] = mapped["budget"]
            elif "budget_max_annual" in mapped and "budget" not in mapped:
                mapped["budget"] = mapped["budget_max_annual"]
            if "target_majors" in mapped and "preferred_majors" not in mapped:
                mapped["preferred_majors"] = mapped["target_majors"]
            elif "preferred_majors" in mapped and "target_majors" not in mapped:
                mapped["target_majors"] = mapped["preferred_majors"]
            return mapped
        return data


class FitDimensionScore(BaseModel):
    """Score and rationale for a single fit dimension."""
    dimension: str
    raw_score: float  # 0 to 100
    weight: float     # 0.0 to 1.0 normalized
    weighted_score: float
    confidence: ConfidenceLevel = ConfidenceLevel.CALCULATED
    rationale: str


class FitAnalysis(BaseModel):
    """Comprehensive fit evaluation result for a college & student profile."""
    overall_score: float  # 0 to 100
    category: str         # Reach, Target, Likely
    admissions_probability: float  # 0.0 to 1.0
    dimensions: List[FitDimensionScore]
    normalized_weights_used: Dict[str, float]

    def to_breakdown_dict(self) -> Dict[str, Any]:
        """Convert dimension list into a direct map keyed by dimension names and aliases."""
        res = {}
        for dim in self.dimensions:
            dim_dict = {
                "score": dim.raw_score,
                "raw_score": dim.raw_score,
                "weighted_score": dim.weighted_score,
                "weight": dim.weight,
                "rationale": dim.rationale,
                "confidence": dim.confidence.value,
            }
            res[dim.dimension] = dim_dict
            # Add common alias mappings
            if dim.dimension == "career":
                res["career_outcomes"] = dim_dict
            elif dim.dimension == "roi":
                res["roi_value"] = dim_dict
            elif dim.dimension == "academic":
                res["academic_fit"] = dim_dict
            elif dim.dimension == "admissions":
                res["admissions_fit"] = dim_dict
            elif dim.dimension == "experience":
                res["student_experience"] = dim_dict
            elif dim.dimension == "strength":
                res["academic_strength"] = dim_dict
        return res


class ApplicationTracker(BaseModel):
    """Tracks application milestones, deadlines, requirements, and decisions derived from tracker template."""
    status: str = "Not Started"  # Not Started, In Progress, Submitted, Decision Received
    plan: str = "Regular Decision"  # Early Action, Early Decision, Early Decision II, Regular Decision, Rolling
    platform: str = "Common App"  # Common App, Coalition App, Institutional Portal, Direct
    priority_deadline: Optional[str] = None  # e.g. "2024-11-01"
    regular_deadline: Optional[str] = None   # e.g. "2025-01-01"
    early_reason: Optional[str] = None
    
    # Checklist items
    research_completed: bool = False
    transcripts_requested: bool = False
    transcripts_submitted: bool = False
    test_scores_sent: bool = False
    has_supplemental_essays: bool = True
    essays_completed: bool = False
    counselor_rec_requested: bool = False
    teacher_rec_requested: bool = False
    application_fee_paid: bool = False
    application_submitted: bool = False
    portal_account_checked: bool = False
    financial_aid_submitted: bool = False
    
    # Decision
    decision: str = "Pending"  # Pending, Accepted, Deferred, Waitlisted, Denied
    decision_date: Optional[str] = None
    notes: Optional[str] = None

    def calculate_completion_percentage(self) -> int:
        """Calculate percentage of application progress."""
        core_items = [
            self.research_completed,
            self.transcripts_requested,
            self.transcripts_submitted,
            self.test_scores_sent,
            self.essays_completed,
            self.counselor_rec_requested,
            self.teacher_rec_requested,
            self.application_fee_paid,
            self.application_submitted,
            self.portal_account_checked,
            self.financial_aid_submitted,
        ]
        completed = sum(1 for item in core_items if item)
        return int((completed / len(core_items)) * 100)

    def to_dict(self) -> dict:
        d = self.model_dump()
        d["completion_percentage"] = self.calculate_completion_percentage()
        return d


class PortfolioItem(BaseModel):
    """A saved college entry in the student's portfolio."""
    college_id: str
    college_name: str
    id: Optional[str] = None
    canonical_name: Optional[str] = None
    added_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    notes: Optional[str] = None
    tag: Optional[str] = None
    custom_label: Optional[str] = None
    category_override: Optional[str] = None
    college: Optional[CanonicalCollege] = None
    fit_score: Optional[float] = None
    fit_category: Optional[str] = None
    fit_breakdown: Optional[dict] = None
    tracker: ApplicationTracker = Field(default_factory=ApplicationTracker)

    def to_api_dict(self) -> dict:
        cid = self.id or self.college_id
        cname = self.canonical_name or self.college_name
        tag_val = self.tag or self.category_override or self.fit_category or "Target"
        bd = self.fit_breakdown
        if not bd and self.college:
            bd = self.college.fit_breakdown
        if not bd:
            from server.services.fit_scorer import fit_scorer
            if self.college:
                fit_res = fit_scorer.evaluate_college_fit(self.college, None)
                bd = fit_res.to_breakdown_dict()
        score_val = self.fit_score if self.fit_score is not None else 85.0
        fit_score_dict = {
            "overall": score_val,
            "score": score_val,
            "category": self.fit_category or tag_val,
            "breakdown": bd or {},
        }
        # Extract flat metrics for direct frontend & dashboard use
        net_price = None
        admit_rate = None
        median_earnings = None
        loc_str = None
        school_type = "public"
        
        if self.college:
            if self.college.costs and self.college.costs.net_price_average:
                net_price = self.college.costs.net_price_average.value
            if self.college.admissions and self.college.admissions.acceptance_rate:
                admit_rate = self.college.admissions.acceptance_rate.value
            if self.college.outcomes and self.college.outcomes.median_earnings_10yr:
                median_earnings = self.college.outcomes.median_earnings_10yr.value
            if self.college.location:
                loc_str = f"{self.college.location.city}, {self.college.location.state}"
            school_type = "private" if "private" in self.college.control.lower() else "public"

        return {
            "id": cid,
            "college_id": cid,
            "name": cname,
            "canonical_name": cname,
            "college_name": cname,
            "added_at": self.added_at,
            "notes": self.notes,
            "user_note": self.notes or "",
            "tag": tag_val,
            "category": self.fit_category or tag_val,
            "custom_label": self.custom_label,
            "category_override": self.category_override,
            "fit_score": fit_score_dict,
            "composite_score": score_val,
            "fit_category": self.fit_category or tag_val,
            "fit_breakdown": bd or {},
            "net_price": net_price,
            "average_net_price": net_price,
            "admit_rate": admit_rate,
            "acceptance_rate": admit_rate,
            "median_earnings": median_earnings,
            "median_earnings_10yr": median_earnings,
            "location": loc_str,
            "type": school_type,
            "tracker": (self.tracker if hasattr(self, "tracker") and self.tracker else ApplicationTracker()).to_dict(),
            "application_tracker": (self.tracker if hasattr(self, "tracker") and self.tracker else ApplicationTracker()).to_dict(),
            "college": self.college.to_api_dict() if self.college else None,
        }


class StudentPortfolio(BaseModel):
    """Complete guest portfolio stored server-side for a session ID."""
    portfolio_id: str
    colleges: List[PortfolioItem] = Field(default_factory=list)
    preferences: StudentPreferences = Field(default_factory=StudentPreferences)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class PortfolioSummary(BaseModel):
    """High-level metrics for dashboard visualization."""
    total_colleges: int = 0
    reach_count: int = 0
    target_count: int = 0
    likely_count: int = 0
    average_net_price: Optional[int] = None
    average_acceptance_rate: Optional[float] = None
    average_median_earnings: Optional[int] = None

