"""Training Module Endpoints for Suraksha-XR."""
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/api/training", tags=["Training Modules"])


@router.get("/modules", response_model=List[schemas.TrainingModuleDto])
def get_training_modules(db: Session = Depends(get_db)):
    """Retrieve all available interactive AR safety training modules."""
    modules = db.query(models.TrainingModule).all()
    return modules
