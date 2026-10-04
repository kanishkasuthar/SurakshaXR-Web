"""Canonical Event Ingestion and Scoring Pipeline for Person 1 & Person 3."""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas
from app.scoring import ScoringEngine
from app.ai_coach import AISafetyCoach
from app.recommendations import RecommendationEngine

router = APIRouter(prefix="/api/v1", tags=["Events & Scoring"])


@router.post("/events", response_model=schemas.EventResponse, status_code=status.HTTP_200_OK)
def ingest_event(event_req: schemas.SyncEventRequest, db: Session = Depends(get_db)):
    """
    Ingest AR/simulation safety events from Unity (Person 1) or Android (Person 3).

    Features:
    - Idempotent: duplicate event_id requests return previous result without double-counting.
    - Transparent scoring: action-based point calculation clamped to 0-100.
    - Mistake analysis: severity, weak area identification.
    - AI Coach: adaptive guidance, personalized feedback, next training selection.
    - Offline sync safe.
    """
    # 1. Idempotency Check
    existing_event = db.query(models.Event).filter(models.Event.event_id == event_req.event_id).first()
    if existing_event:
        # Return existing result for this worker/scenario
        existing_res = db.query(models.TrainingResult).filter(
            models.TrainingResult.worker_id == event_req.worker_id,
            models.TrainingResult.scenario_id == event_req.scenario_id
        ).order_by(models.TrainingResult.completed_at.desc()).first()

        if existing_res:
            return schemas.EventResponse(
                event_id=event_req.event_id,
                worker_id=existing_res.worker_id,
                scenario_id=existing_res.scenario_id,
                score=existing_res.score,
                mistakes=existing_res.mistakes,
                weak_area=existing_res.weak_area,
                recommendation=existing_res.recommendation,
                message=existing_res.message,
                next_training=existing_res.next_training,
                ppe_level=existing_res.ppe_level,
                completed_at=existing_res.completed_at.isoformat() if existing_res.completed_at else None,
            )

    # A new TRAINING_STARTED event resets this worker+scenario scoring session.
    if event_req.action.upper() == "TRAINING_STARTED":
        db.query(models.Event).filter(
            models.Event.worker_id == event_req.worker_id,
            models.Event.scenario_id == event_req.scenario_id
        ).delete(synchronize_session=False)

        db.query(models.TrainingResult).filter(
            models.TrainingResult.worker_id == event_req.worker_id,
            models.TrainingResult.scenario_id == event_req.scenario_id
        ).delete(synchronize_session=False)

        db.commit()

    # 2. Ensure Worker exists in database
    worker = db.query(models.Worker).filter(models.Worker.worker_id == event_req.worker_id).first()
    if not worker:
        worker = models.Worker(
            worker_id=event_req.worker_id,
            name=f"Worker {event_req.worker_id}",
            phone=None,
            language="en"
        )
        db.add(worker)
        db.commit()
        db.refresh(worker)

    # 3. Store Event in Database
    obj_id = event_req.metadata.object_id if event_req.metadata else None
    px = event_req.metadata.position.x if event_req.metadata and event_req.metadata.position else None
    py = event_req.metadata.position.y if event_req.metadata and event_req.metadata.position else None
    pz = event_req.metadata.position.z if event_req.metadata and event_req.metadata.position else None

    new_event = models.Event(
        event_id=event_req.event_id,
        worker_id=event_req.worker_id,
        scenario_id=event_req.scenario_id,
        action=event_req.action,
        timestamp=event_req.timestamp,
        object_id=obj_id,
        position_x=px,
        position_y=py,
        position_z=pz,
        created_at=datetime.now(timezone.utc)
    )
    db.add(new_event)
    db.commit()

    # 4. Fetch prior session events for this worker and scenario to evaluate progression
    recent_events = db.query(models.Event).filter(
        models.Event.worker_id == event_req.worker_id,
        models.Event.scenario_id == event_req.scenario_id
    ).order_by(models.Event.timestamp.asc()).all()

    actions_list = [e.action for e in recent_events]
    if not actions_list:
        actions_list = [event_req.action]

    # 5. Scoring Engine Evaluation
    eval_result = ScoringEngine.evaluate_events(actions_list, event_req.scenario_id)

    # 6. AI Safety Coach Analysis
    coach_feedback = AISafetyCoach.generate_feedback(
        score=eval_result["score"],
        mistakes=eval_result["mistakes"],
        weak_area=eval_result["weak_area"],
        scenario_id=event_req.scenario_id,
        recent_actions=actions_list
    )

    # 7. Update or Record Training Result
    now = datetime.now(timezone.utc)
    training_res = db.query(models.TrainingResult).filter(
        models.TrainingResult.worker_id == event_req.worker_id,
        models.TrainingResult.scenario_id == event_req.scenario_id
    ).first()

    if not training_res:
        training_res = models.TrainingResult(
            worker_id=event_req.worker_id,
            scenario_id=event_req.scenario_id,
            score=eval_result["score"],
            mistakes=eval_result["mistakes"],
            weak_area=eval_result["weak_area"],
            recommendation=coach_feedback["recommendation"],
            ppe_level=eval_result["ppe_level"],
            message=coach_feedback["message"],
            next_training=coach_feedback["next_training"],
            completed_at=now
        )
        db.add(training_res)
    else:
        training_res.score = eval_result["score"]
        training_res.mistakes = eval_result["mistakes"]
        training_res.weak_area = eval_result["weak_area"]
        training_res.recommendation = coach_feedback["recommendation"]
        training_res.ppe_level = eval_result["ppe_level"]
        training_res.message = coach_feedback["message"]
        training_res.next_training = coach_feedback["next_training"]
        training_res.completed_at = now

    db.commit()
    db.refresh(training_res)

    # 8. Adaptive Recommendation Engine Sync
    RecommendationEngine.sync_recommendations_for_result(
        db=db,
        worker_id=event_req.worker_id,
        scenario_id=event_req.scenario_id,
        score=eval_result["score"],
        mistakes=eval_result["mistakes"],
        weak_area=eval_result["weak_area"],
        recent_actions=actions_list
    )

    # 9. Update / Issue Certificate if eligible (score >= 80)
    all_worker_results = db.query(models.TrainingResult).filter(
        models.TrainingResult.worker_id == event_req.worker_id
    ).all()
    avg_score = sum(r.score for r in all_worker_results) / len(all_worker_results) if all_worker_results else eval_result["score"]

    if avg_score >= 80:
        cert = db.query(models.Certificate).filter(models.Certificate.worker_id == event_req.worker_id).first()
        if not cert:
            cert_id = f"SURAKSHA-{event_req.worker_id}-2026"
            cert = models.Certificate(
                worker_id=event_req.worker_id,
                certificate_id=cert_id,
                verification_token=cert_id,
                status="Certified",
                issued_at=now
            )
            db.add(cert)
            db.commit()

    return schemas.EventResponse(
        event_id=event_req.event_id,
        worker_id=event_req.worker_id,
        scenario_id=event_req.scenario_id,
        score=training_res.score,
        mistakes=training_res.mistakes,
        weak_area=training_res.weak_area,
        recommendation=training_res.recommendation,
        message=training_res.message,
        next_training=training_res.next_training,
        ppe_level=training_res.ppe_level,
        completed_at=training_res.completed_at.isoformat() if training_res.completed_at else None,
    )
