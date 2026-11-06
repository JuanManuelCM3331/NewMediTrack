import json
from datetime import timedelta
from tests.conftest import TestingSessionLocal
from core.security import create_access_token
from core.time_utils import get_app_now_naive, get_app_today
from models import Dose, Medication, Treatment, User


def create_test_user_and_token(email: str = "dosesrouter@test.com"):
    db = TestingSessionLocal()
    user = User(
        email=email,
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

    # Usamos la hora actual formateada para que la dosis esté exactamente dentro de la ventana de +/- 15 min
    current_time_str = now.strftime("%H:%M")
    later_time = (now + timedelta(hours=6)).strftime("%H:%M")

    treatment = Treatment(
        owner_id=user_id,
        medication_id=med.id,
        dosage="1 tableta",
        schedule_times=json.dumps([current_time_str, later_time]),
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

    # 3. Probar GET /api/doses/upcoming (dosis a consumir en general, incluyendo días siguientes)
    up_res = client.get("/api/doses/upcoming?limit=5", headers={"Authorization": f"Bearer {token}"})
    assert up_res.status_code == 200
    up_body = up_res.json()
    assert up_body["success"] is True
    assert isinstance(up_body["data"], list)
    assert len(up_body["data"]) >= 1


def test_cannot_snooze_or_miss_future_dose_out_of_window(client):
    """Verifica que una dosis que no está en el rango de tiempo no pueda tomarse, posponerse ni marcarse como no tomada."""
    user_id, token = create_test_user_and_token("window_test@example.com")
    db = TestingSessionLocal()
    today = get_app_today()
    now = get_app_now_naive()

    med = Medication(owner_id=user_id, name="Ibuprofeno", presentation="Cápsula", stock=15)
    db.add(med)
    db.commit()
    db.refresh(med)

    # Dosis 4 horas en el futuro (fuera del rango de 15 min antes)
    future_time_str = (now + timedelta(hours=4)).strftime("%H:%M")
    treatment = Treatment(
        owner_id=user_id,
        medication_id=med.id,
        dosage="1 cápsula",
        schedule_times=json.dumps([future_time_str]),
        start_date=today,
        duration_days=2,
        active=True,
    )
    db.add(treatment)
    db.commit()

    # Generar la dosis mediante la consulta de hoy
    res = client.get("/api/doses/today", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    doses = res.json()["data"]
    assert len(doses) == 1
    future_dose_id = doses[0]["id"]
    assert doses[0]["can_take"] is False

    # 1. Intentar posponer la dosis futura -> debe ser rechazada con 409
    snooze_res = client.post(
        f"/api/doses/{future_dose_id}/decision?decision=snoozed",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert snooze_res.status_code == 409

    # 2. Intentar marcar como no tomada la dosis futura -> debe ser rechazada con 409
    miss_res = client.post(
        f"/api/doses/{future_dose_id}/decision?decision=missed",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert miss_res.status_code == 409

    # 3. Intentar tomar la dosis futura -> debe ser rechazada con 409
    take_res = client.post(
        f"/api/doses/{future_dose_id}/decision?decision=taken",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert take_res.status_code == 409
