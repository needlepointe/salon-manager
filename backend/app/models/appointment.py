from datetime import datetime
from sqlalchemy import (
    Integer, String, Boolean, Text, DateTime, Numeric,
    ForeignKey, func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Appointment(Base):
    __tablename__ = "appointments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    client_id: Mapped[int] = mapped_column(Integer, ForeignKey("clients.id"), nullable=False)
    service_type: Mapped[str] = mapped_column(String(60), nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    price: Mapped[float] = mapped_column(Numeric(8, 2), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default="scheduled"
    )  # scheduled/completed/cancelled/no_show/needs_review
    start_datetime: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_datetime: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    google_event_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    deposit_paid: Mapped[bool] = mapped_column(Boolean, default=False)
    deposit_amount: Mapped[float] = mapped_column(Numeric(8, 2), default=0.00)
    cancellation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )

    # Relationships
    client: Mapped["Client"] = relationship("Client", back_populates="appointments")  # type: ignore[name-defined]  # noqa
    aftercare_sequence: Mapped["AftercareSequence | None"] = relationship(  # type: ignore[name-defined]  # noqa
        "AftercareSequence", back_populates="appointment", uselist=False
    )
    inventory_transactions: Mapped[list["InventoryTransaction"]] = relationship(  # type: ignore[name-defined]  # noqa
        "InventoryTransaction", back_populates="appointment"
    )
