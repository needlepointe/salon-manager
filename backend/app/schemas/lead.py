from datetime import datetime
from pydantic import BaseModel


class LeadCreate(BaseModel):
    name: str
    phone: str
    email: str | None = None
    source: str | None = None
    hair_length: str | None = None
    hair_texture: str | None = None
    desired_length: str | None = None
    desired_color: str | None = None
    extension_type: str | None = None
    budget_range: str | None = None
    timeline: str | None = None
    notes: str | None = None


class LeadUpdate(BaseModel):
    name: str | None = None
    phone: str | None = None
    email: str | None = None
    source: str | None = None
    hair_length: str | None = None
    hair_texture: str | None = None
    desired_length: str | None = None
    desired_color: str | None = None
    extension_type: str | None = None
    budget_range: str | None = None
    timeline: str | None = None
    pipeline_stage: str | None = None
    quote_amount: float | None = None
    quote_text: str | None = None
    notes: str | None = None
    next_follow_up_at: datetime | None = None
    client_id: int | None = None


class LeadRead(BaseModel):
    id: int
    client_id: int | None
    name: str
    phone: str
    email: str | None
    source: str | None
    hair_length: str | None
    hair_texture: str | None
    desired_length: str | None
    desired_color: str | None
    extension_type: str | None
    budget_range: str | None
    timeline: str | None
    ai_qualification_score: int | None
    ai_qualification_tier: str | None
    ai_qualification_notes: str | None
    pipeline_stage: str
    quote_amount: float | None
    quote_text: str | None
    quote_sent_at: datetime | None
    follow_up_count: int
    last_follow_up_at: datetime | None
    next_follow_up_at: datetime | None
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class LeadPipelineSummary(BaseModel):
    new: int = 0
    contacted: int = 0
    qualified: int = 0
    quoted: int = 0
    follow_up: int = 0
    booked: int = 0
    lost: int = 0
