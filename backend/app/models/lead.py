from datetime import datetime
from sqlalchemy import (
    Integer, String, Boolean, Text, DateTime, Numeric,
    ForeignKey, func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class ExtensionLead(Base):
    __tablename__ = "extension_leads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    client_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("clients.id"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    email: Mapped[str | None] = mapped_column(String(120), nullable=True)
    source: Mapped[str | None] = mapped_column(String(60), nullable=True)  # instagram/referral/walk-in/website

    # Hair profile
    hair_length: Mapped[str | None] = mapped_column(String(30), nullable=True)   # short/medium/long/extra-long
    hair_texture: Mapped[str | None] = mapped_column(String(30), nullable=True)
    desired_length: Mapped[str | None] = mapped_column(String(30), nullable=True)
    desired_color: Mapped[str | None] = mapped_column(String(60), nullable=True)
    extension_type: Mapped[str | None] = mapped_column(String(60), nullable=True)  # tape-in/weft/nano/keratin
    budget_range: Mapped[str | None] = mapped_column(String(40), nullable=True)
    timeline: Mapped[str | None] = mapped_column(String(40), nullable=True)

    # AI qualification
    ai_qualification_score: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 0-100
    ai_qualification_tier: Mapped[str | None] = mapped_column(String(20), nullable=True)  # hot/warm/cold/unqualified
    ai_qualification_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Pipeline
    pipeline_stage: Mapped[str] = mapped_column(
        String(30), default="new"
    )  # new/contacted/qualified/quoted/follow_up/booked/lost

    # Quote
    quote_amount: Mapped[float | None] = mapped_column(Numeric(8, 2), nullable=True)
    quote_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    quote_sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Follow-up
    follow_up_count: Mapped[int] = mapped_column(Integer, default=0)
    last_follow_up_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    next_follow_up_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )

    # Relationships
    client: Mapped["Client | None"] = relationship("Client", back_populates="extension_lead")  # type: ignore[name-defined]  # noqa
    sms_messages: Mapped[list["SmsMessage"]] = relationship(  # type: ignore[name-defined]  # noqa
        "SmsMessage", back_populates="lead"
    )
