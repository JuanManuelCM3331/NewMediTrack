from sqlalchemy import select
from sqlalchemy.orm import Session

from models import Medication
from schemas.medication_schema import MedicationCreate, MedicationUpdate


def list_medications(
    db: Session,
    user_id: int,
    search: str | None = None,
    offset: int = 0,
    limit: int = 50,
) -> list[Medication]:
    query = (
        select(Medication)
        .where(Medication.owner_id == user_id)
        .order_by(Medication.name)
        .offset(offset)
        .limit(limit)
    )
    if search:
        query = query.where(Medication.name.ilike(f"%{search}%"))
    return list(db.scalars(query))


def get_medication(db: Session, medication_id: int, user_id: int) -> Medication | None:
    medication = db.get(Medication, medication_id)
    if not medication or medication.owner_id != user_id:
        return None
    return medication


def create_medication(db: Session, user_id: int, payload: MedicationCreate) -> Medication:
    medication = Medication(owner_id=user_id, **payload.model_dump())
    db.add(medication)
    db.commit()
    db.refresh(medication)
    return medication


def update_medication(db: Session, medication: Medication, payload: MedicationUpdate) -> Medication:
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(medication, key, value)
    db.commit()
    db.refresh(medication)
    return medication


def delete_medication(db: Session, medication: Medication) -> None:
    db.delete(medication)
    db.commit()
