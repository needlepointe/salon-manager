from datetime import datetime, date
from sqlalchemy import (
    Integer, String, Boolean, Text, Date, DateTime, Numeric,
    ForeignKey, func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Client(Base):
    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    email: Mapped[str | None] = mapped_column(String(120), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    first_visit_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    last_visit_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    total_visits: Mapped[int] = mapped_column(Integer, default=0)
    total_spent: Mapped[float] = mapped_column(Numeric(10, 2), default=0.00)
    is_lapsed: Mapped[bool] = mapped_column(Boolean, default=False)
    hair_profile: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    gdpr_consent: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )

    # Relationships
    appointments: Mapped[list["Appointment"]] = relationship(  # type: ignore[name-defined]  # noqa
        "Appointment", back_populates="client", cascade="all, delete-orphan"
    )
    waitlist_entries: Mapped[list["WaitlistEntry"]] = relationship(
        "WaitlistEntry", back_populates="client", cascade="all, delete-orphan"
    )
    sms_messages: Mapped[list["SmsMessage"]] = relationship(  # type: ignore[name-defined]  # noqa
        "SmsMessage", back_populates="client"
    )
    extension_lead: Mapped["ExtensionLead | None"] = relationship(  # type: ignore[name-defined]  # noqa
        "ExtensionLead", back_populates="client", uselist=False
    )


class WaitlistEntry(Base):
    __tablename__ = "waitlist_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    client_id: Mapped[int] = mapped_column(Integer, ForeignKey("clients.id"), nullable=False)
    desired_service: Mapped[str] = mapped_column(String(60), nullable=False)
    desired_date_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    desired_date_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    flexibility_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="waiting")  # waiting/offered/booked/expired
    notified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    client: Mapped["Client"] = relationship("Client", back_populates="waitlist_entries")
