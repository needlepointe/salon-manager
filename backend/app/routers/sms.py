"""
Twilio SMS webhook receiver + internal SMS sending.
The /webhook endpoint is public-facing and Twilio-signed.
"""
import json
from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.client import Client
from app.models.communication import SmsMessage, ChatSession
from app.services.twilio_service import twilio_service
from app.services.ai.chat_agent import get_sms_response
from app.config import get_settings
import secrets

router = APIRouter(prefix="/sms", tags=["sms"])
settings = get_settings()


@router.post("/webhook")
async def twilio_webhook(
    request: Request,
    From: str = Form(...),
    Body: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Twilio inbound SMS webhook.
    Validates signature, routes to keyword handler or AI chatbot.
    """
    # Validate Twilio signature
    form_data = dict(await request.form())
    signature = request.headers.get("X-Twilio-Signature", "")
    url = str(request.url)

    if not twilio_service.validate_webhook_signature(url, form_data, signature):
        raise HTTPException(status_code=403, detail="Invalid Twilio signature")

    from_number = From.strip()
    body_text = Body.strip()

    # Log inbound message
    # Look up client by phone
    result = await db.execute(select(Client).where(Client.phone == from_number))
    client = result.scalar_one_or_none()

    inbound_msg = SmsMessage(
        client_id=client.id if client else None,
        phone_number=from_number,
        direction="inbound",
        body=body_text,
        status="received",
        message_type="inbound",
    )
    db.add(inbound_msg)
    await db.flush()

    # Keyword routing
    body_upper = body_text.upper().strip()
    response_text = None

    if body_upper in ("CANCEL", "STOP", "UNSUBSCRIBE"):
        response_text = (
            f"Got it! To cancel your appointment, please call or text {settings.stylist_name} directly. "
            "Reply HELP for more options."
        )
    elif body_upper in ("BOOK", "REBOOK", "SCHEDULE"):
        booking_link = settings.booking_link or f"Contact {settings.stylist_name} to book"
        response_text = (
            f"Hi! To book an appointment: {booking_link}\n"
            f"Or reply with your preferred date and I'll check availability for you!"
        )
    elif body_upper == "HELP":
        response_text = (
            f"Hi! I'm {settings.stylist_name}'s assistant for {settings.salon_name}.\n"
            "Reply: BOOK to schedule • CANCEL to cancel • or ask me anything about services & pricing!"
        )
    else:
        # Route to AI FAQ chatbot
        # Get or create SMS chat session for this phone number
        session_token = f"sms_{from_number.replace('+', '')}"
        session_result = await db.execute(
            select(ChatSession).where(ChatSession.session_token == session_token)
        )
        session = session_result.scalar_one_or_none()
        if not session:
            session = ChatSession(
                session_token=session_token,
                client_id=client.id if client else None,
                channel="sms",
                messages_json="[]",
            )
            db.add(session)
            await db.flush()

        try:
            messages = json.loads(session.messages_json)
        except Exception:
            messages = []

        messages.append({"role": "user", "content": body_text})
        ai_response = await get_sms_response(messages)
        messages.append({"role": "assistant", "content": ai_response})
        session.messages_json = json.dumps(messages[-20:])  # Keep last 20 messages

        response_text = ai_response

    # Send response
    if response_text:
        sid = twilio_service.send_sms(from_number, response_text[:1600])
        db.add(SmsMessage(
            client_id=client.id if client else None,
            phone_number=from_number,
            direction="outbound",
            body=response_text[:1600],
            twilio_sid=sid,
            status="sent",
            message_type="auto_reply",
        ))

    await db.commit()

    # Return empty TwiML (we already sent via API, no need for TwiML response)
    return Response(
        content='<?xml version="1.0" encoding="UTF-8"?><Response></Response>',
        media_type="application/xml",
    )


@router.post("/send")
async def send_sms(
    to: str,
    body: str,
    message_type: str = "manual",
    client_id: int | None = None,
    lead_id: int | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Internal endpoint to send an outbound SMS."""
    sid = twilio_service.send_sms(to, body)
    msg = SmsMessage(
        client_id=client_id,
        lead_id=lead_id,
        phone_number=to,
        direction="outbound",
        body=body,
        twilio_sid=sid,
        status="sent" if sid else "failed",
        message_type=message_type,
    )
    db.add(msg)
    await db.commit()
    return {"message": "SMS sent", "twilio_sid": sid}


@router.get("/history/{client_id}", response_model=list)
async def get_sms_history(client_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(SmsMessage)
        .where(SmsMessage.client_id == client_id)
        .order_by(SmsMessage.created_at.desc())
        .limit(50)
    )
    messages = result.scalars().all()
    return [
        {
            "id": m.id,
            "direction": m.direction,
            "body": m.body,
            "status": m.status,
            "message_type": m.message_type,
            "created_at": m.created_at.isoformat(),
        }
        for m in messages
    ]
