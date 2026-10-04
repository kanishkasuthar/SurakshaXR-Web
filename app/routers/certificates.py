"""Certificate Generation and QR Verification Endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/api", tags=["Certificates & Verification"])


@router.get("/certificates/{worker_id}", response_model=schemas.CertificateDto)
def get_certificate(worker_id: str, db: Session = Depends(get_db)):
    """Retrieve official safety training certificate for a worker."""
    worker = db.query(models.Worker).filter(models.Worker.worker_id == worker_id).first()
    if not worker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Worker '{worker_id}' not found"
        )

    cert = db.query(models.Certificate).filter(models.Certificate.worker_id == worker_id).first()

    # Calculate overall score from training results
    results = db.query(models.TrainingResult).filter(models.TrainingResult.worker_id == worker_id).all()
    scores = [r.score for r in results]
    overall_score = round(sum(scores) / len(scores)) if scores else 0

    if not cert:
        # If worker has passing score, auto-issue certificate
        if overall_score >= 80:
            cert_id = f"SURAKSHA-{worker_id}-2026"
            cert = models.Certificate(
                worker_id=worker_id,
                certificate_id=cert_id,
                verification_token=cert_id,
                status="Certified",
            )
            db.add(cert)
            db.commit()
            db.refresh(cert)
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No certified credentials found for worker '{worker_id}'"
            )

    issued_date = cert.issued_at.strftime("%Y-%m-%d") if cert.issued_at else "2026-09-27"

    return schemas.CertificateDto(
        certificate_id=cert.certificate_id,
        worker_id=worker.worker_id,
        worker_name=worker.name,
        overall_score=overall_score,
        status=cert.status,
        issued_on=issued_date,
        verification_token=cert.verification_token
    )


@router.get("/verify/{token}", response_model=schemas.VerificationResponse)
def verify_certificate(token: str, db: Session = Depends(get_db)):
    """
    Verify authenticity of a safety certificate by scanning its verification token.
    Publicly accessible endpoint for field safety auditors and regulators.
    """
    cert = db.query(models.Certificate).filter(
        (models.Certificate.verification_token == token) |
        (models.Certificate.certificate_id == token)
    ).first()

    if not cert:
        return schemas.VerificationResponse(
            valid=False,
            verified=False,
            message="Certificate not found or invalid"
        )

    worker = db.query(models.Worker).filter(models.Worker.worker_id == cert.worker_id).first()
    results = db.query(models.TrainingResult).filter(models.TrainingResult.worker_id == cert.worker_id).all()
    scores = [r.score for r in results]
    overall = round(sum(scores) / len(scores)) if scores else 85

    issued_date = cert.issued_at.strftime("%Y-%m-%d") if cert.issued_at else "2026-09-27"

    return schemas.VerificationResponse(
        valid=True,
        verified=True,
        worker_id=cert.worker_id,
        worker_name=worker.name if worker else cert.worker_id,
        certificate_id=cert.certificate_id,
        status="Valid" if cert.status in ["Certified", "Valid"] else cert.status,
        overall_score=overall,
        issued_on=issued_date,
        verification_token=cert.verification_token,
        message="Official Suraksha-XR Certificate Verified"
    )
