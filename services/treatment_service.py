import json
from sqlalchemy import delete, select
from sqlalchemy.orm import Session, joinedload

from models import Dose, Medication, Treatment
from schemas.treatment_schema import TreatmentCreate, TreatmentUpdate


def serialize_treatment(treatment: Treatment) -> dict:
    try:
        schedule = json.loads(treatment.schedule_times)
    except (json.JSONDecodeError, TypeError):
        schedule = []
    return {
        "id": treatment.id,
        "medication_id": treatment.medication_id,
        "medication_name": treatment.medication.name if treatment.medication else "Desconocido",
        "dosage": treatment.dosage,
        "schedule_times": schedule,
        "start_date": treatment.start_date,
        "duration_days": treatment.duration_days,
        "instructions": treatment.instructions,
        "active": treatment.active,
    }


def list_treatments(db: Session, user_id: int, active: bool | None = None) -> list[Treatment]:
    query = (
        select(Treatment)
        .options(joinedload(Treatment.medication))
        .where(Treatment.owner_id == user_id)
        .order_by(Treatment.active.desc(), Treatment.start_date.desc())
    )
    if active is not None:
        query = query.where(Treatment.active == active)
    return list(db.scalars(query).unique())


def get_treatment(db: Session, treatment_id: int, user_id: int) -> Treatment | None:
    return db.scalar(
        select(Treatment)
        .options(joinedload(Treatment.medication))
        .where(Treatment.id == treatment_id, Treatment.owner_id == user_id)
    )


def create_treatment(db: Session, user_id: int, medication: Medication, payload: TreatmentCreate) -> Treatment:
    treatment = Treatment(
        owner_id=user_id,
        schedule_times=json.dumps(payload.schedule_times),
        **payload.model_dump(exclude={"schedule_times"}),
    )
    db.add(treatment)
    db.commit()
    db.refresh(treatment)
    treatment.medication = medication
    return treatment


def update_treatment(db: Session, treatment: Treatment, payload: TreatmentUpdate) -> Treatment:
    values = payload.model_dump(exclude_unset=True)
    schedule_updated = "schedule_times" in values
    if schedule_updated:
        treatment.schedule_times = json.dumps(values.pop("schedule_times"))
    for key, value in values.items():
        setattr(treatment, key, value)

    if schedule_updated:
        # Limpiar dosis pendientes sin decisión previa para regenerar según el nuevo horario
        db.execute(
            delete(Dose).where(
                Dose.treatment_id == treatment.id,
                Dose.status == "pending",
                Dose.decided_at.is_(None),
            )
        )

    db.commit()
    db.refresh(treatment)
    treatment.medication = db.get(Medication, treatment.medication_id)
    return treatment


def delete_treatment(db: Session, treatment: Treatment) -> None:
    db.delete(treatment)
    db.commit()
