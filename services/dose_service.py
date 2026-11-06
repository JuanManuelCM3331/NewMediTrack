from datetime import date, datetime, time, timedelta
import json
import re

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from core.time_utils import get_app_now_naive, get_app_timezone, get_app_today
from models import Dose, Treatment
from schemas.dose_schema import DoseDecisionResponse, DoseOut
from services.treatment_service import list_treatments


def parse_dosage_quantity(dosage_str: str) -> int:
    """Extrae la cantidad numérica de la dosis para descontar stock (por defecto 1)."""
    match = re.search(r"(\d+)", dosage_str)
    if match:
        val = int(match.group(1))
        return val if 0 < val <= 1000 else 1
    return 1


def ensure_due_doses(db: Session, user_id: int, for_date: date | None = None) -> list[Dose]:
    """Garantiza que todas las dosis de la jornada existan en la base de datos."""
    day = for_date or get_app_today()
    now = get_app_now_naive()
    treatments = list_treatments(db, user_id, active=True)

    for treatment in treatments:
        end_date = treatment.start_date + timedelta(days=treatment.duration_days - 1)
        if not (treatment.start_date <= day <= end_date):
            continue
        try:
            times = json.loads(treatment.schedule_times)
        except (json.JSONDecodeError, TypeError):
            continue

        for scheduled_time in times:
            parts = scheduled_time.split(":")
            if len(parts) != 2:
                continue
            hour, minute = int(parts[0]), int(parts[1])
            scheduled_at = datetime.combine(day, time(hour, minute))

            existing = db.scalar(
                select(Dose).where(
                    Dose.treatment_id == treatment.id,
                    Dose.scheduled_at == scheduled_at,
                )
            )
            if not existing:
                db.add(
                    Dose(
                        user_id=user_id,
                        treatment_id=treatment.id,
                        scheduled_at=scheduled_at,
                        status="pending",
                        created_at=now,
                    )
                )
    db.commit()

    start_of_day = datetime.combine(day, time.min)
    end_of_day = datetime.combine(day + timedelta(days=1), time.min)
    return list(
        db.scalars(
            select(Dose)
            .options(joinedload(Dose.treatment).joinedload(Treatment.medication))
            .where(
                Dose.user_id == user_id,
                Dose.scheduled_at >= start_of_day,
                Dose.scheduled_at < end_of_day,
            )
            .order_by(Dose.scheduled_at)
        )
    )


def get_today_schedule(db: Session, user_id: int) -> list[dict]:
    """Obtiene y calcula el estado dinámico y cuenta regresiva de las dosis de hoy."""
    doses = ensure_due_doses(db, user_id)
    now = get_app_now_naive()
    tz = get_app_timezone()
    data = []

    for dose in doses:
        # Reactivación automática de dosis pospuestas si se cumplió el tiempo
        if dose.status == "snoozed" and now >= dose.scheduled_at:
            dose.status = "pending"
            dose.created_at = now

        minutes_left = None
        is_due = False

        if dose.status == "pending":
            effective_start = max(dose.scheduled_at, dose.created_at if dose.created_at else dose.scheduled_at)
            deadline = effective_start + timedelta(minutes=5)

            if now < dose.scheduled_at:
                is_due = False
                minutes_left = None
            elif now <= deadline:
                is_due = True
                minutes_left = max(0, int((deadline - now).total_seconds() // 60))
            else:
                dose.status = "missed"
                dose.decided_at = now
                is_due = False
                minutes_left = None

        iso_scheduled = dose.scheduled_at.replace(tzinfo=tz).isoformat()
        data.append({
            "id": dose.id,
            "treatment_id": dose.treatment_id,
            "medication_name": dose.treatment.medication.name if (dose.treatment and dose.treatment.medication) else "Desconocido",
            "dosage": dose.treatment.dosage if dose.treatment else "",
            "scheduled_at": iso_scheduled,
            "status": dose.status,
            "minutes_left": minutes_left,
            "is_due": is_due,
        })

    db.commit()
    return data


def decide_dose(db: Session, user_id: int, dose_id: int, decision: str) -> tuple[dict, str]:
    """Ejecuta la decisión sobre una dosis (tomada o pospuesta) y sincroniza existencias."""
    dose = db.scalar(
        select(Dose)
        .options(joinedload(Dose.treatment).joinedload(Treatment.medication))
        .where(Dose.id == dose_id, Dose.user_id == user_id)
    )
    if not dose:
        raise ValueError("Dosis no encontrada")
    if dose.status == "missed" and decision == "snoozed":
        raise ValueError("No puedes posponer una dosis que ya fue omitida")

    now = get_app_now_naive()
    medication = dose.treatment.medication if dose.treatment else None
    qty = parse_dosage_quantity(dose.treatment.dosage) if dose.treatment else 1

    # Descuento o restitución de stock
    if decision == "taken" and dose.status != "taken":
        if medication:
            medication.stock = max(0, medication.stock - qty)
    elif dose.status == "taken" and decision != "taken":
        if medication:
            medication.stock += qty

    if decision == "snoozed":
        dose.status = "snoozed"
        dose.scheduled_at = now + timedelta(minutes=10)
        dose.decided_at = now
    else:
        dose.status = decision
        dose.decided_at = now

    db.commit()
    if medication:
        db.refresh(medication)

    msg = "Dosis registrada como tomada" if decision == "taken" else "Dosis pospuesta 10 minutos"
    if decision == "taken" and medication:
        if medication.stock == 0:
            msg += f" (¡Existencias agotadas de {medication.name}!)"
        elif medication.stock <= 3:
            msg += f" (Quedan pocas existencias de {medication.name}: {medication.stock} disp.)"

    tz = get_app_timezone()
    payload = {
        "id": dose.id,
        "status": dose.status,
        "scheduled_at": dose.scheduled_at.replace(tzinfo=tz).isoformat(),
        "medication_stock": medication.stock if medication else 0,
    }
    return payload, msg
