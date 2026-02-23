from datetime import datetime
from pydantic import BaseModel


class ReportRead(BaseModel):
    id: int
    report_month: str
    revenue_total: float
    appointments_count: int
    new_clients_count: int
    lapsed_recovered: int
    leads_converted: int
    top_services_json: str | None
    inventory_spend: float
    ai_summary_text: str | None
    ai_generated_at: datetime | None
    charts_data_json: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DashboardStats(BaseModel):
    today_revenue: float
    today_appointments: int
    today_appointments_completed: int
    month_revenue: float
    month_new_clients: int
    active_leads: int
    low_stock_count: int
    lapsed_clients_count: int
    pending_aftercare_count: int
    upcoming_appointments: list[dict]


class AlertItem(BaseModel):
    type: str  # low_stock/lapsed_client/pending_aftercare/lead_followup/appointment_review
    severity: str  # high/medium/low
    title: str
    description: str
    action_url: str | None = None
    entity_id: int | None = None


class AftercareSequenceRead(BaseModel):
    id: int
    appointment_id: int
    client_id: int
    client_name: str | None = None
    service_type: str | None = None
    appointment_date: datetime | None = None
    d3_sent_at: datetime | None
    d3_response: str | None
    w2_sent_at: datetime | None
    w2_response: str | None
    upsell_offer_sent: bool
    upsell_converted: bool
    created_at: datetime

    model_config = {"from_attributes": True}
