import json
from tests.conftest import TestingSessionLocal
from dependencies import create_access_token
from models import Dose, Medication, Treatment, User
from time_utils import get_app_now_naive, get_app_today


def create_test_user_and_token():
    db = TestingSessionLocal()
    user = User(
        email="dosesrouter@test.com",
        full_name="Doses Router User",
        password_hash="fakehash",
        role="user",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token(user)
    user_id = user.id
    db.close()
    return user_id, token


def test_dedicated_doses_router_endpoints(client):
    """Verifica que el nuevo router desacoplado /api/doses funcione con contratos ApiResponse tipados."""
    user_id, token = create_test_user_and_token()
    db = TestingSessionLocal()
    today = get_app_today()
    now = get_app_now_naive()

    med = Medication(owner_id=user_id, name="Paracetamol", presentation="Tableta", stock=20)
    db.add(med)
    db.commit()
    db.refresh(med)

    treatment = Treatment(
        owner_id=user_id,
        medication_id=med.id,
        dosage="1 tableta",
        schedule_times=json.dumps(["08:00", "20:00"]),
        start_date=today,
        duration_days=3,
        active=True,
    )
    db.add(treatment)
    db.commit()
    db.refresh(treatment)

    # 1. Probar GET /api/doses/today
    res = client.get("/api/doses/today", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    assert isinstance(body["data"], list)
    assert len(body["data"]) == 2
    dose_id = body["data"][0]["id"]

    # 2. Probar POST /api/doses/{id}/decision?decision=taken
    dec_res = client.post(
        f"/api/doses/{dose_id}/decision?decision=taken",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert dec_res.status_code == 200
    dec_body = dec_res.json()
    assert dec_body["success"] is True
    assert dec_body["data"]["status"] == "taken"
    assert dec_body["data"]["medication_stock"] == 19
