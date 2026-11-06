import json
from datetime import date, datetime, time, timedelta

import bcrypt
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from models import Dose, Medication, Treatment, User, ROLE_USER
from time_utils import get_app_now_naive, get_app_today


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email.lower()))


def create_user(db: Session, email: str, full_name: str, password: str, role: str = ROLE_USER) -> User:
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


def get_admin_summary(db: Session) -> dict[str, int]:
    return {
        "users": db.scalar(select(func.count()).select_from(User)) or 0,
        "medications": db.scalar(select(func.count()).select_from(Medication)) or 0,
        "treatments": db.scalar(select(func.count()).select_from(Treatment)) or 0,
    }


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


def ensure_due_doses(db: Session, user_id: int, for_date: date | None = None) -> list[Dose]:
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
                    Dose.scheduled_at == scheduled_at
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
