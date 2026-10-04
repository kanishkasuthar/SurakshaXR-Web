"""Admin and Analytics Endpoints for Person 4 Web Dashboard."""
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/api/admin", tags=["Admin Dashboard & Analytics"])


@router.get("/workers", response_model=List[schemas.AdminWorkerDto])
def get_admin_workers(db: Session = Depends(get_db)):
    """Retrieve all workers and their training scores and certification status."""
    workers = db.query(models.Worker).all()
    results = []

    for w in workers:
        worker_results = db.query(models.TrainingResult).filter(
            models.TrainingResult.worker_id == w.worker_id
        ).all()

        fire_score = 0
        gas_score = 0
        ppe_score = 0
        scores = []

        for r in worker_results:
            sc_id = r.scenario_id.upper()
            if "FIRE" in sc_id:
                fire_score = r.score
            elif "GAS" in sc_id:
                gas_score = r.score
            elif "PPE" in sc_id:
                ppe_score = r.score
            scores.append(r.score)

        overall = round(sum(scores) / len(scores)) if scores else 0

        cert = db.query(models.Certificate).filter(models.Certificate.worker_id == w.worker_id).first()
        if cert and cert.status == "Certified":
            status_text = "Certified"
        elif overall >= 80:
            status_text = "Certified"
        elif overall > 0:
            status_text = "Training Required"
        else:
            status_text = "Not Certified"

        results.append(
            schemas.AdminWorkerDto(
                worker_id=w.worker_id,
                name=w.name,
                score=overall,
                overall_score=overall,
                fire_score=fire_score,
                gas_score=gas_score,
                ppe_score=ppe_score,
                status=status_text
            )
        )
    return results


@router.get("/analytics", response_model=schemas.AdminAnalyticsDto)
def get_admin_analytics(db: Session = Depends(get_db)):
    """
    Retrieve real-time aggregate training analytics, certification rates,
    and category performance for Web_Person4 dashboard.
    """
    workers = db.query(models.Worker).all()
    total_workers = len(workers)
    total_events = db.query(models.Event).count()
    all_results = db.query(models.TrainingResult).all()
    total_trainings = len(all_results)

    total_mistakes = sum(r.mistakes for r in all_results)

    all_scores = [r.score for r in all_results]
    average_score = round(sum(all_scores) / len(all_scores), 1) if all_scores else 0.0

    # Module specific averages
    fire_scores = [r.score for r in all_results if "FIRE" in r.scenario_id.upper()]
    gas_scores = [r.score for r in all_results if "GAS" in r.scenario_id.upper()]
    ppe_scores = [r.score for r in all_results if "PPE" in r.scenario_id.upper()]

    avg_fire = round(sum(fire_scores) / len(fire_scores)) if fire_scores else 0
    avg_gas = round(sum(gas_scores) / len(gas_scores)) if gas_scores else 0
    avg_ppe = round(sum(ppe_scores) / len(ppe_scores)) if ppe_scores else 0

    # Workers certification status count
    certified_count = 0
    for w in workers:
        w_results = [r.score for r in all_results if r.worker_id == w.worker_id]
        w_overall = round(sum(w_results) / len(w_results)) if w_results else 0
        cert = db.query(models.Certificate).filter(models.Certificate.worker_id == w.worker_id).first()
        if (cert and cert.status == "Certified") or w_overall >= 80:
            certified_count += 1

    training_required = total_workers - certified_count

    return schemas.AdminAnalyticsDto(
        total_workers=total_workers,
        workers=total_workers,
        certified=certified_count,
        training_required=training_required,
        total_events=total_events,
        total_trainings=total_trainings,
        average_score=average_score,
        total_mistakes=total_mistakes,
        module_scores={
            "Fire": avg_fire,
            "Gas": avg_gas,
            "PPE": avg_ppe
        }
    )


@router.get("/events", response_model=List[schemas.AdminEventDto])
def get_admin_events(db: Session = Depends(get_db)):
    """Recent safety events for the live dashboard."""
    events = db.query(models.Event).order_by(models.Event.created_at.desc()).limit(50).all()
    return [
        schemas.AdminEventDto(
            event_id=e.event_id,
            worker_id=e.worker_id,
            scenario_id=e.scenario_id,
            action=e.action,
            timestamp=e.timestamp,
            created_at=e.created_at.isoformat() if e.created_at else None,
        )
        for e in events
    ]


@router.get("/results", response_model=List[schemas.AdminResultDto])
def get_admin_results(db: Session = Depends(get_db)):
    """Latest training results for all workers."""
    results = db.query(models.TrainingResult).order_by(models.TrainingResult.completed_at.desc()).all()
    return [
        schemas.AdminResultDto(
            worker_id=r.worker_id,
            scenario_id=r.scenario_id,
            score=r.score,
            mistakes=r.mistakes,
            weak_area=r.weak_area,
            recommendation=r.recommendation,
            message=r.message,
            next_training=r.next_training,
            completed_at=r.completed_at.isoformat() if r.completed_at else None,
        )
        for r in results
    ]


@router.get("/recommendations", response_model=List[schemas.RecommendationDto])
def get_admin_recommendations(db: Session = Depends(get_db)):
    recs = db.query(models.Recommendation).order_by(models.Recommendation.created_at.desc()).limit(40).all()
    return [
        schemas.RecommendationDto(title=f"{r.worker_id}: {r.title}", message=r.message, module_id=r.module_id)
        for r in recs
    ]
