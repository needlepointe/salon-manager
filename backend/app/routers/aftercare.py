from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.database import get_db
from app.models.report import AftercareSequence
from app.models.appointment import Appointment
from app.models.client import Client
from app.models.communication import SmsMessage
from app.services.twilio_service import twilio_service
from app.config import get_settings

router = APIRouter(prefix="/aftercare", tags=["aftercare"])
settings = get_settings()


@router.get("/")
async def list_sequences(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(AftercareSequence, Appointment, Client)
        .join(Appointment, AftercareSequence.appointment_id == Appointment.id)
        .join(Client, AftercareSequence.client_id == Client.id)
        .order_by(AftercareSequence.created_at.desc())
        .limit(50)
    )
    rows = result.all()
    return [
        {
            "id": seq.id,
            "appointment_id": seq.appointment_id,
            "client_id": seq.client_id,
            "client_name": client.full_name,
            "service_type": appt.service_type,
            "appointment_date": appt.start_datetime.isoformat(),
            "d3_sent_at": seq.d3_sent_at.isoformat() if seq.d3_sent_at else None,
            "d3_response": seq.d3_response,
            "w2_sent_at": seq.w2_sent_at.isoformat() if seq.w2_sent_at else None,
            "w2_response": seq.w2_response,
            "upsell_offer_sent": seq.upsell_offer_sent,
            "upsell_converted": seq.upsell_converted,
        }
        for seq, appt, client in rows
    ]


@router.get("/pending")
async def get_pending_sequences(db: AsyncSession = Depends(get_db)):
    """Sequences where D3 or W2 is due but not yet sent."""
    now = datetime.now()
    d3_threshold = now - timedelta(days=3)
    w2_threshold = now - timedelta(days=14)

    # D3 pending
    d3_result = await db.execute(
        select(AftercareSequence, Appointment, Client)
        .join(Appointment, AftercareSequence.appointment_id == Appointment.id)
        .join(Client, AftercareSequence.client_id == Client.id)
        .where(
            and_(
                AftercareSequence.d3_sent_at.is_(None),
                Appointment.end_datetime <= d3_threshold,
                Appointment.status == "completed",
            )
        )
    )
    # W2 pending
    w2_result = await db.execute(
        select(AftercareSequence, Appointment, Client)
        .join(Appointment, AftercareSequence.appointment_id == Appointment.id)
        .join(Client, AftercareSequence.client_id == Client.id)
        .where(
            and_(
                AftercareSequence.w2_sent_at.is_(None),
                AftercareSequence.d3_sent_at.is_not(None),
                Appointment.end_datetime <= w2_threshold,
                Appointment.status == "completed",
            )
        )
    )

    pending = []
    for seq, appt, client in d3_result.all():
        pending.append({
            "id": seq.id,
            "type": "d3",
            "client_name": client.full_name,
            "service_type": appt.service_type,
            "appointment_date": appt.start_datetime.isoformat(),
        })
    for seq, appt, client in w2_result.all():
        pending.append({
            "id": seq.id,
            "type": "w2",
            "client_name": client.full_name,
            "service_type": appt.service_type,
            "appointment_date": appt.start_datetime.isoformat(),
        })

    return pending


@router.post("/{sequence_id}/send-d3")
async def send_d3(sequence_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(AftercareSequence, Appointment, Client)
        .join(Appointment, AftercareSequence.appointment_id == Appointment.id)
        .join(Client, AftercareSequence.client_id == Client.id)
        .where(AftercareSequence.id == sequence_id)
    )
    row = result.one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Aftercare sequence not found")
    seq, appt, client = row

    body = (
        f"Hi {client.full_name.split()[0]}! It's been 3 days since your {appt.service_type}. "
        f"How are you loving your hair? Any aftercare questions? I'm always here to help! "
        f"— {settings.stylist_name}"
    )
    sid = twilio_service.send_sms(client.phone, body)
    sms = SmsMessage(
        client_id=client.id,
        appointment_id=appt.id,
        phone_number=client.phone,
        direction="outbound",
        body=body,
        twilio_sid=sid,
        status="sent",
        message_type="aftercare_d3",
    )
    db.add(sms)
    await db.flush()
    seq.d3_sent_at = datetime.now()
    seq.d3_sms_id = sms.id
    await db.commit()
    return {"message": "D3 aftercare sent", "body": body}


@router.post("/{sequence_id}/send-w2")
async def send_w2(sequence_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(AftercareSequence, Appointment, Client)
        .join(Appointment, AftercareSequence.appointment_id == Appointment.id)
        .join(Client, AftercareSequence.client_id == Client.id)
        .where(AftercareSequence.id == sequence_id)
    )
    row = result.one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Aftercare sequence not found")
    seq, appt, client = row

    body = (
        f"Hi {client.full_name.split()[0]}! Two weeks since your {appt.service_type} — "
        f"your extensions should be feeling totally natural by now! 🌟 "
        f"Ready for your next visit? Reply BOOK and I'll get you sorted! "
        f"— {settings.stylist_name}"
    )
    sid = twilio_service.send_sms(client.phone, body)
    sms = SmsMessage(
        client_id=client.id,
        appointment_id=appt.id,
        phone_number=client.phone,
        direction="outbound",
        body=body,
        twilio_sid=sid,
        status="sent",
        message_type="aftercare_w2",
    )
    db.add(sms)
    await db.flush()
    seq.w2_sent_at = datetime.now()
    seq.w2_sms_id = sms.id
    seq.upsell_offer_sent = True
    await db.commit()
    return {"message": "W2 aftercare sent", "body": body}


@router.put("/{sequence_id}/response")
async def record_response(
    sequence_id: int,
    response_type: str,  # "d3" or "w2"
    response_text: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AftercareSequence).where(AftercareSequence.id == sequence_id)
    )
    seq = result.scalar_one_or_none()
    if not seq:
        raise HTTPException(status_code=404, detail="Aftercare sequence not found")

    if response_type == "d3":
        seq.d3_response = response_text
    elif response_type == "w2":
        seq.w2_response = response_text
    else:
        raise HTTPException(status_code=400, detail="response_type must be 'd3' or 'w2'")

    await db.commit()
    return {"message": "Response recorded"}
