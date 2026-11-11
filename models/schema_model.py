from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base
from core.time_utils import get_app_now_naive


class MedicationSchemaTemplate(Base):
    __tablename__ = "medication_schemas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    manager_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    medication_name: Mapped[str] = mapped_column(String(120), nullable=False)
    presentation: Mapped[str] = mapped_column(String(80), default="Tableta", nullable=False)
    default_stock: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    dosage: Mapped[str] = mapped_column(String(80), nullable=False)
    schedule_times: Mapped[str] = mapped_column(Text, nullable=False)
    duration_days: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=get_app_now_naive, nullable=False)

    manager = relationship("User", foreign_keys=[manager_id])
