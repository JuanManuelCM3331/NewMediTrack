import json
from datetime import date, datetime, time, timedelta

import bcrypt
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from models import Dose, Medication, Treatment, User

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email.lower()))


def create_user(db: Session, email: str, full_name: str, password: str, role: str = "user") -> User:
    user = User(email=email.lower(), full_name=full_name, password_hash=hash_password(password), role=role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user_name(db: Session, user: User, full_name: str) -> User:
    user.full_name = full_name.strip()
    db.commit()
    db.refresh(user)
    return user


def list_medications(db: Session, user_id: int, search: str | None = None, offset: int = 0, limit: int = 50) -> list[Medication]:
    query = select(Medication).where(Medication.owner_id == user_id).order_by(Medication.name).offset(offset).limit(limit)
    if search:
        query = query.where(Medication.name.ilike(f"%{search}%"))
    return list(db.scalars(query))


def list_treatments(db: Session, user_id: int, active: bool | None = None) -> list[Treatment]:
    query = select(Treatment).options(joinedload(Treatment.medication)).where(Treatment.owner_id == user_id).order_by(Treatment.active.desc(), Treatment.start_date.desc())
    if active is not None:
        query = query.where(Treatment.active == active)
    return list(db.scalars(query).unique())


def serialize_treatment(treatment: Treatment) -> dict:
    return {"id": treatment.id, "medication_id": treatment.medication_id, "medication_name": treatment.medication.name, "dosage": treatment.dosage, "schedule_times": json.loads(treatment.schedule_times), "start_date": treatment.start_date, "duration_days": treatment.duration_days, "instructions": treatment.instructions, "active": treatment.active}


def ensure_due_doses(db: Session, user_id: int, for_date: date | None = None) -> list[Dose]:
    day = for_date or date.today()
    current_time = datetime.now()
    treatments = list_treatments(db, user_id, active=True)
    for treatment in treatments:
        end_date = treatment.start_date + timedelta(days=treatment.duration_days - 1)
        if not treatment.start_date <= day <= end_date:
            continue
        for scheduled_time in json.loads(treatment.schedule_times):
            hour, minute = (int(part) for part in scheduled_time.split(":"))
            scheduled_at = datetime.combine(day, time(hour, minute))
            if scheduled_at > current_time:
                continue
            existing = db.scalar(select(Dose).where(Dose.treatment_id == treatment.id, Dose.scheduled_at == scheduled_at))
            if not existing:
                db.add(Dose(user_id=user_id, treatment_id=treatment.id, scheduled_at=scheduled_at, status="pending"))
    db.commit()
    return list(db.scalars(select(Dose).options(joinedload(Dose.treatment).joinedload(Treatment.medication)).where(Dose.user_id == user_id, Dose.scheduled_at >= datetime.combine(day, time.min), Dose.scheduled_at < datetime.combine(day + timedelta(days=1), time.min)).order_by(Dose.scheduled_at)))
