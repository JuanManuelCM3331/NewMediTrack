from datetime import date
import json

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from core.exceptions import DomainError
from core.time_utils import get_app_now_naive, get_app_today
from models import (
    Dose,
    LINK_ACCEPTED,
    LINK_PENDING,
    LINK_REJECTED,
    Medication,
    MedicationSchemaTemplate,
    PatientLink,
    ROLE_USER,
    Treatment,
    User,
)
from schemas.medication_schema import MedicationOut
from schemas.patient_admin_schema import SchemaTemplateCreate
from services.dose_service import get_today_schedule
from services.medication_service import list_medications
from services.treatment_service import list_treatments, serialize_treatment
from services.user_service import get_user_by_email


def serialize_link(link: PatientLink) -> dict:
    return {
        "id": link.id,
        "manager_id": link.manager_id,
        "manager_name": link.manager.full_name if link.manager else "Administrador",
        "manager_email": link.manager.email if link.manager else "",
        "patient_id": link.patient_id,
        "patient_name": link.patient.full_name if link.patient else "Paciente",
        "patient_email": link.patient.email if link.patient else "",
        "status": link.status,
        "created_at": link.created_at,
        "responded_at": link.responded_at,
    }


def create_link_request(db: Session, manager: User, patient_email: str) -> dict:
    target = get_user_by_email(db, patient_email.strip().lower())
    if not target or not target.is_active:
        raise DomainError("No se encontró una cuenta de usuario activa con ese correo", status_code=404)
    if target.id == manager.id or target.role != ROLE_USER:
        raise DomainError("Solo puedes enviar solicitudes de enlace a cuentas de usuario paciente", status_code=422)

    existing = db.scalar(
        select(PatientLink)
        .options(joinedload(PatientLink.manager), joinedload(PatientLink.patient))
        .where(PatientLink.manager_id == manager.id, PatientLink.patient_id == target.id)
    )
    if existing:
        if existing.status == LINK_ACCEPTED:
            raise DomainError("Ya estás enlazado con este paciente", status_code=409)
        if existing.status == LINK_PENDING:
            raise DomainError("Ya enviaste una solicitud pendiente a este paciente", status_code=409)
        existing.status = LINK_PENDING
        existing.created_at = get_app_now_naive()
        existing.responded_at = None
        db.commit()
        db.refresh(existing)
        return serialize_link(existing)

    link = PatientLink(
        manager_id=manager.id,
        patient_id=target.id,
        status=LINK_PENDING,
    )
    db.add(link)
    db.commit()
    db.refresh(link)
    link.manager = manager
    link.patient = target
    return serialize_link(link)


def list_manager_links(db: Session, manager_id: int) -> list[dict]:
    links = list(
        db.scalars(
            select(PatientLink)
            .options(joinedload(PatientLink.manager), joinedload(PatientLink.patient))
            .where(PatientLink.manager_id == manager_id)
            .order_by(PatientLink.created_at.desc())
        ).unique()
    )
    return [serialize_link(item) for item in links]


def list_patient_links(db: Session, patient_id: int) -> list[dict]:
    links = list(
        db.scalars(
            select(PatientLink)
            .options(joinedload(PatientLink.manager), joinedload(PatientLink.patient))
            .where(PatientLink.patient_id == patient_id)
            .order_by(PatientLink.created_at.desc())
        ).unique()
    )
    return [serialize_link(item) for item in links]


def respond_link_request(db: Session, patient: User, link_id: int, decision: str) -> dict:
    link = db.scalar(
        select(PatientLink)
        .options(joinedload(PatientLink.manager), joinedload(PatientLink.patient))
        .where(PatientLink.id == link_id, PatientLink.patient_id == patient.id)
    )
    if not link:
        raise DomainError("Solicitud de enlace no encontrada", status_code=404)

    normalized = decision.strip().lower()
    if normalized in {"accept", "accepted"}:
        link.status = LINK_ACCEPTED
    elif normalized in {"reject", "rejected"}:
        link.status = LINK_REJECTED
    else:
        raise DomainError("La decisión debe ser accept o reject", status_code=422)

    link.responded_at = get_app_now_naive()
    db.commit()
    db.refresh(link)
    return serialize_link(link)


def delete_link(db: Session, user: User, link_id: int) -> None:
    link = db.get(PatientLink, link_id)
    if not link or (link.manager_id != user.id and link.patient_id != user.id):
        raise DomainError("Enlace no encontrado", status_code=404)
    db.delete(link)
    db.commit()


def require_accepted_patient(db: Session, manager_id: int, patient_id: int) -> User:
    link = db.scalar(
        select(PatientLink).where(
            PatientLink.manager_id == manager_id,
            PatientLink.patient_id == patient_id,
            PatientLink.status == LINK_ACCEPTED,
        )
    )
    if not link:
        raise DomainError("No tienes un enlace activo y aceptado con este paciente", status_code=403)
    patient = db.get(User, patient_id)
    if not patient or not patient.is_active:
        raise DomainError("El paciente no está disponible", status_code=404)
    return patient


def get_patient_overview(db: Session, manager_id: int, patient_id: int) -> dict:
    patient = require_accepted_patient(db, manager_id, patient_id)
    medications = [MedicationOut.model_validate(m) for m in list_medications(db, patient.id)]
    treatments = [serialize_treatment(t) for t in list_treatments(db, patient.id)]
    today_doses = get_today_schedule(db, patient.id)

    today_total = len(today_doses)
    today_taken = sum(1 for d in today_doses if d["status"] == "taken")
    today_pending = sum(1 for d in today_doses if d["status"] == "pending")
    today_snoozed = sum(1 for d in today_doses if d["status"] == "snoozed")
    today_missed = sum(1 for d in today_doses if d["status"] == "missed")

    history_taken = (
        db.scalar(
            select(func.count(Dose.id)).where(
                Dose.user_id == patient.id,
                Dose.status == "taken",
            )
        )
        or 0
    )
    history_missed = (
        db.scalar(
            select(func.count(Dose.id)).where(
                Dose.user_id == patient.id,
                Dose.status == "missed",
            )
        )
        or 0
    )

    decided_total = history_taken + history_missed
    adherence_rate = round((history_taken / decided_total) * 100) if decided_total > 0 else 100
    today_progress_rate = round((today_taken / today_total) * 100) if today_total > 0 else 0
    low_stock_count = sum(1 for m in medications if m.stock <= 5)
    active_treatments_count = sum(1 for t in treatments if t.get("active", True))

    return {
        "patient_id": patient.id,
        "patient_name": patient.full_name,
        "patient_email": patient.email,
        "medications": medications,
        "treatments": treatments,
        "today_doses": today_doses,
        "stats": {
            "medications_count": len(medications),
            "low_stock_count": low_stock_count,
            "active_treatments_count": active_treatments_count,
            "today_total": today_total,
            "today_taken": today_taken,
            "today_pending": today_pending,
            "today_snoozed": today_snoozed,
            "today_missed": today_missed,
            "today_progress_rate": today_progress_rate,
            "adherence_rate": adherence_rate,
            "history_taken_doses": history_taken,
            "history_missed_doses": history_missed,
        },
    }


def serialize_schema_template(tpl: MedicationSchemaTemplate) -> dict:
    try:
        times = json.loads(tpl.schedule_times)
    except (json.JSONDecodeError, TypeError):
        times = []
    return {
        "id": tpl.id,
        "title": tpl.title,
        "medication_name": tpl.medication_name,
        "presentation": tpl.presentation,
        "default_stock": tpl.default_stock,
        "dosage": tpl.dosage,
        "schedule_times": times,
        "duration_days": tpl.duration_days,
        "instructions": tpl.instructions,
        "notes": tpl.notes,
    }


def list_schema_templates(db: Session, manager_id: int) -> list[dict]:
    items = list(
        db.scalars(
            select(MedicationSchemaTemplate)
            .where(MedicationSchemaTemplate.manager_id == manager_id)
            .order_by(MedicationSchemaTemplate.created_at.desc())
        )
    )
    return [serialize_schema_template(item) for item in items]


def create_schema_template(db: Session, manager_id: int, payload: SchemaTemplateCreate) -> dict:
    tpl = MedicationSchemaTemplate(
        manager_id=manager_id,
        title=payload.title,
        medication_name=payload.medication_name,
        presentation=payload.presentation,
        default_stock=payload.default_stock,
        dosage=payload.dosage,
        schedule_times=json.dumps(payload.schedule_times),
        duration_days=payload.duration_days,
        instructions=payload.instructions,
        notes=payload.notes,
    )
    db.add(tpl)
    db.commit()
    db.refresh(tpl)
    return serialize_schema_template(tpl)


def delete_schema_template(db: Session, manager_id: int, schema_id: int) -> None:
    tpl = db.get(MedicationSchemaTemplate, schema_id)
    if not tpl or tpl.manager_id != manager_id:
        raise DomainError("Esquema no encontrado", status_code=404)
    db.delete(tpl)
    db.commit()


def apply_schema_to_patient(
    db: Session,
    manager_id: int,
    patient_id: int,
    schema_id: int,
    start_date: date | None = None,
) -> dict:
    patient = require_accepted_patient(db, manager_id, patient_id)
    tpl = db.get(MedicationSchemaTemplate, schema_id)
    if not tpl or tpl.manager_id != manager_id:
        raise DomainError("Esquema no encontrado", status_code=404)

    medication = Medication(
        owner_id=patient.id,
        name=tpl.medication_name,
        presentation=tpl.presentation,
        stock=tpl.default_stock,
        notes=tpl.notes,
    )
    db.add(medication)
    db.commit()
    db.refresh(medication)

    treatment = Treatment(
        owner_id=patient.id,
        medication_id=medication.id,
        dosage=tpl.dosage,
        schedule_times=tpl.schedule_times,
        start_date=start_date or get_app_today(),
        duration_days=tpl.duration_days,
        instructions=tpl.instructions,
        active=True,
    )
    db.add(treatment)
    db.commit()
    db.refresh(treatment)
    treatment.medication = medication

    today_doses = get_today_schedule(db, patient.id)
    return {
        "medication": MedicationOut.model_validate(medication),
        "treatment": serialize_treatment(treatment),
        "today_doses": today_doses,
    }
