from datetime import datetime, date
from pydantic import BaseModel, EmailStr, field_validator
import re


class ClientBase(BaseModel):
    full_name: str
    phone: str
    email: str | None = None
    notes: str | None = None
    hair_profile: str | None = None  # JSON string
    gdpr_consent: bool = False

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        # Strip whitespace and common formatting
        cleaned = re.sub(r"[\s\-\(\)\.]+", "", v)
        if not cleaned.startswith("+"):
            cleaned = "+1" + cleaned.lstrip("1")
        if not re.match(r"^\+\d{10,15}$", cleaned):
            raise ValueError("Phone must be in E.164 format (e.g. +12125551234)")
        return cleaned


class ClientCreate(ClientBase):
    first_visit_date: date | None = None


class ClientUpdate(BaseModel):
    full_name: str | None = None
    phone: str | None = None
    email: str | None = None
    notes: str | None = None
    hair_profile: str | None = None
    gdpr_consent: bool | None = None
    is_lapsed: bool | None = None


class ClientRead(ClientBase):
    id: int
    first_visit_date: date | None
    last_visit_date: date | None
    total_visits: int
    total_spent: float
    is_lapsed: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ClientListItem(BaseModel):
    id: int
    full_name: str
    phone: str
    email: str | None
    last_visit_date: date | None
    total_visits: int
    total_spent: float
    is_lapsed: bool

    model_config = {"from_attributes": True}


class WaitlistEntryCreate(BaseModel):
    client_id: int
    desired_service: str
    desired_date_from: date | None = None
    desired_date_to: date | None = None
    flexibility_notes: str | None = None


class WaitlistEntryRead(WaitlistEntryCreate):
    id: int
    status: str
    notified_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}
