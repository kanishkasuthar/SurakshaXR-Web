"""SQLAlchemy Database Models for Suraksha-XR."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, BigInteger, DateTime, func
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default="worker", nullable=False)
    worker_id = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Worker(Base):
    __tablename__ = "workers"

    worker_id = Column(String(50), primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    phone = Column(String(50), nullable=True)
    language = Column(String(20), default="en", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class TrainingModule(Base):
    __tablename__ = "training_modules"

    module_id = Column(String(50), primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    category = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    level = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String(100), unique=True, index=True, nullable=False)
    worker_id = Column(String(50), index=True, nullable=False)
    scenario_id = Column(String(50), nullable=False)
    action = Column(String(100), nullable=False)
    timestamp = Column(BigInteger, nullable=False)
    object_id = Column(String(100), nullable=True)
    position_x = Column(Float, nullable=True)
    position_y = Column(Float, nullable=True)
    position_z = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class TrainingResult(Base):
    __tablename__ = "training_results"

    id = Column(Integer, primary_key=True, index=True)
    worker_id = Column(String(50), index=True, nullable=False)
    scenario_id = Column(String(50), nullable=False)
    score = Column(Integer, nullable=False, default=0)
    mistakes = Column(Integer, nullable=False, default=0)
    weak_area = Column(String(100), nullable=True)
    recommendation = Column(Text, nullable=True)
    ppe_level = Column(String(50), nullable=True)
    message = Column(Text, nullable=True)
    next_training = Column(String(50), nullable=True)
    completed_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    worker_id = Column(String(50), index=True, nullable=False)
    title = Column(String(100), nullable=False)
    message = Column(Text, nullable=False)
    module_id = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Certificate(Base):
    __tablename__ = "certificates"

    id = Column(Integer, primary_key=True, index=True)
    worker_id = Column(String(50), unique=True, index=True, nullable=False)
    certificate_id = Column(String(100), unique=True, index=True, nullable=False)
    verification_token = Column(String(100), unique=True, index=True, nullable=False)
    status = Column(String(50), default="Certified", nullable=False)
    issued_at = Column(DateTime, default=datetime.utcnow, nullable=False)
