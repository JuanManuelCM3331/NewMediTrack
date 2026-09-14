from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class Dose(Base):
    __tablename__ = "doses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    treatment_id: Mapped[int] = mapped_column(ForeignKey("treatments.id", ondelete="CASCADE"), index=True, nullable=False)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime, index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    user = relationship("User", back_populates="doses")
    treatment = relationship("Treatment", back_populates="doses")
