"""AI Safety Coach and Mistake Analysis Engine for Suraksha-XR."""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class MistakeDetail:
    mistake_type: str
    scenario_id: str
    severity: str
    weak_area: str
    recommended_correction: str


MISTAKE_CATALOG: Dict[str, Dict[str, str]] = {
    "WRONG_EXIT": {
        "severity": "High",
        "weak_area": "Emergency Evacuation",
        "recommended_correction": "Review emergency evacuation signs and follow marked green exit routes immediately.",
    },
    "RUN_WRONG_WAY": {
        "severity": "High",
        "weak_area": "Emergency Evacuation",
        "recommended_correction": "Do not run toward hazards during an evacuation; proceed to the designated assembly point.",
    },
    "WRONG_EQUIPMENT": {
        "severity": "High",
        "weak_area": "Fire Safety",
        "recommended_correction": "Match extinguisher class to fire type (Class A/B/C/Electrical). Never use water on live electrical equipment.",
    },
    "USE_WATER_ON_ELECTRICAL": {
        "severity": "Critical",
        "weak_area": "Fire Safety",
        "recommended_correction": "Using water on electrical equipment risks fatal shock. Use CO2 or dry chemical extinguishers.",
    },
    "PPE_MISSED": {
        "severity": "Medium",
        "weak_area": "PPE Compliance",
        "recommended_correction": "Select and equip all mandatory PPE (helmet, gloves, safety boots, goggles) before entering work zones.",
    },
    "IGNORE_PPE": {
        "severity": "High",
        "weak_area": "PPE Compliance",
        "recommended_correction": "PPE is mandatory under safety regulations. Repeat PPE donning and inspection procedures.",
    },
    "GAS_LEAK_IGNORED": {
        "severity": "Critical",
        "weak_area": "Gas Safety",
        "recommended_correction": "Never ignore active gas leak alarms. Shut off the supply valve and evacuate upwind immediately.",
    },
    "ENTER_WITHOUT_MASK": {
        "severity": "Critical",
        "weak_area": "Gas Safety",
        "recommended_correction": "Atmospheric hazards require breathing apparatus. Never enter a contaminated gas zone unprotected.",
    },
    "DEMO_WRONG_ACTION": {
        "severity": "Medium",
        "weak_area": "Operational Safety",
        "recommended_correction": "Review operating protocols before activating machinery.",
    },
}

NEXT_MODULE_PROGRESSION: Dict[str, str] = {
    "FIRE_01": "FIRE_02",
    "FIRE_02": "FIRE_ADVANCED",
    "GAS_01": "GAS_02",
    "GAS_02": "GAS_ADVANCED",
    "PPE_01": "PPE_02",
    "PPE_02": "PPE_ADVANCED",
}


class MistakeAnalyzer:
    """Analyzes incorrect actions to determine severity, weak areas, and corrections."""

    @staticmethod
    def analyze_action(action: str, scenario_id: str) -> Optional[MistakeDetail]:
        action_key = action.upper().strip()
        data = MISTAKE_CATALOG.get(action_key)
        if not data:
            return None
        return MistakeDetail(
            mistake_type=action_key,
            scenario_id=scenario_id,
            severity=data["severity"],
            weak_area=data["weak_area"],
            recommended_correction=data["recommended_correction"]
        )

    @classmethod
    def analyze_actions(cls, actions: List[str], scenario_id: str) -> List[MistakeDetail]:
        mistakes = []
        for a in actions:
            detail = cls.analyze_action(a, scenario_id)
            if detail:
                mistakes.append(detail)
        return mistakes


class AISafetyCoach:
    """
    Deterministic, explainable rule-based AI Safety Coach.
    Evaluates worker performance and generates personalized adaptive feedback.
    """

    @classmethod
    def generate_feedback(
        cls,
        score: int,
        mistakes: int,
        weak_area: str,
        scenario_id: str,
        recent_actions: Optional[List[str]] = None
    ) -> Dict[str, str]:
        """
        Produce:
        - message (personalized coaching feedback)
        - recommendation (actionable next step)
        - next_training (recommended next module ID)
        """
        actions = recent_actions or []
        mistake_details = MistakeAnalyzer.analyze_actions(actions, scenario_id)

        # Adaptive Rules:
        # 1. Score >= 85: Mastery achieved -> recommend next module or advanced level
        if score >= 85 and mistakes == 0:
            next_mod = NEXT_MODULE_PROGRESSION.get(scenario_id, scenario_id)
            message = "Excellent performance! All safety protocols were executed accurately and efficiently."
            recommendation = f"Mastery certified. Proceed to {next_mod} or complete advanced scenario certification."
            return {
                "message": message,
                "recommendation": recommendation,
                "next_training": next_mod,
            }
        elif score >= 85:
            next_mod = NEXT_MODULE_PROGRESSION.get(scenario_id, scenario_id)
            message = f"Strong overall safety awareness achieved ({score}%). Minor improvements needed in {weak_area}."
            recommendation = f"Reinforce {weak_area} protocols, then advance to {next_mod}."
            return {
                "message": message,
                "recommendation": recommendation,
                "next_training": next_mod,
            }

        # 2. Score 70-84: Competent but requires reinforcement
        elif 70 <= score < 85:
            if weak_area == "PPE Compliance" or "PPE" in weak_area:
                message = "Good response, but PPE protocol gaps were identified. Improve equipment selection before hazard entry."
                recommendation = "Practice helmet, gloves, goggles and safety-shoe selection."
                next_training = "PPE_01"
            elif weak_area == "Gas Safety" or "Gas" in weak_area:
                message = "Gas hazard handling requires caution. Ensure gas isolation is confirmed before entering the chamber."
                recommendation = "Repeat the gas-leak response scenario and review the shutdown sequence."
                next_training = "GAS_01"
            elif weak_area == "Emergency Evacuation":
                message = "Evacuation pathing delayed. Always prioritize designated emergency exits over nearest windows."
                recommendation = "Repeat emergency exit training and route drills."
                next_training = scenario_id
            else:
                message = f"Satisfactory execution ({score}%). Review {weak_area} to achieve full certification standard."
                recommendation = f"Complete reinforcement drill for {scenario_id}."
                next_training = scenario_id

            return {
                "message": message,
                "recommendation": recommendation,
                "next_training": next_training,
            }

        # 3. Score < 70: Remedial training required
        else:
            if mistake_details:
                top_mistake = mistake_details[0]
                message = f"Critical safety deviations detected in {top_mistake.weak_area}. {top_mistake.recommended_correction}"
                recommendation = f"Repeat {scenario_id} training focusing on {top_mistake.weak_area}."
            else:
                message = f"Score ({score}%) is below the safety clearance threshold. Review hazard procedures before re-attempting."
                recommendation = f"Repeat {scenario_id} training."

            return {
                "message": message,
                "recommendation": recommendation,
                "next_training": scenario_id,
            }
