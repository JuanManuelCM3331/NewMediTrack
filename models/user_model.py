from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base
from core.time_utils import get_app_now_naive

ROLE_ADMIN = "admin"
ROLE_USER = "user"
ROLE_PATIENT_ADMIN = "patient_admin"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(30), default=ROLE_USER, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=get_app_now_naive, nullable=False)

    medications = relationship("Medication", back_populates="owner", cascade="all, delete-orphan")
    treatments = relationship("Treatment", back_populates="owner", cascade="all, delete-orphan")
    doses = relationship("Dose", back_populates="user", cascade="all, delete-orphan")
