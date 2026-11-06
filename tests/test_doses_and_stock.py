import json
from datetime import date, datetime, time, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base, get_db
from dependencies import create_access_token
from main import app
from models import Dose, Medication, Treatment, User
from time_utils import get_app_now_naive, get_app_today, get_app_timezone

TEST_ENGINE = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=TEST_ENGINE, autoflush=False, autocommit=False, expire_on_commit=False)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=TEST_ENGINE)
    yield
    Base.metadata.drop_all(bind=TEST_ENGINE)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def create_test_user_and_token():
    db = TestingSessionLocal()
    user = User(
        email="paciente@test.com",
        full_name="Paciente Prueba",
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


def test_ensure_due_doses_generates_all_doses_of_the_day():
    """2.1: Verifica que las dosis futuras del día no se omitan y aparezcan en la agenda."""
    user_id, token = create_test_user_and_token()
    db = TestingSessionLocal()
    today = get_app_today()

    med = Medication(owner_id=user_id, name="Ibuprofeno", presentation="Tableta", stock=20)
    db.add(med)
    db.commit()
    db.refresh(med)

    treatment = Treatment(
        owner_id=user_id,
        medication_id=med.id,
        dosage="1 tableta",
        schedule_times=json.dumps(["07:00", "14:00", "23:30"]),
        start_date=today,
        duration_days=5,
        active=True,
    )
    db.add(treatment)
    db.commit()
    db.close()

    response = client.get("/api/treatments/schedule/today", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()["data"]

    # Deben existir exactamente las 3 dosis programadas para hoy
    assert len(data) == 3
    times = [d["scheduled_at"] for d in data]
    assert any("07:00" in t for t in times)
    assert any("14:00" in t for t in times)
    assert any("23:30" in t for t in times)

    # La dosis futura de las 23:30 debe estar en estado 'pending'
    future_dose = [d for d in data if "23:30" in d["scheduled_at"]][0]
    assert future_dose["status"] == "pending"


def test_avoid_false_instant_missed_dose():
    """2.1: Verifica que si una dosis se genera después de la hora programada, tenga ventana de gracia."""
    user_id, token = create_test_user_and_token()
    db = TestingSessionLocal()
    now = get_app_now_naive()

    med = Medication(owner_id=user_id, name="Omeprazol", presentation="Cápsula", stock=15)
    db.add(med)
    db.commit()
    db.refresh(med)

    treatment = Treatment(
        owner_id=user_id,
        medication_id=med.id,
        dosage="1 cápsula",
        schedule_times=json.dumps(["06:00"]),
        start_date=now.date(),
        duration_days=3,
        active=True,
    )
    db.add(treatment)
    db.commit()
    db.refresh(treatment)

    past_time = now - timedelta(minutes=20)
    dose = Dose(
        user_id=user_id,
        treatment_id=treatment.id,
        scheduled_at=past_time,
        status="pending",
        created_at=now,  # Creada hace 0 minutos
    )
    db.add(dose)
    db.commit()
    db.refresh(dose)
    dose_id = dose.id
    db.close()

    response = client.get("/api/treatments/schedule/today", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()["data"]
    test_dose = [d for d in data if d["id"] == dose_id][0]

    # No debe marcarse instantáneamente como 'missed' porque se acaba de crear
    assert test_dose["status"] == "pending"
    assert test_dose["is_due"] is True
    assert test_dose["minutes_left"] is not None


def test_snooze_reschedules_and_reactivates():
    """2.2: Verifica que 'snoozed' pospone 10 minutos la dosis y se reactiva al cumplirse el tiempo."""
    user_id, token = create_test_user_and_token()
    db = TestingSessionLocal()
    now = get_app_now_naive()

    med = Medication(owner_id=user_id, name="Loratadina", presentation="Tableta", stock=10)
    db.add(med)
    db.commit()
    db.refresh(med)

    treatment = Treatment(
        owner_id=user_id,
        medication_id=med.id,
        dosage="1 tableta",
        schedule_times=json.dumps(["08:00"]),
        start_date=now.date(),
        duration_days=3,
        active=True,
    )
    db.add(treatment)
    db.commit()
    db.refresh(treatment)

    dose = Dose(
        user_id=user_id,
        treatment_id=treatment.id,
        scheduled_at=now,
        status="pending",
        created_at=now,
    )
    db.add(dose)
    db.commit()
    db.refresh(dose)
    dose_id = dose.id
    db.close()

    # Usuario pospone la dosis 10 minutos
    res = client.post(f"/api/treatments/doses/{dose_id}/decision?decision=snoozed", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    body = res.json()
    assert body["data"]["status"] == "snoozed"

    # Verificar en BD que scheduled_at se desplazó aproximadamente 10 minutos al futuro
    db = TestingSessionLocal()
    db_dose = db.get(Dose, dose_id)
    diff_minutes = (db_dose.scheduled_at - now).total_seconds() / 60
    assert 9 <= diff_minutes <= 11
    db.close()

    # Si simulamos que ya transcurrieron los 10 minutos
    db = TestingSessionLocal()
    db_dose = db.get(Dose, dose_id)
    db_dose.scheduled_at = now - timedelta(seconds=1)
    db.commit()
    db.close()

    # Al consultar la agenda, la dosis pospuesta debe reactivarse automáticamente a 'pending'
    res_agenda = client.get("/api/treatments/schedule/today", headers={"Authorization": f"Bearer {token}"})
    agenda_doses = res_agenda.json()["data"]
    snoozed_dose = [d for d in agenda_doses if d["id"] == dose_id][0]
    assert snoozed_dose["status"] == "pending"
    assert snoozed_dose["is_due"] is True


def test_stock_reduction_on_dose_taken():
    """2.3: Verifica que al tomar una dosis se descuente el inventario de medicamento."""
    user_id, token = create_test_user_and_token()
    db = TestingSessionLocal()
    now = get_app_now_naive()

    # Stock inicial = 10
    med = Medication(owner_id=user_id, name="Amoxicilina", presentation="Cápsula", stock=10)
    db.add(med)
    db.commit()
    db.refresh(med)
    med_id = med.id

    treatment = Treatment(
        owner_id=user_id,
        medication_id=med_id,
        dosage="2 cápsulas",  # Debería descontar 2 unidades
        schedule_times=json.dumps(["12:00"]),
        start_date=now.date(),
        duration_days=5,
        active=True,
    )
    db.add(treatment)
    db.commit()
    db.refresh(treatment)

    dose = Dose(
        user_id=user_id,
        treatment_id=treatment.id,
        scheduled_at=now,
        status="pending",
        created_at=now,
    )
    db.add(dose)
    db.commit()
    db.refresh(dose)
    dose_id = dose.id
    db.close()

    # Marcar dosis como tomada
    res = client.post(f"/api/treatments/doses/{dose_id}/decision?decision=taken", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.json()["data"]["medication_stock"] == 8

    # Verificar persistencia en base de datos
    db = TestingSessionLocal()
    updated_med = db.get(Medication, med_id)
    assert updated_med.stock == 8
    db.close()


def test_timezone_iso_offset_included():
    """2.4: Verifica que las fechas retornadas incluyan el offset de zona horaria de la app."""
    user_id, token = create_test_user_and_token()
    db = TestingSessionLocal()
    today = get_app_today()

    med = Medication(owner_id=user_id, name="Vitamina C", presentation="Tableta", stock=30)
    db.add(med)
    db.commit()
    db.refresh(med)

    treatment = Treatment(
        owner_id=user_id,
        medication_id=med.id,
        dosage="1 tableta",
        schedule_times=json.dumps(["09:00"]),
        start_date=today,
        duration_days=1,
        active=True,
    )
    db.add(treatment)
    db.commit()
    db.close()

    res = client.get("/api/treatments/schedule/today", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    doses = res.json()["data"]
    assert len(doses) >= 1
    # Verifica que el ISO string contenga el offset de zona horaria (ej: -05:00)
    assert "-05:00" in doses[0]["scheduled_at"]
