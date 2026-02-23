from datetime import datetime
from sqlalchemy import (
    Integer, String, Text, DateTime, ForeignKey, func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class SmsMessage(Base):
    __tablename__ = "sms_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    client_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("clients.id"), nullable=True
    )
    lead_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("extension_leads.id"), nullable=True
    )
    appointment_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("appointments.id"), nullable=True
    )
    phone_number: Mapped[str] = mapped_column(String(20), nullable=False)
    direction: Mapped[str] = mapped_column(String(10), nullable=False)  # inbound/outbound
    body: Mapped[str] = mapped_column(Text, nullable=False)
    twilio_sid: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), default="sent"
    )  # sent/delivered/failed/received
    message_type: Mapped[str | None] = mapped_column(
        String(40), nullable=True
    )  # reminder/lapsed_outreach/aftercare_d3/aftercare_w2/quote/manual/follow_up
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    client: Mapped["Client | None"] = relationship("Client", back_populates="sms_messages")  # type: ignore[name-defined]  # noqa
    lead: Mapped["ExtensionLead | None"] = relationship("ExtensionLead", back_populates="sms_messages")  # type: ignore[name-defined]  # noqa


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_token: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    client_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("clients.id"), nullable=True
    )
    channel: Mapped[str] = mapped_column(String(20), default="web")  # web/sms
    messages_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )
