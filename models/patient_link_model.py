from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base
from core.time_utils import get_app_now_naive

LINK_PENDING = "pending"
LINK_ACCEPTED = "accepted"
LINK_REJECTED = "rejected"


class PatientLink(Base):
    __tablename__ = "patient_links"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    manager_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    patient_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default=LINK_PENDING, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=get_app_now_naive, nullable=False)
    responded_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    manager = relationship("User", foreign_keys=[manager_id])
    patient = relationship("User", foreign_keys=[patient_id])
