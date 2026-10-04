"""Transparent, Explainable Action-Based Scoring Engine for Suraksha-XR."""
from typing import List, Dict, Any, Tuple, Optional


# Configurable Action Weights (Transparent & Explainable)
ACTION_WEIGHTS: Dict[str, int] = {
    # Positive actions
    "SAFE_EXIT": 20,
    "EXTINGUISHER_USED": 20,
    "USE_FIRE_EXTINGUISHER": 20,
    "ALARM_TRIGGERED": 15,
    "PULL_FIRE_ALARM": 15,
    "GAS_SHUTOFF": 20,
    "SHUTOFF_VALVE": 20,
    "CLOSE_GAS_VALVE": 20,
    "PPE_SELECTED": 15,
    "EQUIP_PPE": 15,
    "SELECT_PPE": 15,
    "HELP_REQUESTED": 10,
    "CALL_HELP": 10,
    "DEMO_CORRECT_ACTION": 15,
    "CORRECT_ACTION": 15,
    "SCENARIO_COMPLETED": 10,
    "TRAINING_STARTED": 0,

    # Negative actions (Mistakes)
    "WRONG_ACTION": -15,
    "WRONG_EXIT": -20,
    "RUN_WRONG_WAY": -20,
    "WRONG_EQUIPMENT": -15,
    "USE_WATER_ON_ELECTRICAL": -15,
    "PPE_MISSED": -15,
    "IGNORE_PPE": -15,
    "GAS_LEAK_IGNORED": -20,
    "ENTER_WITHOUT_MASK": -20,
    "DEMO_WRONG_ACTION": -15,
}

# Weak Area Mapping for specific actions
ACTION_WEAK_AREA_MAP: Dict[str, str] = {
    "WRONG_EXIT": "Emergency Evacuation",
    "RUN_WRONG_WAY": "Emergency Evacuation",
    "WRONG_EQUIPMENT": "Fire Safety",
    "USE_WATER_ON_ELECTRICAL": "Fire Safety",
    "PPE_MISSED": "PPE Compliance",
    "IGNORE_PPE": "PPE Compliance",
    "GAS_LEAK_IGNORED": "Gas Safety",
    "ENTER_WITHOUT_MASK": "Gas Safety",
    "DEMO_WRONG_ACTION": "Hazard Response",
    "WRONG_ACTION": "Hazard Response",
}

# Default scenario category fallback
SCENARIO_CATEGORY_MAP: Dict[str, str] = {
    "FIRE_01": "Fire Safety",
    "GAS_01": "Gas Safety",
    "PPE_01": "PPE Compliance",
}

BASE_SCORE = 70


class ScoringEngine:
    """Evaluates worker actions, computes explainable scores, and tallies mistakes."""

    @staticmethod
    def get_action_weight(action: str) -> int:
        """Return the point delta for an action. Unknown actions default to 0."""
        return ACTION_WEIGHTS.get(action.upper(), 0)

    @classmethod
    def evaluate_events(
        cls,
        events: List[str],
        scenario_id: str = "FIRE_01"
    ) -> Dict[str, Any]:
        """
        Evaluate a sequence of actions performed by a worker in a scenario.

        Returns:
            {
                "score": int (0-100),
                "total_events": int,
                "correct_actions": int,
                "incorrect_actions": int,
                "mistakes": int,
                "weak_area": str,
                "ppe_level": str,
            }
        """
        total_events = len(events)
        correct_actions = 0
        mistakes = 0
        score_delta = 0
        weak_area_counts: Dict[str, int] = {}

        has_ppe_actions = False

        for act in events:
            action_key = act.upper().strip()
            weight = cls.get_action_weight(action_key)

            if "PPE" in action_key:
                has_ppe_actions = True

            if weight > 0:
                correct_actions += 1
                score_delta += weight
            elif weight < 0:
                mistakes += 1
                score_delta += weight
                area = ACTION_WEAK_AREA_MAP.get(action_key, SCENARIO_CATEGORY_MAP.get(scenario_id, "General Safety"))
                weak_area_counts[area] = weak_area_counts.get(area, 0) + 1

        final_score = max(0, min(100, BASE_SCORE + score_delta))

        # Determine dominant weak area
        if weak_area_counts:
            dominant_weak_area = max(weak_area_counts.items(), key=lambda x: x[1])[0]
        else:
            dominant_weak_area = "None" if mistakes == 0 else SCENARIO_CATEGORY_MAP.get(scenario_id, "General Safety")

        # Determine PPE Level
        if final_score >= 85 and not mistakes:
            ppe_level = "Level 2"
        elif has_ppe_actions or scenario_id.startswith("PPE"):
            ppe_level = "Level 1"
        else:
            ppe_level = "Level 1"

        return {
            "score": final_score,
            "total_events": total_events,
            "correct_actions": correct_actions,
            "incorrect_actions": mistakes,
            "mistakes": mistakes,
            "weak_area": dominant_weak_area if dominant_weak_area != "None" else SCENARIO_CATEGORY_MAP.get(scenario_id, "None"),
            "ppe_level": ppe_level,
        }
