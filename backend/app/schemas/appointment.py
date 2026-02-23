from datetime import datetime
from pydantic import BaseModel, model_validator


class AppointmentCreate(BaseModel):
    client_id: int
    service_type: str
    duration_minutes: int
    price: float
    start_datetime: datetime
    notes: str | None = None
    deposit_paid: bool = False
    deposit_amount: float = 0.0

    @model_validator(mode="after")
    def compute_end_datetime(self) -> "AppointmentCreate":
        # end_datetime is computed from start + duration
        return self

    @property
    def end_datetime(self) -> datetime:
        from datetime import timedelta
        return self.start_datetime + timedelta(minutes=self.duration_minutes)


class AppointmentUpdate(BaseModel):
    service_type: str | None = None
    duration_minutes: int | None = None
    price: float | None = None
    status: str | None = None
    start_datetime: datetime | None = None
    notes: str | None = None
    deposit_paid: bool | None = None
    deposit_amount: float | None = None
    cancellation_reason: str | None = None


class AppointmentRead(BaseModel):
    id: int
    client_id: int
    service_type: str
    duration_minutes: int
    price: float
    status: str
    start_datetime: datetime
    end_datetime: datetime
    google_event_id: str | None
    notes: str | None
    deposit_paid: bool
    deposit_amount: float
    cancellation_reason: str | None
    created_at: datetime

    # Nested client info
    client_name: str | None = None
    client_phone: str | None = None

    model_config = {"from_attributes": True}


class AppointmentListItem(BaseModel):
    id: int
    client_id: int
    client_name: str | None = None
    service_type: str
    price: float
    status: str
    start_datetime: datetime
    end_datetime: datetime
    deposit_paid: bool

    model_config = {"from_attributes": True}
