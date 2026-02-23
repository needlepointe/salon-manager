from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_, func
from app.database import get_db
from app.models.client import Client, WaitlistEntry
from app.models.appointment import Appointment
from app.schemas.client import (
    ClientCreate, ClientUpdate, ClientRead, ClientListItem, WaitlistEntryCreate, WaitlistEntryRead
)

router = APIRouter(prefix="/clients", tags=["clients"])


@router.get("/", response_model=list[ClientListItem])
async def list_clients(
    search: str | None = Query(None),
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    query = select(Client)
    if search:
        query = query.where(
            or_(
                Client.full_name.ilike(f"%{search}%"),
                Client.phone.ilike(f"%{search}%"),
                Client.email.ilike(f"%{search}%"),
            )
        )
    query = query.order_by(Client.full_name).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/", response_model=ClientRead, status_code=201)
async def create_client(data: ClientCreate, db: AsyncSession = Depends(get_db)):
    # Check phone uniqueness
    existing = await db.execute(select(Client).where(Client.phone == data.phone))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="A client with this phone number already exists.")

    client = Client(**data.model_dump())
    db.add(client)
    await db.flush()
    await db.refresh(client)
    return client


@router.get("/lapsed", response_model=list[ClientListItem])
async def list_lapsed_clients(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Client)
        .where(Client.is_lapsed == True)  # noqa: E712
        .order_by(Client.last_visit_date.asc())
    )
    return result.scalars().all()


@router.get("/{client_id}", response_model=ClientRead)
async def get_client(client_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Client).where(Client.id == client_id))
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client


@router.put("/{client_id}", response_model=ClientRead)
async def update_client(
    client_id: int, data: ClientUpdate, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Client).where(Client.id == client_id))
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(client, field, value)
    await db.flush()
    await db.refresh(client)
    return client


@router.get("/{client_id}/timeline")
async def get_client_timeline(client_id: int, db: AsyncSession = Depends(get_db)):
    """Return the full communication + appointment timeline for a client."""
    from app.models.communication import SmsMessage
    from app.models.report import AftercareSequence

    result = await db.execute(select(Client).where(Client.id == client_id))
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    # Appointments
    appts_result = await db.execute(
        select(Appointment)
        .where(Appointment.client_id == client_id)
        .order_by(Appointment.start_datetime.desc())
        .limit(20)
    )
    appointments = appts_result.scalars().all()

    # SMS history
    sms_result = await db.execute(
        select(SmsMessage)
        .where(SmsMessage.client_id == client_id)
        .order_by(SmsMessage.created_at.desc())
        .limit(30)
    )
    sms_messages = sms_result.scalars().all()

    return {
        "client": {
            "id": client.id,
            "full_name": client.full_name,
            "phone": client.phone,
            "email": client.email,
            "total_visits": client.total_visits,
            "total_spent": float(client.total_spent),
            "is_lapsed": client.is_lapsed,
            "hair_profile": client.hair_profile,
        },
        "appointments": [
            {
                "id": a.id,
                "service_type": a.service_type,
                "status": a.status,
                "price": float(a.price),
                "start_datetime": a.start_datetime.isoformat(),
                "notes": a.notes,
            }
            for a in appointments
        ],
        "sms_messages": [
            {
                "id": m.id,
                "direction": m.direction,
                "body": m.body,
                "status": m.status,
                "message_type": m.message_type,
                "created_at": m.created_at.isoformat(),
            }
            for m in sms_messages
        ],
    }


@router.post("/{client_id}/sms-outreach")
async def send_lapsed_outreach(client_id: int, db: AsyncSession = Depends(get_db)):
    """Generate an AI-drafted lapsed outreach SMS and send it via Twilio."""
    from app.services.ai.lead_qualifier import draft_lapsed_outreach
    from app.services.twilio_service import twilio_service
    from app.models.communication import SmsMessage

    result = await db.execute(select(Client).where(Client.id == client_id))
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    # Get last service
    appt_result = await db.execute(
        select(Appointment)
        .where(
            and_(
                Appointment.client_id == client_id,
                Appointment.status == "completed",
            )
        )
        .order_by(Appointment.start_datetime.desc())
        .limit(1)
    )
    last_appt = appt_result.scalar_one_or_none()
    last_service = last_appt.service_type if last_appt else "hair appointment"

    weeks_since = 0
    if client.last_visit_date:
        weeks_since = (datetime.now().date() - client.last_visit_date).days // 7

    client_data = {
        "full_name": client.full_name,
        "last_service": last_service,
        "weeks_since_visit": weeks_since,
        "total_visits": client.total_visits,
    }

    message_body = await draft_lapsed_outreach(client_data)
    sid = twilio_service.send_sms(client.phone, message_body)

    # Log the message
    sms = SmsMessage(
        client_id=client.id,
        phone_number=client.phone,
        direction="outbound",
        body=message_body,
        twilio_sid=sid,
        status="sent",
        message_type="lapsed_outreach",
    )
    db.add(sms)

    # Mark as no longer lapsed (outreach was sent)
    client.is_lapsed = False
    await db.commit()

    return {"message": "Outreach sent", "body": message_body, "twilio_sid": sid}


# Waitlist
@router.post("/waitlist/", response_model=WaitlistEntryRead, status_code=201)
async def add_to_waitlist(data: WaitlistEntryCreate, db: AsyncSession = Depends(get_db)):
    entry = WaitlistEntry(**data.model_dump())
    db.add(entry)
    await db.flush()
    await db.refresh(entry)
    return entry


@router.get("/waitlist/", response_model=list[WaitlistEntryRead])
async def list_waitlist(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(WaitlistEntry)
        .where(WaitlistEntry.status == "waiting")
        .order_by(WaitlistEntry.created_at.asc())
    )
    return result.scalars().all()
