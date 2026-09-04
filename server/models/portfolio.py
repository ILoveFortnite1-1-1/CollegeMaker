from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid
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


class ChecklistItem(BaseModel):
    """An individual application requirement checklist item."""
    id: str = Field(default_factory=lambda: f"chk_{uuid.uuid4().hex[:8]}")
    name: str
    required: bool = True
    completed: bool = False
    deadline: Optional[str] = None
    category: Optional[str] = "General"
    notes: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def sync_checklist_aliases(cls, data: Any) -> Any:
        if isinstance(data, dict):
            mapped = dict(data)
            if "title" in mapped and "name" not in mapped:
                mapped["name"] = mapped["title"]
            elif "name" in mapped and "title" not in mapped:
                mapped["title"] = mapped["name"]
            if "due_date" in mapped and "deadline" not in mapped:
                mapped["deadline"] = mapped["due_date"]
            return mapped
        return data


class ApplicationTracker(BaseModel):
    """Tracks application milestones, deadlines, requirements, and decisions derived from tracker template."""
    status: str = "Not Started"  # Not Started, In Progress, Submitted, Decision Received
    plan: str = "Regular Decision"  # Early Action, Early Decision, Early Decision II, Regular Decision, Rolling
    platform: str = "Common App"  # Common App, Coalition App, Institutional Portal, Direct
    priority_deadline: Optional[str] = None  # e.g. "2024-11-01"
    regular_deadline: Optional[str] = None   # e.g. "2025-01-01"
    early_reason: Optional[str] = None
    
    # Deadlines for R2
    fafsa_deadline: Optional[str] = None
    css_profile_deadline: Optional[str] = None
    scholarship_deadlines: Dict[str, str] = Field(default_factory=dict)

    # Checklist requirements for R7
    requirements: List[ChecklistItem] = Field(default_factory=list)
    
    # Checklist items
    research_completed: bool = False
    transcripts_requested: bool = False
    transcripts_submitted: bool = False
    test_scores_sent: bool = False
    has_supplemental_essays: bool = True
    common_app_essay_completed: bool = False
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

    @model_validator(mode="before")
    @classmethod
    def sync_tracker_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            mapped = dict(data)
            if "checklist_items" in mapped and "requirements" not in mapped:
                mapped["requirements"] = mapped["checklist_items"]
            # Handle scholarship_deadlines if passed as a list of dicts
            sd = mapped.get("scholarship_deadlines")
            if isinstance(sd, list):
                sd_dict = {}
                for item in sd:
                    if isinstance(item, dict) and "name" in item and "deadline" in item:
                        sd_dict[item["name"]] = item["deadline"]
                mapped["scholarship_deadlines"] = sd_dict
            return mapped
        return data

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
        d["checklist_items"] = [r.model_dump() if hasattr(r, "model_dump") else r for r in self.requirements]
        return d


class FinancialAidOffer(BaseModel):
    """Detailed breakdown of financial aid and scholarship package for a college."""
    college_id: Optional[str] = None
    merit_aid: int = 0
    need_based_grants: int = 0
    institutional_grants: int = 0
    outside_scholarships: int = 0
    federal_loans: int = 0
    work_study: int = 0
    custom_sticker_price: Optional[int] = None
    notes: Optional[str] = None
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @model_validator(mode="before")
    @classmethod
    def sync_aid_aliases(cls, data: Any) -> Any:
        if isinstance(data, dict):
            mapped = dict(data)
            if "sticker_price_override" in mapped and "custom_sticker_price" not in mapped:
                mapped["custom_sticker_price"] = int(mapped["sticker_price_override"]) if mapped["sticker_price_override"] is not None else None
            elif "custom_sticker_price" in mapped and "sticker_price_override" not in mapped:
                mapped["sticker_price_override"] = mapped["custom_sticker_price"]
            # Support loan aliases (yearly_loan, loans, annual_loans, etc.)
            loan_val = mapped.get("federal_loans")
            for alias in ["yearly_loan", "yearly_loans", "annual_loans", "annual_loan", "loans", "loan", "federal_loan"]:
                if alias in mapped and (loan_val is None or loan_val == 0):
                    loan_val = mapped[alias]
            if loan_val is not None:
                try:
                    mapped["federal_loans"] = int(float(loan_val))
                except (ValueError, TypeError):
                    pass
            return mapped
        return data

    @property
    def total_grants(self) -> int:
        return (
            max(0, int(self.merit_aid or 0))
            + max(0, int(self.need_based_grants or 0))
            + max(0, int(self.institutional_grants or 0))
            + max(0, int(self.outside_scholarships or 0))
        )

    @property
    def total_loans(self) -> int:
        return max(0, int(self.federal_loans or 0))

    @property
    def total_self_help(self) -> int:
        return max(0, int(self.federal_loans or 0)) + max(0, int(self.work_study or 0))

    def calculate_metrics(self, default_sticker_price: int = 25000) -> Dict[str, Any]:
        if self.custom_sticker_price is not None and self.custom_sticker_price > 0:
            sticker = int(self.custom_sticker_price)
        else:
            sticker = max(0, int(default_sticker_price or 25000))
        grants = self.total_grants
        net_annual = max(0, sticker - grants)
        four_year = net_annual * 4
        annual_loan = max(0, int(self.federal_loans or 0))
        annual_work_study = max(0, int(self.work_study or 0))
        total_debt_grad = annual_loan * 4

        # True out-of-pocket cash commitment after scholarships, grants, loans, and work-study
        annual_out_of_pocket = max(0, sticker - grants - annual_loan - annual_work_study)
        four_year_out_of_pocket = annual_out_of_pocket * 4

        # Standard 10-year repayment at 5.5% annual interest
        r = 0.055 / 12.0
        n = 120
        if total_debt_grad > 0:
            monthly_payment = round(total_debt_grad * (r * (1 + r)**n) / ((1 + r)**n - 1), 2)
        else:
            monthly_payment = 0.0

        return {
            "sticker_price": sticker,
            "total_grants": grants,
            "total_self_help": self.total_self_help,
            "net_annual_cost": net_annual,
            "four_year_total_cost": four_year,
            "four_year_cost": four_year,
            "annual_out_of_pocket": annual_out_of_pocket,
            "four_year_out_of_pocket": four_year_out_of_pocket,
            "federal_loans": annual_loan,
            "yearly_loan": annual_loan,
            "total_debt_at_graduation": total_debt_grad,
            "total_debt_grad": total_debt_grad,
            "estimated_monthly_payment": monthly_payment,
            "monthly_loan_payment": monthly_payment,
            "work_study": self.work_study,
        }


class CollegeAidComparison(BaseModel):
    """Comparative financial aid evaluation metrics for a single college."""
    college_id: str
    college_name: str
    has_offer: bool = True
    sticker_price: int = 0
    sticker_price_source: str = "Scorecard"
    total_grants: int = 0
    total_self_help: int = 0
    net_annual_cost: int = 0
    four_year_total_cost: int = 0
    annual_out_of_pocket: int = 0
    four_year_out_of_pocket: int = 0
    federal_loans: int = 0
    total_debt_at_graduation: int = 0
    estimated_monthly_payment: float = 0.0
    monthly_loan_payment: Optional[float] = None
    median_debt_scorecard: Optional[int] = None
    scorecard_monthly_loan_payment: Optional[float] = None
    is_best_value: bool = False
    offer: Optional[FinancialAidOffer] = None
    metrics: Optional[Dict[str, Any]] = None

    @model_validator(mode="before")
    @classmethod
    def sync_comparison_aliases(cls, data: Any) -> Any:
        if isinstance(data, dict):
            mapped = dict(data)
            if "monthly_loan_payment" in mapped and "estimated_monthly_payment" not in mapped:
                mapped["estimated_monthly_payment"] = mapped["monthly_loan_payment"]
            elif "estimated_monthly_payment" in mapped and "monthly_loan_payment" not in mapped:
                mapped["monthly_loan_payment"] = mapped["estimated_monthly_payment"]
            if "four_year_cost" in mapped and "four_year_total_cost" not in mapped:
                mapped["four_year_total_cost"] = mapped["four_year_cost"]
            elif "four_year_total_cost" in mapped and "four_year_cost" not in mapped:
                mapped["four_year_cost"] = mapped["four_year_total_cost"]
            if "yearly_loan" in mapped and "federal_loans" not in mapped:
                mapped["federal_loans"] = mapped["yearly_loan"]
            return mapped
        return data


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
    aid_offer: Optional[FinancialAidOffer] = None


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
            "aid_offer": self.aid_offer.model_dump() if hasattr(self, "aid_offer") and self.aid_offer else None,
        }


class EssayEntry(BaseModel):
    """Essay tracker entry for tracking prompts, word limits, drafts, and reuse across colleges.
    Explicitly distinguishes between college-specific supplemental essays and the generic Common App essay.
    """
    id: str = Field(default_factory=lambda: f"essay_{uuid.uuid4().hex[:8]}")
    title: Optional[str] = "Untitled Essay"
    prompt: str
    essay_type: str = "Supplemental"  # 'Supplemental' | 'Common App'
    is_common_app: bool = False
    word_limit: Optional[int] = None
    current_word_count: int = 0
    draft_status: str = "Not Started"  # 'Not Started' | 'Drafting' | 'Reviewing' | 'Final'
    colleges: List[str] = Field(default_factory=list)
    content: Optional[str] = ""
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @model_validator(mode="before")
    @classmethod
    def sync_essay_aliases(cls, data: Any) -> Any:
        if isinstance(data, dict):
            mapped = dict(data)
            if "word_count" in mapped and "current_word_count" not in mapped:
                mapped["current_word_count"] = mapped["word_count"]
            elif "current_word_count" in mapped and "word_count" not in mapped:
                mapped["word_count"] = mapped["current_word_count"]
            if "status" in mapped and "draft_status" not in mapped:
                mapped["draft_status"] = mapped["status"]
            elif "draft_status" in mapped and "status" not in mapped:
                mapped["status"] = mapped["draft_status"]
            if "college_ids" in mapped and "colleges" not in mapped:
                mapped["colleges"] = mapped["college_ids"]
            elif "colleges" in mapped and "college_ids" not in mapped:
                mapped["college_ids"] = mapped["colleges"]
            if "is_common_app_main" in mapped and "is_common_app" not in mapped:
                mapped["is_common_app"] = mapped["is_common_app_main"]
            if mapped.get("is_common_app") or mapped.get("is_common_app_main"):
                mapped["is_common_app"] = True
                mapped["essay_type"] = "Common App"
            elif mapped.get("essay_type") in ["Common App", "common_app", "commonapp", "Personal Statement"]:
                mapped["is_common_app"] = True
                mapped["essay_type"] = "Common App"
            elif "essay_type" not in mapped:
                mapped["essay_type"] = "Supplemental"
                mapped["is_common_app"] = False
            return mapped
        return data

    @property
    def reuse_count(self) -> int:
        return len(self.colleges)

    def to_dict(self) -> dict:
        d = self.model_dump()
        d["reuse_count"] = self.reuse_count
        d["status"] = self.draft_status
        d["word_count"] = self.current_word_count
        d["college_ids"] = self.colleges
        d["is_common_app"] = self.is_common_app
        d["essay_type"] = self.essay_type
        return d



class ScenarioOverrideRequest(BaseModel):
    """Scenario simulation overrides without persisting."""
    college_id: Optional[str] = None
    hypothetical_major: Optional[str] = None
    is_in_state: Optional[bool] = None
    annual_aid_amount: Optional[int] = None
    annual_loan_amount: Optional[int] = None
    budget_max_annual: Optional[int] = None
    gpa: Optional[float] = None
    sat_score: Optional[int] = None
    act_score: Optional[int] = None

    @model_validator(mode="before")
    @classmethod
    def sync_scenario_aliases(cls, data: Any) -> Any:
        if isinstance(data, dict):
            mapped = dict(data)
            if "major" in mapped and "hypothetical_major" not in mapped:
                mapped["hypothetical_major"] = mapped["major"]
            elif "hypothetical_major" in mapped and "major" not in mapped:
                mapped["major"] = mapped["hypothetical_major"]
            if "in_state" in mapped and "is_in_state" not in mapped:
                mapped["is_in_state"] = mapped["in_state"]
            elif "is_in_state" in mapped and "in_state" not in mapped:
                mapped["in_state"] = mapped["is_in_state"]
            if "residency" in mapped:
                if mapped["residency"] == "in_state":
                    mapped["is_in_state"] = True
                elif mapped["residency"] == "out_of_state":
                    mapped["is_in_state"] = False
            if "aid_amount" in mapped and "annual_aid_amount" not in mapped:
                mapped["annual_aid_amount"] = mapped["aid_amount"]
            elif "annual_aid_amount" in mapped and "aid_amount" not in mapped:
                mapped["aid_amount"] = mapped["annual_aid_amount"]
            if "budget" in mapped and "budget_max_annual" not in mapped:
                mapped["budget_max_annual"] = mapped["budget"]
            elif "budget_max_annual" in mapped and "budget" not in mapped:
                mapped["budget"] = mapped["budget_max_annual"]
            # Loan aliases
            loan_val = mapped.get("annual_loan_amount")
            for alias in ["yearly_loan", "yearly_loans", "annual_loans", "annual_loan", "loans", "loan", "loan_amount"]:
                if alias in mapped and (loan_val is None or loan_val == 0):
                    loan_val = mapped[alias]
            if loan_val is not None:
                try:
                    mapped["annual_loan_amount"] = int(float(loan_val))
                except (ValueError, TypeError):
                    pass
            return mapped
        return data


class ScenarioResult(BaseModel):
    """Comparative fit and cost result of what-if simulation."""
    college_id: str
    college_name: str
    baseline_fit_score: float
    what_if_fit_score: float
    fit_score_delta: float
    baseline_category: str
    what_if_category: str
    baseline_net_price: int
    what_if_net_price: int
    net_price_delta: int
    annual_loan_amount: Optional[int] = 0
    what_if_out_of_pocket: Optional[int] = None
    total_debt_at_graduation: Optional[int] = 0
    estimated_monthly_payment: Optional[float] = 0.0
    median_debt_scorecard: Optional[int] = None
    scorecard_monthly_loan_payment: Optional[float] = None
    dimension_deltas: Dict[str, float] = Field(default_factory=dict)
    baseline: Optional[Dict[str, Any]] = None
    scenario: Optional[Dict[str, Any]] = None
    delta: Optional[Dict[str, Any]] = None


class StudentPortfolio(BaseModel):
    """Complete guest portfolio stored server-side for a session ID."""
    portfolio_id: str
    colleges: List[PortfolioItem] = Field(default_factory=list)
    preferences: StudentPreferences = Field(default_factory=StudentPreferences)
    aid_offers: Dict[str, FinancialAidOffer] = Field(default_factory=dict)
    essays: List[EssayEntry] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


Portfolio = StudentPortfolio



class PortfolioSummary(BaseModel):
    """High-level metrics for dashboard visualization."""
    total_colleges: int = 0
    reach_count: int = 0
    target_count: int = 0
    likely_count: int = 0
    average_net_price: Optional[int] = None
    average_acceptance_rate: Optional[float] = None
    average_median_earnings: Optional[int] = None

