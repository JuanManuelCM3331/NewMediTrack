from sqlalchemy import func, select
from sqlalchemy.orm import Session

from core.security import hash_password
from models import Medication, Treatment, User, ROLE_USER


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email.lower()))


def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def create_user(db: Session, email: str, full_name: str, password: str, role: str = ROLE_USER) -> User:
    user = User(
        email=email.lower(),
        full_name=full_name,
        password_hash=hash_password(password),
        role=role,
    )
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
