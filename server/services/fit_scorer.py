"""8-Dimension Student-Customizable Fit Scoring Algorithm."""
from typing import Any, Dict, List, Optional, Tuple
from server.models.canonical import CanonicalCollege, ConfidenceLevel
from server.models.portfolio import (
    FitAnalysis,
    FitDimensionScore,
    FitWeights,
    StudentPreferences,
)


def _get_metric_val(field: Any, default: Any = None) -> Any:
    """Safely extract a numerical or scalar value from a MetricField or raw value."""
    if field is None:
        return default
    if hasattr(field, "value"):
        val = getattr(field, "value")
        return val if val is not None else default
    return field if field is not None else default


class FitScorerService:
    """Calculates multidimensional student-college fit scores and Reach/Target/Likely classification."""

    def evaluate_college_fit(
        self,
        college: CanonicalCollege,
        preferences: Optional[StudentPreferences] = None,
    ) -> FitAnalysis:
        """Calculate the complete 8-dimension fit evaluation for a college given student preferences."""
        prefs = preferences or StudentPreferences()
        weights = prefs.weights or FitWeights()

        dimension_scores: List[FitDimensionScore] = []
        available_dims: List[str] = []

        # 1. Career (25%)
        career_score, career_rationale = self._score_career(college, prefs)
        dimension_scores.append(
            FitDimensionScore(
                dimension="career",
                raw_score=career_score,
                weight=weights.career,
                weighted_score=0.0,
                confidence=ConfidenceLevel.CALCULATED,
                rationale=career_rationale,
            )
        )
        available_dims.append("career")

        # 2. ROI (20%)
        roi_score, roi_rationale = self._score_roi(college, prefs)
        dimension_scores.append(
            FitDimensionScore(
                dimension="roi",
                raw_score=roi_score,
                weight=weights.roi,
                weighted_score=0.0,
                confidence=ConfidenceLevel.CALCULATED,
                rationale=roi_rationale,
            )
        )
        available_dims.append("roi")

        # 3. Academic (15%)
        acad_score, acad_rationale = self._score_academic(college, prefs)
        dimension_scores.append(
            FitDimensionScore(
                dimension="academic",
                raw_score=acad_score,
                weight=weights.academic,
                weighted_score=0.0,
                confidence=ConfidenceLevel.CALCULATED,
                rationale=acad_rationale,
            )
        )
        available_dims.append("academic")

        # 4. Admissions Feasibility (10%)
        admit_score, admit_rationale = self._score_admissions(college, prefs)
        dimension_scores.append(
            FitDimensionScore(
                dimension="admissions",
                raw_score=admit_score,
                weight=weights.admissions,
                weighted_score=0.0,
                confidence=ConfidenceLevel.CALCULATED,
                rationale=admit_rationale,
            )
        )
        available_dims.append("admissions")

        # 5. Campus Experience (10%)
        exp_score, exp_rationale = self._score_experience(college, prefs)
        dimension_scores.append(
            FitDimensionScore(
                dimension="experience",
                raw_score=exp_score,
                weight=weights.experience,
                weighted_score=0.0,
                confidence=ConfidenceLevel.CALCULATED,
                rationale=exp_rationale,
            )
        )
        available_dims.append("experience")

        # 6. Academic Strength / Major Match (10%)
        strength_score, strength_rationale = self._score_strength(college, prefs)
        dimension_scores.append(
            FitDimensionScore(
                dimension="strength",
                raw_score=strength_score,
                weight=weights.strength,
                weighted_score=0.0,
                confidence=ConfidenceLevel.CALCULATED,
                rationale=strength_rationale,
            )
        )
        available_dims.append("strength")

        # 7. Location (5%)
        loc_score, loc_rationale = self._score_location(college, prefs)
        dimension_scores.append(
            FitDimensionScore(
                dimension="location",
                raw_score=loc_score,
                weight=weights.location,
                weighted_score=0.0,
                confidence=ConfidenceLevel.CALCULATED,
                rationale=loc_rationale,
            )
        )
        available_dims.append("location")

        # 8. Cost & Affordability (5%)
        cost_score, cost_rationale = self._score_cost(college, prefs)
        dimension_scores.append(
            FitDimensionScore(
                dimension="cost",
                raw_score=cost_score,
                weight=weights.cost,
                weighted_score=0.0,
                confidence=ConfidenceLevel.CALCULATED,
                rationale=cost_rationale,
            )
        )
        available_dims.append("cost")

        # Normalize weights across all 8 dimensions
        norm_weights = weights.normalized(available_dims)
        overall_score = 0.0

        for dim in dimension_scores:
            w = norm_weights.get(dim.dimension, 0.0)
            dim.weight = round(w, 4)
            dim.weighted_score = round(dim.raw_score * w, 2)
            overall_score += dim.weighted_score

        overall_score = min(100.0, max(0.0, round(overall_score, 1)))

        # Determine Category (Reach, Target, Likely) and Admissions Probability
        category, prob = self._classify_category(college, prefs)

        return FitAnalysis(
            overall_score=overall_score,
            category=category,
            admissions_probability=prob,
            dimensions=dimension_scores,
            normalized_weights_used=norm_weights,
        )

    def calculate_fit(
        self,
        college: CanonicalCollege,
        preferences: Optional[StudentPreferences] = None,
    ) -> FitAnalysis:
        """Calculate fit evaluation for a college (alias for evaluate_college_fit)."""
        return self.evaluate_college_fit(college, preferences)

    def categorize_college(
        self,
        college: CanonicalCollege,
        preferences: Optional[StudentPreferences] = None,
    ) -> Tuple[str, float]:
        """Categorize college as Reach/Target/Likely (alias for _classify_category)."""
        prefs = preferences or StudentPreferences()
        return self._classify_category(college, prefs)

    def _score_career(self, college: CanonicalCollege, prefs: StudentPreferences) -> Tuple[float, str]:
        """Score based on post-grad 10-year earnings ($50k - $120k baseline)."""
        outcomes = getattr(college, "outcomes", None)
        field = getattr(outcomes, "median_earnings_10yr", None) if outcomes else None
        earnings = _get_metric_val(field, default=70000)
        if earnings is None:
            earnings = 70000

        earnings = float(earnings)
        # Map $45k to 50pts, $75k to 80pts, $115k+ to 98pts
        if earnings >= 115000:
            score = 98.0
        elif earnings >= 90000:
            score = 88.0 + (earnings - 90000.0) / 25000.0 * 10.0
        elif earnings >= 70000:
            score = 75.0 + (earnings - 70000.0) / 20000.0 * 13.0
        elif earnings >= 50000:
            score = 60.0 + (earnings - 50000.0) / 20000.0 * 15.0
        else:
            score = max(40.0, (earnings / 50000.0) * 60.0)

        score = min(100.0, max(0.0, score))
        rationale = f"Median 10-year alumni earnings of ${int(earnings):,} places it in the upper quartile nationally."
        return round(score, 1), rationale

    def _score_roi(self, college: CanonicalCollege, prefs: StudentPreferences) -> Tuple[float, str]:
        """Score based on earnings to net price ratio."""
        outcomes = getattr(college, "outcomes", None)
        costs = getattr(college, "costs", None)
        earnings_field = getattr(outcomes, "median_earnings_10yr", None) if outcomes else None
        net_price_field = getattr(costs, "net_price_average", None) if costs else None

        earnings = _get_metric_val(earnings_field, default=75000)
        net_price = _get_metric_val(net_price_field, default=22000)
        if earnings is None:
            earnings = 75000
        if net_price is None:
            net_price = 22000

        earnings = float(earnings)
        net_price = float(net_price)
        ratio = earnings / max(1000.0, net_price)

        # Ratio >= 5.0 -> 98, 4.0 -> 90, 3.0 -> 80, 2.0 -> 65, 1.0 -> 50
        if ratio >= 5.0:
            score = 98.0
        elif ratio >= 3.5:
            score = 85.0 + (ratio - 3.5) / 1.5 * 13.0
        elif ratio >= 2.0:
            score = 65.0 + (ratio - 2.0) / 1.5 * 20.0
        else:
            score = max(35.0, ratio * 32.5)

        score = min(100.0, max(0.0, score))
        rationale = f"Strong financial return with an earnings-to-annual-net-price multiplier of {ratio:.1f}x."
        return round(score, 1), rationale

    def _score_academic(self, college: CanonicalCollege, prefs: StudentPreferences) -> Tuple[float, str]:
        """Score academic rigor and student profile match."""
        outcomes = getattr(college, "outcomes", None)
        admissions = getattr(college, "admissions", None)
        comp_field = getattr(outcomes, "completion_rate_6yr", None) if outcomes else None
        comp_rate = _get_metric_val(comp_field, default=0.85)
        if comp_rate is None:
            comp_rate = 0.85

        comp_rate = float(comp_rate)
        score = comp_rate * 100.0

        # Adjust based on student SAT/GPA if present
        sat_score = getattr(prefs, "sat_score", None) or getattr(prefs, "sat", None) if prefs else None
        if sat_score and admissions:
            sat25_field = getattr(admissions, "sat_total_25", None)
            sat75_field = getattr(admissions, "sat_total_75", None)
            sat25 = _get_metric_val(sat25_field, default=None)
            sat75 = _get_metric_val(sat75_field, default=None)

            if sat25 is not None and sat75 is not None:
                sat25 = float(sat25)
                sat75 = float(sat75)
                sat_score_f = float(sat_score)
                if sat_score_f >= sat75:
                    score = min(100.0, score + 8.0)
                elif sat_score_f >= sat25:
                    score = min(100.0, score + 4.0)
                else:
                    score = max(40.0, score - 8.0)

        score = min(100.0, max(0.0, score))
        rationale = f"6-year graduation rate is {int(comp_rate * 100)}% with high student retention."
        return round(score, 1), rationale

    def _score_admissions(self, college: CanonicalCollege, prefs: StudentPreferences) -> Tuple[float, str]:
        """Score admissions feasibility."""
        admissions = getattr(college, "admissions", None)
        admit_field = getattr(admissions, "acceptance_rate", None) if admissions else None
        admit_rate = _get_metric_val(admit_field, default=0.20)
        if admit_rate is None:
            admit_rate = 0.20

        admit_rate = min(1.0, max(0.0, float(admit_rate)))

        if admit_rate > 0.65:
            score = 92.0
            rationale = f"High accessibility with an acceptance rate of {int(admit_rate * 100)}%."
        elif admit_rate >= 0.40:
            score = 80.0
            rationale = f"Accessible admissions with a {int(admit_rate * 100)}% acceptance rate."
        elif admit_rate >= 0.20:
            score = 68.0
            rationale = f"Competitive selectivity with a {int(admit_rate * 100)}% admission rate."
        elif admit_rate >= 0.10:
            score = 54.0
            rationale = f"Highly selective admissions with a {int(admit_rate * 100)}% acceptance rate."
        else:
            score = 42.0
            rationale = f"Ultra-selective institution with a {admit_rate * 100:.1f}% acceptance rate."

        score = min(100.0, max(0.0, score))
        return round(score, 1), rationale

    def _score_experience(self, college: CanonicalCollege, prefs: StudentPreferences) -> Tuple[float, str]:
        """Score campus culture, size, and retention."""
        outcomes = getattr(college, "outcomes", None)
        retention_field = getattr(outcomes, "retention_rate_ft", None) if outcomes else None
        retention = _get_metric_val(retention_field, default=0.90)
        if retention is None:
            retention = 0.90

        retention = min(1.0, max(0.0, float(retention)))
        if retention >= 0.95:
            score = 95.0
        elif retention >= 0.90:
            score = 86.0
        elif retention >= 0.82:
            score = 75.0
        else:
            score = max(40.0, retention * 80.0)

        rationale = f"First-year retention rate of {int(retention * 100)}% signifies campus community vitality."
        return round(score, 1), rationale

    def _score_strength(self, college: CanonicalCollege, prefs: StudentPreferences) -> Tuple[float, str]:
        """Score program strengths relative to student major interests."""
        if not prefs or not prefs.preferred_majors:
            return 82.0, "Offers comprehensive and nationally recognized degree programs."

        popular_programs = getattr(college, "popular_programs", None) or []
        college_programs = [str(p).lower() for p in popular_programs if p is not None]
        matches = 0
        for major in prefs.preferred_majors:
            if not major:
                continue
            m_lower = str(major).lower()
            if any(m_lower in cp or cp in m_lower for cp in college_programs):
                matches += 1

        if matches > 0:
            score = 95.0
            rationale = f"Top match: {matches} of your preferred majors align directly with signature departments."
        else:
            score = 72.0
            rationale = "Offers strong general academics across broad disciplinary domains."

        score = min(100.0, max(0.0, score))
        return round(score, 1), rationale

    def _score_location(self, college: CanonicalCollege, prefs: StudentPreferences) -> Tuple[float, str]:
        """Score geographic and setting preferences."""
        score = 75.0
        notes = []
        loc = getattr(college, "location", None)
        c_state = getattr(loc, "state", "") if loc else ""
        c_city = getattr(loc, "city", "") if loc else ""
        c_loctype = getattr(loc, "location_type", "") if loc else ""

        if prefs and prefs.home_state and c_state and str(prefs.home_state).upper() == str(c_state).upper():
            score += 15.0
            notes.append(f"In-state institution ({c_state})")

        if prefs and prefs.preferred_location_types and c_loctype:
            if c_loctype in prefs.preferred_location_types:
                score += 10.0
                notes.append(f"Matches desired {c_loctype} setting")
            else:
                score -= 10.0

        score = min(100.0, max(40.0, score))
        loc_str = f"Located in {c_city}, {c_state}." if (c_city and c_state) else "Geographic location preferences evaluated."
        rationale = "; ".join(notes) if notes else loc_str
        return round(score, 1), rationale

    def _score_cost(self, college: CanonicalCollege, prefs: StudentPreferences) -> Tuple[float, str]:
        """Score affordability against student budget."""
        costs = getattr(college, "costs", None)
        net_price_field = getattr(costs, "net_price_average", None) if costs else None
        net_price = _get_metric_val(net_price_field, default=20000)
        if net_price is None:
            net_price = 20000

        # Check for income-bracket-specific net price if student provided it
        if prefs and prefs.family_income_bracket and costs:
            bracket_attr = f"net_price_income_{prefs.family_income_bracket}"
            bracket_field = getattr(costs, bracket_attr, None)
            bracket_val = _get_metric_val(bracket_field, default=None)
            if bracket_val is not None:
                net_price = bracket_val

        net_price = float(net_price)
        budget = getattr(prefs, "budget_max_annual", None) if prefs else None
        if budget is not None and budget > 0:
            budget = float(budget)
            if net_price <= budget:
                score = 96.0
                rationale = f"Annual net price of ${int(net_price):,} is comfortably within your ${int(budget):,} budget."
            else:
                overage = net_price - budget
                pct_over = overage / budget
                score = max(30.0, 90.0 - (pct_over * 70.0))
                rationale = f"Annual net price of ${int(net_price):,} exceeds preferred budget of ${int(budget):,}."
        else:
            # General cost score (lower net price -> higher score)
            if net_price <= 15000:
                score = 95.0
            elif net_price <= 25000:
                score = 85.0
            elif net_price <= 35000:
                score = 75.0
            elif net_price <= 45000:
                score = 62.0
            else:
                score = 50.0
            rationale = f"Average annual net price is ${int(net_price):,} for undergraduate students."

        score = min(100.0, max(0.0, score))
        return round(score, 1), rationale

    def _classify_category(self, college: CanonicalCollege, prefs: StudentPreferences) -> Tuple[str, float]:
        """Determine Reach / Target / Likely category and admissions probability."""
        admissions = getattr(college, "admissions", None)
        admit_field = getattr(admissions, "acceptance_rate", None) if admissions else None
        admit_rate = _get_metric_val(admit_field, default=0.20)
        if admit_rate is None:
            admit_rate = 0.20

        admit_rate = min(1.0, max(0.0, float(admit_rate)))

        # Highly selective schools (<15% acceptance rate) are always Reach for general pool
        if admit_rate < 0.15:
            return "Reach", round(max(0.04, min(1.0, admit_rate * 0.8)), 2)

        # If student provided SAT score
        sat_score = getattr(prefs, "sat_score", None) or getattr(prefs, "sat", None) if prefs else None
        if sat_score and admissions:
            sat25_field = getattr(admissions, "sat_total_25", None)
            sat75_field = getattr(admissions, "sat_total_75", None)
            sat25 = _get_metric_val(sat25_field, default=1200)
            sat75 = _get_metric_val(sat75_field, default=1450)
            if sat25 is None:
                sat25 = 1200
            if sat75 is None:
                sat75 = 1450

            sat25 = float(sat25)
            sat75 = float(sat75)
            sat_score_f = float(sat_score)

            if sat_score_f >= sat75 and admit_rate >= 0.30:
                return "Likely", round(min(0.92, max(0.0, admit_rate * 1.5)), 2)
            elif sat_score_f >= sat25:
                return "Target", round(min(0.75, max(0.25, admit_rate * 1.1)), 2)
            else:
                return "Reach", round(max(0.05, min(1.0, admit_rate * 0.5)), 2)

        # If student provided GPA
        gpa = getattr(prefs, "gpa", None) if prefs else None
        if gpa:
            try:
                gpa_f = float(gpa)
                if gpa_f >= 3.85 and admit_rate >= 0.35:
                    return "Likely", round(min(0.90, admit_rate * 1.3), 2)
                elif gpa_f >= 3.4 and admit_rate >= 0.18:
                    return "Target", round(min(0.75, max(0.25, admit_rate)), 2)
                else:
                    return "Reach", round(max(0.05, admit_rate * 0.6), 2)
            except (ValueError, TypeError):
                pass

        # Fallback to clear selectivity tiers
        if admit_rate >= 0.50:
            return "Likely", round(min(0.88, max(0.0, admit_rate)), 2)
        elif admit_rate >= 0.18:
            return "Target", round(min(1.0, max(0.0, admit_rate)), 2)
        else:
            return "Reach", round(min(1.0, max(0.0, admit_rate)), 2)


fit_scorer = FitScorerService()

