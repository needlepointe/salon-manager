from datetime import datetime
from pydantic import BaseModel


class SmsMessageRead(BaseModel):
    id: int
    client_id: int | None
    lead_id: int | None
    phone_number: str
    direction: str
    body: str
    twilio_sid: str | None
    status: str
    message_type: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatSessionCreate(BaseModel):
    channel: str = "web"
    client_id: int | None = None


class ChatSessionRead(BaseModel):
    id: int
    session_token: str
    client_id: int | None
    channel: str
    messages_json: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatMessage(BaseModel):
    role: str  # user/assistant
    content: str


class SendMessageRequest(BaseModel):
    content: str
