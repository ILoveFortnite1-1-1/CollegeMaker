"""Admissions Chances Estimator Service."""
from typing import Any, Dict, Optional
from server.models.canonical import CanonicalCollege, ChancesEstimate
from server.models.portfolio import StudentPreferences


class ChancesService:
    """Estimates student admission chances (Reach, Target, Likely, Safety) based on Scorecard data."""

    def estimate_chances(
        self,
        college: CanonicalCollege,
        preferences: Optional[StudentPreferences] = None,
        custom_gpa: Optional[float] = None,
        custom_sat: Optional[int] = None,
        custom_act: Optional[int] = None,
    ) -> ChancesEstimate:
        """Evaluate chances for a college against student preferences or explicit stats."""
        # 1. Resolve acceptance rate
        admissions = getattr(college, "admissions", None)
        ar_field = getattr(admissions, "acceptance_rate", None)
        ar = ar_field.value if ar_field and ar_field.value is not None else 0.40

        # 2. Resolve college 25th/75th percentiles
        sat_25 = None
        sat_75 = None
        act_25 = None
        act_75 = None

        if admissions:
            if admissions.sat_total_25 and admissions.sat_total_25.value:
                sat_25 = admissions.sat_total_25.value
            if admissions.sat_total_75 and admissions.sat_total_75.value:
                sat_75 = admissions.sat_total_75.value

            # Fallback to reading + math if total is missing
            if not sat_25 and admissions.sat_reading_25 and admissions.sat_math_25:
                r25 = admissions.sat_reading_25.value or 0
                m25 = admissions.sat_math_25.value or 0
                if r25 > 0 and m25 > 0:
                    sat_25 = r25 + m25
            if not sat_75 and admissions.sat_reading_75 and admissions.sat_math_75:
                r75 = admissions.sat_reading_75.value or 0
                m75 = admissions.sat_math_75.value or 0
                if r75 > 0 and m75 > 0:
                    sat_75 = r75 + m75

            if admissions.act_25 and admissions.act_25.value:
                act_25 = admissions.act_25.value
            if admissions.act_75 and admissions.act_75.value:
                act_75 = admissions.act_75.value

        # 3. Resolve student credentials
        student_gpa = custom_gpa
        student_sat = custom_sat
        student_act = custom_act

        if preferences:
            if student_gpa is None:
                student_gpa = preferences.gpa
            if student_sat is None:
                student_sat = preferences.sat_score or preferences.sat
            if student_act is None:
                student_act = preferences.act_score

        # 4. Invariant: Colleges with acceptance rate < 15% are ALWAYS Reach
        if ar < 0.15:
            classification = "Reach"
            prob = max(0.04, min(0.18, ar * 0.8))
            summary = f"Ultra-selective institution ({int(round(ar * 100))}% admit rate). Classified as Reach for all applicants."
            gpa_status = self._evaluate_gpa_status(student_gpa, 3.8)
            test_status = self._evaluate_test_status(student_sat, student_act, sat_25, sat_75, act_25, act_75)

            return ChancesEstimate(
                college_id=str(college.id),
                college_name=college.name,
                classification=classification,
                category=classification,
                gpa_status=gpa_status,
                test_status=test_status,
                overall_probability=round(prob, 2),
                admissions_probability=round(prob, 2),
                acceptance_rate=round(ar, 3),
                summary=summary,
                rationale=summary,
            )

        # 5. Evaluate test status
        sat_tier = None
        if student_sat and sat_25 and sat_75:
            if student_sat > sat_75:
                sat_tier = "above_75"
            elif student_sat >= sat_25:
                sat_tier = "between"
            else:
                sat_tier = "below_25"

        act_tier = None
        if student_act and act_25 and act_75:
            if student_act > act_75:
                act_tier = "above_75"
            elif student_act >= act_25:
                act_tier = "between"
            else:
                act_tier = "below_25"

        stat_tier = sat_tier or act_tier

        # 6. Classification decision matrix
        if stat_tier == "above_75" or (student_gpa is not None and student_gpa >= 3.80):
            if ar >= 0.50:
                classification = "Safety"
                prob = min(0.95, 0.75 + ar * 0.2)
                summary = f"Your academic stats exceed the 75th percentile and the acceptance rate ({int(round(ar * 100))}%) makes this a Safety."
            elif ar >= 0.28:
                classification = "Likely"
                prob = min(0.85, 0.55 + ar * 0.4)
                summary = f"Your stats are above the middle 50% range, making admission Likely ({int(round(ar * 100))}% admit rate)."
            else:
                classification = "Target"
                prob = min(0.65, 0.35 + ar * 0.8)
                summary = f"Scores exceed 75th percentile, but competitive overall selectivity ({int(round(ar * 100))}%) keeps this as Target."

        elif stat_tier == "between" or (student_gpa is not None and student_gpa >= 3.20):
            if ar >= 0.60:
                classification = "Likely"
                prob = min(0.88, 0.65 + ar * 0.2)
                summary = f"Your stats fall in the middle 50% with an accessible acceptance rate ({int(round(ar * 100))}%)."
            elif ar >= 0.20:
                classification = "Target"
                prob = min(0.65, 0.30 + ar * 0.6)
                summary = f"Your stats are squarely within the middle 50% percentile range ({int(round(ar * 100))}% admit rate)."
            else:
                classification = "Reach"
                prob = min(0.35, 0.15 + ar * 0.5)
                summary = f"Scores are in range, but high institutional selectivity ({int(round(ar * 100))}%) creates a Reach."

        elif stat_tier == "below_25" or (student_gpa is not None and student_gpa < 3.20):
            if ar >= 0.70:
                classification = "Target"
                prob = min(0.60, 0.40 + ar * 0.2)
                summary = f"Stats are below the 25th percentile, but high overall acceptance ({int(round(ar * 100))}%) provides a Target opportunity."
            else:
                classification = "Reach"
                prob = max(0.06, ar * 0.5)
                summary = f"Academic credentials fall below the 25th percentile of admitted students ({int(round(ar * 100))}% admit rate)."

        else:
            # Fallback based purely on acceptance rate when student stats are not provided
            if ar >= 0.65:
                classification = "Safety"
                prob = min(0.92, ar)
                summary = f"Accessible admissions rate of {int(round(ar * 100))}% indicates strong admissions certainty."
            elif ar >= 0.40:
                classification = "Likely"
                prob = min(0.80, ar)
                summary = f"Favorable acceptance rate of {int(round(ar * 100))}% provides Likely positioning."
            elif ar >= 0.18:
                classification = "Target"
                prob = min(0.60, ar)
                summary = f"Selective admissions with an acceptance rate of {int(round(ar * 100))}% (Target tier)."
            else:
                classification = "Reach"
                prob = min(0.28, ar)
                summary = f"Highly competitive admissions ({int(round(ar * 100))}% acceptance rate) places this in Reach."

        gpa_status = self._evaluate_gpa_status(student_gpa, 3.5)
        test_status = self._evaluate_test_status(student_sat, student_act, sat_25, sat_75, act_25, act_75)

        return ChancesEstimate(
            college_id=str(college.id),
            college_name=college.name,
            classification=classification,
            category=classification,
            gpa_status=gpa_status,
            test_status=test_status,
            overall_probability=round(prob, 2),
            admissions_probability=round(prob, 2),
            acceptance_rate=round(ar, 3),
            summary=summary,
            rationale=summary,
        )

    def _evaluate_gpa_status(self, gpa: Optional[float], benchmark: float = 3.5) -> Dict[str, Any]:
        if gpa is None:
            return {"user_gpa": None, "status": "unreported", "benchmark": benchmark}
        if gpa >= benchmark + 0.3:
            status = "above"
        elif gpa >= benchmark - 0.2:
            status = "within"
        else:
            status = "below"
        return {"user_gpa": gpa, "status": status, "benchmark": benchmark}

    def _evaluate_test_status(
        self,
        user_sat: Optional[int],
        user_act: Optional[int],
        sat_25: Optional[int],
        sat_75: Optional[int],
        act_25: Optional[int],
        act_75: Optional[int],
    ) -> Dict[str, Any]:
        position_ratio = None
        status = "unreported"

        if user_sat and sat_25 and sat_75 and sat_75 > sat_25:
            position_ratio = round((user_sat - sat_25) / (sat_75 - sat_25), 2)
            if user_sat > sat_75:
                status = "above"
            elif user_sat >= sat_25:
                status = "within"
            else:
                status = "below"
        elif user_act and act_25 and act_75 and act_75 > act_25:
            position_ratio = round((user_act - act_25) / (act_75 - act_25), 2)
            if user_act > act_75:
                status = "above"
            elif user_act >= act_25:
                status = "within"
            else:
                status = "below"

        return {
            "user_sat": user_sat,
            "user_act": user_act,
            "sat_25": sat_25,
            "sat_75": sat_75,
            "act_25": act_25,
            "act_75": act_75,
            "position_ratio": position_ratio,
            "status": status,
        }


chances_service = ChancesService()
