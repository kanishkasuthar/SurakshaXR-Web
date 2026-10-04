"""Comprehensive Automated Tests for Suraksha-XR FastAPI Backend."""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.scoring import ScoringEngine
from app.ai_coach import AISafetyCoach, MistakeAnalyzer


@pytest.fixture(scope="module")
def client():
    """Create test client with initialized database."""
    with TestClient(app) as c:
        yield c


# 1. Health endpoint test
def test_health_endpoints(client):
    res1 = client.get("/health")
    assert res1.status_code == 200
    assert res1.json()["status"] == "ok"
    assert res1.json()["service"] == "Suraksha-XR Backend"

    res2 = client.get("/api/health")
    assert res2.status_code == 200
    assert res2.json()["status"] == "ok"


# 2. Login test (Admin and Worker)
def test_login_admin(client):
    res = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["role"] == "admin"
    assert data["token"] == data["access_token"]


def test_login_worker(client):
    res = client.post("/api/auth/login", json={"username": "worker01", "password": "worker123"})
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["role"] == "worker"
    assert data["worker"] is not None
    assert data["worker"]["worker_id"] == "W001"
    assert data["worker"]["name"] == "Rahul Kumar"


def test_login_invalid(client):
    res = client.post("/api/auth/login", json={"username": "worker01", "password": "wrongpassword"})
    assert res.status_code == 401


# 3. Training modules test
def test_get_training_modules(client):
    res = client.get("/api/training/modules")
    assert res.status_code == 200
    modules = res.json()
    assert isinstance(modules, list)
    assert len(modules) >= 3
    mod_ids = [m["module_id"] for m in modules]
    assert "FIRE_01" in mod_ids
    assert "GAS_01" in mod_ids
    assert "PPE_01" in mod_ids


# 4. Event ingestion test
def test_event_ingestion(client):
    payload = {
        "event_id": "test_evt_1001",
        "worker_id": "W001",
        "scenario_id": "FIRE_01",
        "action": "EXTINGUISHER_USED",
        "timestamp": 1727352000,
        "metadata": {
            "object_id": "extinguisher_01",
            "position": {"x": 1.0, "y": 0.0, "z": 2.0}
        }
    }
    res = client.post("/api/v1/events", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["event_id"] == "test_evt_1001"
    assert data["worker_id"] == "W001"
    assert data["scenario_id"] == "FIRE_01"
    assert "score" in data
    assert "mistakes" in data
    assert "recommendation" in data
    assert "message" in data


# 5. Duplicate event handling (Idempotency test)
def test_duplicate_event_idempotency(client):
    payload = {
        "event_id": "test_evt_idempotent_01",
        "worker_id": "W001",
        "scenario_id": "FIRE_01",
        "action": "SAFE_EXIT",
        "timestamp": 1727352100,
    }
    res1 = client.post("/api/v1/events", json=payload)
    assert res1.status_code == 200
    first_score = res1.json()["score"]

    # Re-send same event_id
    res2 = client.post("/api/v1/events", json=payload)
    assert res2.status_code == 200
    assert res2.json()["event_id"] == "test_evt_idempotent_01"
    # Idempotent response returns successfully without errors
    assert res2.json()["score"] == first_score


# 6. Scoring engine unit verification
def test_scoring_engine():
    # Positive actions
    events = ["TRAINING_STARTED", "PPE_SELECTED", "EXTINGUISHER_USED", "SAFE_EXIT"]
    eval_res = ScoringEngine.evaluate_events(events, scenario_id="FIRE_01")
    assert eval_res["score"] > 70
    assert eval_res["mistakes"] == 0
    assert eval_res["correct_actions"] == 3

    # Negative actions
    events_with_mistakes = ["TRAINING_STARTED", "WRONG_EQUIPMENT", "WRONG_EXIT"]
    eval_res_mistakes = ScoringEngine.evaluate_events(events_with_mistakes, scenario_id="FIRE_01")
    assert eval_res_mistakes["mistakes"] == 2
    assert eval_res_mistakes["score"] < 70


# 7. Mistake analysis & AI Safety Coach verification
def test_mistake_analysis_and_ai_coach():
    detail = MistakeAnalyzer.analyze_action("WRONG_EXIT", "FIRE_01")
    assert detail is not None
    assert detail.weak_area == "Emergency Evacuation"
    assert detail.severity == "High"

    # AI Coach feedback test
    feedback = AISafetyCoach.generate_feedback(
        score=62,
        mistakes=4,
        weak_area="PPE Compliance",
        scenario_id="PPE_01",
        recent_actions=["PPE_MISSED"]
    )
    assert "PPE" in feedback["weak_area"] if "weak_area" in feedback else True
    assert "recommendation" in feedback
    assert feedback["next_training"] == "PPE_01"


# 8. Latest result endpoint test
def test_get_latest_result(client):
    res = client.get("/api/workers/W001/latest-result")
    assert res.status_code == 200
    data = res.json()
    assert data["worker_id"] == "W001"
    assert "score" in data
    assert "mistakes" in data
    assert "recommendation" in data


# 9. Safety Passport endpoint test
def test_get_passport(client):
    res = client.get("/api/workers/W001/passport")
    assert res.status_code == 200
    data = res.json()
    assert data["worker_id"] == "W001"
    assert data["worker_name"] == "Rahul Kumar"
    assert "fire_score" in data
    assert "gas_score" in data
    assert "ppe_score" in data
    assert "overall_score" in data
    assert data["status"] in ["Certified", "Training Complete", "In Progress"]


# 10. Recommendations endpoint test
def test_get_recommendations(client):
    res = client.get("/api/workers/W001/recommendations")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert "title" in data[0]
    assert "message" in data[0]


# 11. Admin workers endpoint test (Person 4 Web compatibility)
def test_get_admin_workers(client):
    res = client.get("/api/admin/workers")
    assert res.status_code == 200
    workers = res.json()
    assert isinstance(workers, list)
    assert len(workers) >= 3
    w1 = next(w for w in workers if w["worker_id"] == "W001")
    assert w1["name"] == "Rahul Kumar"
    assert "score" in w1
    assert "overall_score" in w1
    assert "fire_score" in w1
    assert "gas_score" in w1
    assert "ppe_score" in w1
    assert "status" in w1


# 12. Admin analytics endpoint test (Person 4 Web compatibility)
def test_get_admin_analytics(client):
    res = client.get("/api/admin/analytics")
    assert res.status_code == 200
    data = res.json()
    assert data["total_workers"] >= 3
    assert data["workers"] >= 3
    assert "certified" in data
    assert "training_required" in data
    assert "total_events" in data
    assert "total_trainings" in data
    assert "average_score" in data
    assert "module_scores" in data
    assert "Fire" in data["module_scores"]
    assert "Gas" in data["module_scores"]
    assert "PPE" in data["module_scores"]


# 13. Certificate retrieval and QR verification test
def test_certificate_and_verification(client):
    # Retrieve certificate
    res = client.get("/api/certificates/W001")
    assert res.status_code == 200
    cert = res.json()
    assert cert["worker_id"] == "W001"
    assert cert["certificate_id"] == "SURAKSHA-W001-2026"
    assert cert["verification_token"] == "SURAKSHA-W001-2026"

    # Verify certificate
    v_res = client.get("/api/verify/SURAKSHA-W001-2026")
    assert v_res.status_code == 200
    v_data = v_res.json()
    assert v_data["valid"] is True
    assert v_data["verified"] is True
    assert v_data["worker_id"] == "W001"

    # Verify invalid token
    inv_res = client.get("/api/verify/INVALID-TOKEN-999")
    assert inv_res.status_code == 200
    assert inv_res.json()["valid"] is False


def test_login_by_worker_id(client):
    res = client.post("/api/auth/login", json={"username": "W001", "password": "worker123"})
    assert res.status_code == 200
    assert res.json()["worker"]["worker_id"] == "W001"


def _post_event(client, event_id, action, worker="W004", scenario="FIRE_01"):
    return client.post("/api/v1/events", json={
        "event_id": event_id,
        "worker_id": worker,
        "scenario_id": scenario,
        "action": action,
        "timestamp": 1727353000,
    })


def test_scoring_wrong_only(client):
    _post_event(client, "iso_wrong_start", "TRAINING_STARTED")
    res = _post_event(client, "iso_wrong_1", "WRONG_EQUIPMENT")
    assert res.status_code == 200
    data = res.json()
    assert data["mistakes"] == 1
    assert data["score"] == 55  # BASE 70 - 15


def test_scoring_correct_only(client):
    _post_event(client, "iso_ok_start", "TRAINING_STARTED", worker="W004", scenario="GAS_01")
    res = _post_event(client, "iso_ok_1", "EXTINGUISHER_USED", worker="W004", scenario="GAS_01")
    assert res.status_code == 200
    data = res.json()
    assert data["mistakes"] == 0
    assert data["score"] == 90  # BASE 70 + 20


def test_scoring_correct_and_wrong(client):
    _post_event(client, "iso_mix_start", "TRAINING_STARTED", worker="W002", scenario="PPE_01")
    _post_event(client, "iso_mix_wrong", "WRONG_EQUIPMENT", worker="W002", scenario="PPE_01")
    res = _post_event(client, "iso_mix_ok", "EXTINGUISHER_USED", worker="W002", scenario="PPE_01")
    assert res.status_code == 200
    data = res.json()
    assert data["mistakes"] == 1
    assert data["score"] == 75  # 70 - 15 + 20


def test_scoring_multiple_wrong_actions(client):
    _post_event(client, "iso_mw_start", "TRAINING_STARTED", worker="W002", scenario="GAS_01")
    _post_event(client, "iso_mw_1", "WRONG_EQUIPMENT", worker="W002", scenario="GAS_01")
    res = _post_event(client, "iso_mw_2", "WRONG_EXIT", worker="W002", scenario="GAS_01")
    assert res.status_code == 200
    data = res.json()
    assert data["mistakes"] == 2
    assert data["score"] == 35  # 70 - 15 - 20


def test_new_session_ignores_old_events(client):
    _post_event(client, "iso_old_start", "TRAINING_STARTED", worker="W003", scenario="PPE_01")
    _post_event(client, "iso_old_wrong", "WRONG_EXIT", worker="W003", scenario="PPE_01")
    old = _post_event(client, "iso_old_wrong2", "WRONG_EQUIPMENT", worker="W003", scenario="PPE_01")
    assert old.json()["mistakes"] >= 2
    reset = _post_event(client, "iso_new_start", "TRAINING_STARTED", worker="W003", scenario="PPE_01")
    assert reset.status_code == 200
    assert reset.json()["mistakes"] == 0
    assert reset.json()["score"] == 70
    fresh = _post_event(client, "iso_new_ok", "EXTINGUISHER_USED", worker="W003", scenario="PPE_01")
    assert fresh.json()["mistakes"] == 0
    assert fresh.json()["score"] == 90
