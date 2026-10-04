"""Database Seeding Script for Suraksha-XR.

Run standalone via: python -m app.seed
Or automatically triggered on FastAPI application startup.
"""
from datetime import datetime
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine, Base
from app import models
from app.auth import get_password_hash


def seed_database(db: Session) -> None:
    """Seed initial demo users, workers, training modules, events, results, and certificates."""
    print("[Seed] Checking and seeding database records...")

    # 1. Users
    users_data = [
        {"username": "admin", "password": "admin123", "role": "admin", "worker_id": None},
        {"username": "worker01", "password": "worker123", "role": "worker", "worker_id": "W001"},
        {"username": "worker02", "password": "worker123", "role": "worker", "worker_id": "W002"},
        {"username": "worker03", "password": "worker123", "role": "worker", "worker_id": "W003"},
    ]
    for u in users_data:
        existing = db.query(models.User).filter(models.User.username == u["username"]).first()
        if not existing:
            db.add(models.User(
                username=u["username"],
                password_hash=get_password_hash(u["password"]),
                role=u["role"],
                worker_id=u["worker_id"]
            ))

    # 2. Workers
    workers_data = [
        {"worker_id": "W001", "name": "Rahul Kumar", "phone": "+91 98765 43210", "language": "en"},
        {"worker_id": "W002", "name": "Priya Singh", "phone": "+91 98765 43211", "language": "hi"},
        {"worker_id": "W003", "name": "Aman Das", "phone": "+91 98765 43212", "language": "en"},
        {"worker_id": "W004", "name": "Neha Patel", "phone": "+91 98765 43213", "language": "hi"},
    ]
    for w in workers_data:
        existing = db.query(models.Worker).filter(models.Worker.worker_id == w["worker_id"]).first()
        if not existing:
            db.add(models.Worker(
                worker_id=w["worker_id"],
                name=w["name"],
                phone=w["phone"],
                language=w["language"]
            ))

    # 3. Training Modules
    modules_data = [
        {
            "module_id": "FIRE_01",
            "title": "Fire Safety",
            "category": "Fire",
            "description": "Extinguisher use, alarm and safe exit",
            "level": "Beginner",
        },
        {
            "module_id": "GAS_01",
            "title": "Gas Safety",
            "category": "Gas",
            "description": "Detect leaks and follow safe shutdown procedure",
            "level": "Beginner",
        },
        {
            "module_id": "PPE_01",
            "title": "PPE Training",
            "category": "PPE",
            "description": "Select and use the required protective equipment",
            "level": "Level 1",
        },
    ]
    for m in modules_data:
        existing = db.query(models.TrainingModule).filter(models.TrainingModule.module_id == m["module_id"]).first()
        if not existing:
            db.add(models.TrainingModule(
                module_id=m["module_id"],
                title=m["title"],
                category=m["category"],
                description=m["description"],
                level=m["level"]
            ))

    db.commit()

    # 4. Sample Training Results (Realistic demo results matching Person 4 dashboard)
    results_data = [
        # W001
        {
            "worker_id": "W001",
            "scenario_id": "FIRE_01",
            "score": 92,
            "mistakes": 1,
            "weak_area": "Fire Safety",
            "recommendation": "Maintain proper safe distance when discharging the extinguisher.",
            "ppe_level": "Level 1",
            "message": "Strong performance on fire suppression and alarm routing.",
            "next_training": "FIRE_02"
        },
        {
            "worker_id": "W001",
            "scenario_id": "GAS_01",
            "score": 84,
            "mistakes": 2,
            "weak_area": "Gas Safety",
            "recommendation": "Repeat gas-leak response scenario and verify valve shutoff.",
            "ppe_level": "Level 1",
            "message": "Good response. Check valve seating carefully.",
            "next_training": "GAS_01"
        },
        {
            "worker_id": "W001",
            "scenario_id": "PPE_01",
            "score": 88,
            "mistakes": 1,
            "weak_area": "PPE",
            "recommendation": "Complete PPE Level 2 and practice glove and boot inspection.",
            "ppe_level": "Level 2",
            "message": "PPE selection verified with high compliance.",
            "next_training": "PPE_02"
        },
        # W002
        {
            "worker_id": "W002",
            "scenario_id": "FIRE_01",
            "score": 76,
            "mistakes": 3,
            "weak_area": "Fire Safety",
            "recommendation": "Repeat fire extinguisher training.",
            "ppe_level": "Level 1",
            "message": "Extinguisher pin sequence requires review.",
            "next_training": "FIRE_01"
        },
        {
            "worker_id": "W002",
            "scenario_id": "GAS_01",
            "score": 81,
            "mistakes": 2,
            "weak_area": "Gas Safety",
            "recommendation": "Review gas detector calibration and safe withdrawal routes.",
            "ppe_level": "Level 1",
            "message": "Sound awareness of warning alarms.",
            "next_training": "GAS_01"
        },
        {
            "worker_id": "W002",
            "scenario_id": "PPE_01",
            "score": 72,
            "mistakes": 4,
            "weak_area": "PPE Compliance",
            "recommendation": "Repeat PPE module. Wear protective eyewear at all times.",
            "ppe_level": "Level 1",
            "message": "Missing eye protection detected.",
            "next_training": "PPE_01"
        },
        # W003
        {
            "worker_id": "W003",
            "scenario_id": "FIRE_01",
            "score": 95,
            "mistakes": 0,
            "weak_area": "None",
            "recommendation": "Advance to industrial high-hazard fire suppression.",
            "ppe_level": "Level 2",
            "message": "Perfect execution of emergency evacuation and suppression.",
            "next_training": "FIRE_ADVANCED"
        },
        {
            "worker_id": "W003",
            "scenario_id": "GAS_01",
            "score": 91,
            "mistakes": 1,
            "weak_area": "Gas Safety",
            "recommendation": "Advance to confined-space gas monitoring.",
            "ppe_level": "Level 2",
            "message": "Rapid and accurate gas valve isolation.",
            "next_training": "GAS_02"
        },
        {
            "worker_id": "W003",
            "scenario_id": "PPE_01",
            "score": 93,
            "mistakes": 1,
            "weak_area": "PPE",
            "recommendation": "Maintain excellent PPE compliance across field operations.",
            "ppe_level": "Level 2",
            "message": "Full PPE ensemble inspected and verified.",
            "next_training": "PPE_02"
        },
    ]

    for res in results_data:
        existing = db.query(models.TrainingResult).filter(
            models.TrainingResult.worker_id == res["worker_id"],
            models.TrainingResult.scenario_id == res["scenario_id"]
        ).first()
        if not existing:
            db.add(models.TrainingResult(**res))

    # 5. Sample Initial Events
    events_data = [
        {"event_id": "seed_evt_001", "worker_id": "W001", "scenario_id": "FIRE_01", "action": "TRAINING_STARTED", "timestamp": 1727351000},
        {"event_id": "seed_evt_002", "worker_id": "W001", "scenario_id": "FIRE_01", "action": "ALARM_TRIGGERED", "timestamp": 1727351010},
        {"event_id": "seed_evt_003", "worker_id": "W001", "scenario_id": "FIRE_01", "action": "EXTINGUISHER_USED", "timestamp": 1727351030},
        {"event_id": "seed_evt_004", "worker_id": "W001", "scenario_id": "FIRE_01", "action": "SAFE_EXIT", "timestamp": 1727351060},
    ]
    for ev in events_data:
        existing = db.query(models.Event).filter(models.Event.event_id == ev["event_id"]).first()
        if not existing:
            db.add(models.Event(**ev))

    # 6. Sample Recommendations
    recs_data = [
        {"worker_id": "W001", "title": "PPE Level 2", "message": "Practice helmet, gloves, goggles and safety-shoe selection.", "module_id": "PPE_01"},
        {"worker_id": "W001", "title": "Gas refresher", "message": "Repeat the gas-leak response scenario and review the shutdown sequence.", "module_id": "GAS_01"},
        {"worker_id": "W002", "title": "PPE Compliance Drills", "message": "Mandatory review of personal protective equipment.", "module_id": "PPE_01"},
        {"worker_id": "W003", "title": "Advanced Leadership Drill", "message": "Proceed to team evacuation leader module.", "module_id": "FIRE_ADVANCED"},
    ]
    for r in recs_data:
        existing = db.query(models.Recommendation).filter(
            models.Recommendation.worker_id == r["worker_id"],
            models.Recommendation.title == r["title"]
        ).first()
        if not existing:
            db.add(models.Recommendation(**r))

    # 7. Sample Certificates
    certs_data = [
        {
            "worker_id": "W001",
            "certificate_id": "SURAKSHA-W001-2026",
            "verification_token": "SURAKSHA-W001-2026",
            "status": "Certified",
        },
        {
            "worker_id": "W003",
            "certificate_id": "SURAKSHA-W003-2026",
            "verification_token": "SURAKSHA-W003-2026",
            "status": "Certified",
        },
    ]
    for c in certs_data:
        existing = db.query(models.Certificate).filter(models.Certificate.worker_id == c["worker_id"]).first()
        if not existing:
            db.add(models.Certificate(**c))

    db.commit()
    print("[Seed] Database successfully populated with initial data.")


if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        seed_database(session)
    finally:
        session.close()
