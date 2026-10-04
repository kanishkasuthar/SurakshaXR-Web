"""Adaptive Recommendation Engine for Suraksha-XR."""
from typing import List
from sqlalchemy.orm import Session
from app import models
from app.ai_coach import AISafetyCoach


class RecommendationEngine:
    """Generates and manages targeted recommendations based on training performance."""

    @classmethod
    def sync_recommendations_for_result(
        cls,
        db: Session,
        worker_id: str,
        scenario_id: str,
        score: int,
        mistakes: int,
        weak_area: str,
        recent_actions: List[str]
    ) -> models.Recommendation:
        """
        Generate an adaptive recommendation based on the latest result and save to DB.
        """
        coach_output = AISafetyCoach.generate_feedback(
            score=score,
            mistakes=mistakes,
            weak_area=weak_area,
            scenario_id=scenario_id,
            recent_actions=recent_actions
        )

        title = f"{weak_area} Improvement" if mistakes > 0 else f"{scenario_id} Advanced Drill"
        message = coach_output["recommendation"]
        module_id = coach_output["next_training"]

        # Check if an identical recent recommendation already exists for this worker
        existing = db.query(models.Recommendation).filter(
            models.Recommendation.worker_id == worker_id,
            models.Recommendation.title == title,
            models.Recommendation.message == message
        ).first()

        if not existing:
            rec = models.Recommendation(
                worker_id=worker_id,
                title=title,
                message=message,
                module_id=module_id
            )
            db.add(rec)
            db.commit()
            db.refresh(rec)
            return rec
        return existing

    @classmethod
    def get_worker_recommendations(
        cls,
        db: Session,
        worker_id: str
    ) -> List[models.Recommendation]:
        """Fetch all recommendations for a given worker, latest first."""
        recs = db.query(models.Recommendation).filter(
            models.Recommendation.worker_id == worker_id
        ).order_by(models.Recommendation.created_at.desc()).all()

        # If none exist yet, return adaptive default recommendations
        if not recs:
            default_recs = [
                models.Recommendation(
                    worker_id=worker_id,
                    title="PPE Level 2",
                    message="Practice helmet, gloves, goggles and safety-shoe selection.",
                    module_id="PPE_01"
                ),
                models.Recommendation(
                    worker_id=worker_id,
                    title="Gas refresher",
                    message="Repeat the gas-leak response scenario and review the shutdown sequence.",
                    module_id="GAS_01"
                )
            ]
            for r in default_recs:
                db.add(r)
            db.commit()
            for r in default_recs:
                db.refresh(r)
            return default_recs

        return recs
