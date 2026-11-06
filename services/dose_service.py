from datetime import date, datetime, time, timedelta
import json
import re

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from core.exceptions import ConflictError, NotFoundError
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
    """Garantiza que todas las dosis de la jornada existan en la base de datos sin duplicar pospuestas."""
    day = for_date or get_app_today()
    now = get_app_now_naive()
    start_of_day = datetime.combine(day, time.min)
    end_of_day = datetime.combine(day + timedelta(days=1), time.min)
    treatments = list_treatments(db, user_id, active=True)

    for treatment in treatments:
        end_date = treatment.start_date + timedelta(days=treatment.duration_days - 1)
        if not (treatment.start_date <= day <= end_date):
            continue
        try:
            times = json.loads(treatment.schedule_times)
        except (json.JSONDecodeError, TypeError):
            continue

        scheduled_slots: list[datetime] = []
        for scheduled_time in times:
            parts = scheduled_time.split(":")
            if len(parts) != 2:
                continue
            hour, minute = int(parts[0]), int(parts[1])
            scheduled_slots.append(datetime.combine(day, time(hour, minute)))

        if not scheduled_slots:
            continue

        existing_day_doses = list(
            db.scalars(
                select(Dose).where(
                    Dose.treatment_id == treatment.id,
                    Dose.scheduled_at >= start_of_day,
                    Dose.scheduled_at < end_of_day,
                )
            )
        )

        # Si ya existen todas las dosis del día para este tratamiento (incluyendo pospuestas), no duplicar
        if len(existing_day_doses) >= len(scheduled_slots):
            continue

        existing_times = {d.scheduled_at for d in existing_day_doses}
        missing_count = len(scheduled_slots) - len(existing_day_doses)

        for scheduled_at in scheduled_slots:
            if missing_count <= 0:
                break
            if scheduled_at not in existing_times:
                db.add(
                    Dose(
                        user_id=user_id,
                        treatment_id=treatment.id,
                        scheduled_at=scheduled_at,
                        status="pending",
                        created_at=now,
                    )
                )
                existing_times.add(scheduled_at)
                missing_count -= 1
    db.commit()

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

        # La dosis solo se puede tomar desde 15 min antes hasta 15 min después de scheduled_at
        diff_seconds = (now - dose.scheduled_at).total_seconds()
        can_take = (
            (dose.status in {"pending", "snoozed"})
            and (-15 * 60 <= diff_seconds <= 15 * 60)
        )

        iso_scheduled = dose.scheduled_at.replace(tzinfo=tz).isoformat()
        data.append({
            "id": dose.id,
            "treatment_id": dose.treatment_id,
            "medication_name": dose.treatment.medication.name if (dose.treatment and dose.treatment.medication) else "Desconocido",
            "dosage": dose.treatment.dosage if dose.treatment else "",
            "notes": dose.treatment.medication.notes if (dose.treatment and dose.treatment.medication) else None,
            "instructions": dose.treatment.instructions if dose.treatment else None,
            "scheduled_at": iso_scheduled,
            "status": dose.status,
            "minutes_left": minutes_left,
            "is_due": is_due,
            "can_take": can_take,
        })

    db.commit()
    return data


def get_upcoming_schedule(db: Session, user_id: int, limit: int = 10) -> list[dict]:
    """Obtiene las próximas dosis a consumir en general (hoy y días posteriores), hasta alcanzar el límite."""
    today = get_app_today()
    tz = get_app_timezone()

    # 1. Obtener y actualizar el estado dinámico de las dosis de hoy
    today_doses = get_today_schedule(db, user_id)
    # Filtrar las pendientes o pospuestas de hoy
    upcoming: list[dict] = [d for d in today_doses if d["status"] in {"pending", "snoozed"}]

    # 2. Si se necesitan más para alcanzar el límite, buscar en días posteriores
    if len(upcoming) < limit:
        for day_offset in range(1, 61):
            if len(upcoming) >= limit:
                break
            future_date = today + timedelta(days=day_offset)
            future_doses = ensure_due_doses(db, user_id, for_date=future_date)
            for dose in future_doses:
                if dose.status in {"pending", "snoozed"}:
                    iso_scheduled = dose.scheduled_at.replace(tzinfo=tz).isoformat()
                    upcoming.append({
                        "id": dose.id,
                        "treatment_id": dose.treatment_id,
                        "medication_name": dose.treatment.medication.name if (dose.treatment and dose.treatment.medication) else "Desconocido",
                        "dosage": dose.treatment.dosage if dose.treatment else "",
                        "notes": dose.treatment.medication.notes if (dose.treatment and dose.treatment.medication) else None,
                        "instructions": dose.treatment.instructions if dose.treatment else None,
                        "scheduled_at": iso_scheduled,
                        "status": dose.status,
                        "minutes_left": None,
                        "is_due": False,
                        "can_take": False,
                    })
                    if len(upcoming) >= limit:
                        break

    return upcoming[:limit]


def decide_dose(db: Session, user_id: int, dose_id: int, decision: str) -> tuple[dict, str]:
    """Ejecuta la decisión sobre una dosis (tomada, pospuesta u omitida) y sincroniza existencias."""
    dose = db.scalar(
        select(Dose)
        .options(joinedload(Dose.treatment).joinedload(Treatment.medication))
        .where(Dose.id == dose_id, Dose.user_id == user_id)
    )
    if not dose:
        raise NotFoundError("Dosis no encontrada")
    if dose.status == "taken":
        raise ConflictError("Esta dosis ya fue registrada como tomada")
    if dose.status == "missed" and decision == "snoozed":
        raise ConflictError("No puedes posponer una dosis que ya fue omitida")

    now = get_app_now_naive()
    diff_seconds = (now - dose.scheduled_at).total_seconds()

    # Validación: no se puede tomar, posponer ni marcar como no tomada si aún no está en el rango de tiempo
    # (El rango comienza 15 minutos antes de la hora programada)
    if diff_seconds < -15 * 60:
        mins_to_wait = int((-diff_seconds) // 60)
        action_verb = "tomar" if decision == "taken" else ("posponer" if decision == "snoozed" else "registrar como no tomada")
        raise ConflictError(
            f"Aún no estás en el rango de tiempo para {action_verb} este medicamento. "
            f"Estará disponible 15 minutos antes de su hora programada (en {mins_to_wait} min)."
        )

    # Si ya expiró la ventana (más de 15 minutos después de la hora programada)
    if diff_seconds > 15 * 60:
        if decision == "taken":
            raise ConflictError("El tiempo para tomar esta dosis ya expiró (más de 15 minutos después de la hora programada).")
        elif decision == "snoozed":
            raise ConflictError("El tiempo para posponer esta dosis ya expiró.")

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

    if decision == "taken":
        msg = "Dosis registrada como tomada"
    elif decision == "snoozed":
        msg = "Dosis pospuesta 10 minutos"
    else:
        msg = "Dosis registrada como no tomada"
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
