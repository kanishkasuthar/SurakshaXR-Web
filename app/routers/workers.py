"""Worker Results, Safety Passport, and Recommendations Endpoints."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas
from app.recommendations import RecommendationEngine

router = APIRouter(prefix="/api/workers", tags=["Workers & Safety Passport"])


@router.get("/{worker_id}/latest-result", response_model=schemas.ResultDto)
def get_latest_result(worker_id: str, db: Session = Depends(get_db)):
    """Retrieve the most recent training assessment result for a worker."""
    result = db.query(models.TrainingResult).filter(
        models.TrainingResult.worker_id == worker_id
    ).order_by(models.TrainingResult.completed_at.desc()).first()

    if not result:
        # Check if worker exists
        worker = db.query(models.Worker).filter(models.Worker.worker_id == worker_id).first()
        if not worker:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Worker '{worker_id}' not found"
            )
        # Return initial default if worker exists but hasn't taken a test
        return schemas.ResultDto(
            worker_id=worker_id,
            score=0,
            mistakes=0,
            weak_area=None,
            recommendation="Start your first safety training module.",
            ppe_level="Level 1",
            completed_at=None,
            message="No training completed yet.",
            next_training="FIRE_01"
        )

    return schemas.ResultDto(
        worker_id=result.worker_id,
        score=result.score,
        mistakes=result.mistakes,
        weak_area=result.weak_area,
        recommendation=result.recommendation,
        ppe_level=result.ppe_level,
        completed_at=result.completed_at.isoformat() if result.completed_at else None,
        message=result.message,
        next_training=result.next_training
    )


@router.get("/{worker_id}/passport", response_model=schemas.PassportDto)
def get_safety_passport(worker_id: str, db: Session = Depends(get_db)):
    """
    Retrieve comprehensive Safety Passport for a worker.
    Calculates fire, gas, PPE, and overall scores from persistent database records.
    """
    worker = db.query(models.Worker).filter(models.Worker.worker_id == worker_id).first()
    worker_name = worker.name if worker else f"Worker {worker_id}"

    results = db.query(models.TrainingResult).filter(
        models.TrainingResult.worker_id == worker_id
    ).all()

    fire_score = 0
    gas_score = 0
    ppe_score = 0

    scores = []
    for r in results:
        sc_id = r.scenario_id.upper()
        if "FIRE" in sc_id:
            fire_score = r.score
            scores.append(r.score)
        elif "GAS" in sc_id:
            gas_score = r.score
            scores.append(r.score)
        elif "PPE" in sc_id:
            ppe_score = r.score
            scores.append(r.score)
        else:
            scores.append(r.score)

    overall_score = round(sum(scores) / len(scores)) if scores else 0

    # Determine certification status
    cert = db.query(models.Certificate).filter(models.Certificate.worker_id == worker_id).first()
    if cert and cert.status == "Certified":
        cert_status = "Certified"
    elif overall_score >= 80:
        cert_status = "Training Complete"
    elif overall_score > 0:
        cert_status = "In Progress"
    else:
        cert_status = "Not Certified"

    return schemas.PassportDto(
        worker_id=worker_id,
        worker_name=worker_name,
        fire_score=fire_score,
        gas_score=gas_score,
        ppe_score=ppe_score,
        overall_score=overall_score,
        status=cert_status
    )


@router.get("/{worker_id}/recommendations", response_model=List[schemas.RecommendationDto])
def get_worker_recommendations(worker_id: str, db: Session = Depends(get_db)):
    """Retrieve personalized AI safety recommendations for a worker."""
    recs = RecommendationEngine.get_worker_recommendations(db, worker_id)
    return [
        schemas.RecommendationDto(
            title=r.title,
            message=r.message,
            module_id=r.module_id
        )
        for r in recs
    ]
