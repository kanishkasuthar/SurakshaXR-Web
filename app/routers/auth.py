"""Authentication Endpoints for Suraksha-XR."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas
from app.auth import verify_password, create_access_token

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/login", response_model=schemas.LoginResponse)
def login(request: schemas.LoginRequest, db: Session = Depends(get_db)):
    """Authenticate a worker or administrator and issue a JWT token."""
    username = request.username.strip()
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        # Allow login with worker_id (e.g. W001) in addition to username (worker01).
        worker_match = db.query(models.Worker).filter(models.Worker.worker_id == username).first()
        if worker_match:
            user = db.query(models.User).filter(models.User.worker_id == worker_match.worker_id).first()
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Generate JWT
    token_data = {"sub": user.username, "role": user.role, "worker_id": user.worker_id}
    access_token = create_access_token(token_data)

    worker_dto = None
    if user.worker_id:
        worker = db.query(models.Worker).filter(models.Worker.worker_id == user.worker_id).first()
        if worker:
            worker_dto = schemas.WorkerDto(
                worker_id=worker.worker_id,
                name=worker.name,
                phone=worker.phone,
                language=worker.language
            )
        else:
            worker_dto = schemas.WorkerDto(
                worker_id=user.worker_id,
                name=user.username,
                phone=None,
                language="en"
            )
    elif user.role == "worker":
        # Fallback if worker_id wasn't explicitly linked
        worker_dto = schemas.WorkerDto(
            worker_id=user.username,
            name=user.username,
            phone=None,
            language="en"
        )

    return schemas.LoginResponse(
        access_token=access_token,
        token=access_token,
        token_type="bearer",
        role=user.role,
        worker=worker_dto
    )
