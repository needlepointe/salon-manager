from datetime import datetime
from sqlalchemy import (
    Integer, String, Boolean, Text, DateTime, Numeric,
    ForeignKey, func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class AftercareSequence(Base):
    __tablename__ = "aftercare_sequences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    appointment_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("appointments.id"), unique=True, nullable=False
    )
    client_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("clients.id"), nullable=False
    )
    d3_sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    d3_response: Mapped[str | None] = mapped_column(Text, nullable=True)
    d3_sms_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("sms_messages.id"), nullable=True
    )
    w2_sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    w2_response: Mapped[str | None] = mapped_column(Text, nullable=True)
    w2_sms_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("sms_messages.id"), nullable=True
    )
    upsell_offer_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    upsell_offer_type: Mapped[str | None] = mapped_column(String(60), nullable=True)
    upsell_converted: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    appointment: Mapped["Appointment"] = relationship(  # type: ignore[name-defined]  # noqa
        "Appointment", back_populates="aftercare_sequence"
    )


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    report_month: Mapped[str] = mapped_column(String(7), unique=True, nullable=False)  # "2026-02"
    revenue_total: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    appointments_count: Mapped[int] = mapped_column(Integer, nullable=False)
    new_clients_count: Mapped[int] = mapped_column(Integer, nullable=False)
    lapsed_recovered: Mapped[int] = mapped_column(Integer, default=0)
    leads_converted: Mapped[int] = mapped_column(Integer, default=0)
    top_services_json: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    inventory_spend: Mapped[float] = mapped_column(Numeric(10, 2), default=0.00)
    ai_summary_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_generated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    charts_data_json: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )


class AppSetting(Base):
    """Key-value store for app settings (e.g., Google OAuth tokens)."""
    __tablename__ = "app_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    value: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )
