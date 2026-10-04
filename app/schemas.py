"""Pydantic request and response schemas for Suraksha-XR."""
from typing import Optional, List, Dict
from pydantic import BaseModel, ConfigDict


# -------------------------------------------------------------
# Authentication Schemas
# -------------------------------------------------------------
class LoginRequest(BaseModel):
    username: str
    password: str


class WorkerDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    worker_id: str
    name: str
    phone: Optional[str] = None
    language: Optional[str] = "en"


class LoginResponse(BaseModel):
    access_token: Optional[str] = None
    token: Optional[str] = None
    token_type: str = "bearer"
    role: str = "worker"
    worker: Optional[WorkerDto] = None


# -------------------------------------------------------------
# Training Module Schemas
# -------------------------------------------------------------
class TrainingModuleDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    module_id: str
    title: str
    category: str
    description: Optional[str] = None
    level: Optional[str] = None


# -------------------------------------------------------------
# Canonical Event Schemas (Person 1 + Person 3)
# -------------------------------------------------------------
class PositionDto(BaseModel):
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0


class EventMetadataDto(BaseModel):
    object_id: Optional[str] = None
    position: Optional[PositionDto] = None


class SyncEventRequest(BaseModel):
    event_id: str
    worker_id: str
    scenario_id: str
    action: str
    timestamp: int
    metadata: Optional[EventMetadataDto] = None


class EventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    event_id: str
    worker_id: str
    scenario_id: str
    score: int
    mistakes: int
    weak_area: Optional[str] = None
    recommendation: Optional[str] = None
    message: Optional[str] = None
    next_training: Optional[str] = None
    ppe_level: Optional[str] = None
    completed_at: Optional[str] = None


# -------------------------------------------------------------
# Worker Results, Passport & Recommendations
# -------------------------------------------------------------
class ResultDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    worker_id: str
    score: int
    mistakes: int
    weak_area: Optional[str] = None
    recommendation: Optional[str] = None
    ppe_level: Optional[str] = None
    completed_at: Optional[str] = None
    message: Optional[str] = None
    next_training: Optional[str] = None


class PassportDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    worker_id: str
    worker_name: str
    fire_score: int = 0
    gas_score: int = 0
    ppe_score: int = 0
    overall_score: int = 0
    status: str = "Not Certified"


class RecommendationDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    title: str
    message: str
    module_id: Optional[str] = None


# -------------------------------------------------------------
# Web Dashboard & Admin Schemas (Person 4)
# -------------------------------------------------------------
class AdminWorkerDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    worker_id: str
    name: str
    score: int
    overall_score: int
    fire_score: int
    gas_score: int
    ppe_score: int
    status: str


class AdminAnalyticsDto(BaseModel):
    total_workers: int
    workers: int
    certified: int
    training_required: int
    total_events: int
    total_trainings: int
    average_score: float
    total_mistakes: int
    module_scores: Dict[str, int]


class AdminEventDto(BaseModel):
    event_id: str
    worker_id: str
    scenario_id: str
    action: str
    timestamp: int
    created_at: Optional[str] = None


class AdminResultDto(BaseModel):
    worker_id: str
    scenario_id: str
    score: int
    mistakes: int
    weak_area: Optional[str] = None
    recommendation: Optional[str] = None
    message: Optional[str] = None
    next_training: Optional[str] = None
    completed_at: Optional[str] = None


# -------------------------------------------------------------
# Certificate & Verification Schemas
# -------------------------------------------------------------
class CertificateDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    certificate_id: str
    worker_id: str
    worker_name: str
    overall_score: int
    status: str
    issued_on: str
    verification_token: str


class VerificationResponse(BaseModel):
    valid: bool
    verified: bool
    worker_id: Optional[str] = None
    worker_name: Optional[str] = None
    certificate_id: Optional[str] = None
    status: Optional[str] = None
    overall_score: Optional[int] = None
    issued_on: Optional[str] = None
    verification_token: Optional[str] = None
    message: Optional[str] = None
