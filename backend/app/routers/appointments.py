from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.database import get_db
from app.models.appointment import Appointment
from app.models.client import Client
from app.schemas.appointment import AppointmentCreate, AppointmentUpdate, AppointmentRead, AppointmentListItem
from app.services.google_calendar import google_calendar_service

router = APIRouter(prefix="/appointments", tags=["appointments"])


def _enrich(appt: Appointment, client: Client | None) -> dict:
    """Add client info to appointment dict."""
    return {
        **{c.key: getattr(appt, c.key) for c in appt.__table__.columns},
        "client_name": client.full_name if client else None,
        "client_phone": client.phone if client else None,
        "price": float(appt.price),
        "deposit_amount": float(appt.deposit_amount),
    }


@router.get("/today", response_model=list[AppointmentListItem])
async def get_today(db: AsyncSession = Depends(get_db)):
    today = datetime.now().date()
    result = await db.execute(
        select(Appointment, Client)
        .join(Client, Appointment.client_id == Client.id)
        .where(
            and_(
                Appointment.start_datetime >= datetime.combine(today, datetime.min.time()),
                Appointment.start_datetime < datetime.combine(today + timedelta(days=1), datetime.min.time()),
                Appointment.status.in_(["scheduled", "completed"]),
            )
        )
        .order_by(Appointment.start_datetime)
    )
    rows = result.all()
    return [
        {**{c.key: getattr(a, c.key) for c in a.__table__.columns},
         "client_name": cl.full_name, "price": float(a.price), "deposit_amount": float(a.deposit_amount)}
        for a, cl in rows
    ]


@router.get("/upcoming", response_model=list[AppointmentListItem])
async def get_upcoming(days: int = 7, db: AsyncSession = Depends(get_db)):
    now = datetime.now()
    end = now + timedelta(days=days)
    result = await db.execute(
        select(Appointment, Client)
        .join(Client, Appointment.client_id == Client.id)
        .where(
            and_(
                Appointment.start_datetime >= now,
                Appointment.start_datetime < end,
                Appointment.status == "scheduled",
            )
        )
        .order_by(Appointment.start_datetime)
    )
    rows = result.all()
    return [
        {**{c.key: getattr(a, c.key) for c in a.__table__.columns},
         "client_name": cl.full_name, "price": float(a.price), "deposit_amount": float(a.deposit_amount)}
        for a, cl in rows
    ]


@router.get("/", response_model=list[AppointmentListItem])
async def list_appointments(
    start_date: str | None = None,
    end_date: str | None = None,
    status: str | None = None,
    client_id: int | None = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(Appointment, Client)
        .join(Client, Appointment.client_id == Client.id)
    )
    conditions = []
    if start_date:
        conditions.append(Appointment.start_datetime >= datetime.fromisoformat(start_date))
    if end_date:
        conditions.append(Appointment.start_datetime <= datetime.fromisoformat(end_date))
    if status:
        conditions.append(Appointment.status == status)
    if client_id:
        conditions.append(Appointment.client_id == client_id)
    if conditions:
        query = query.where(and_(*conditions))

    query = query.order_by(Appointment.start_datetime.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    rows = result.all()
    return [
        {**{c.key: getattr(a, c.key) for c in a.__table__.columns},
         "client_name": cl.full_name, "price": float(a.price), "deposit_amount": float(a.deposit_amount)}
        for a, cl in rows
    ]


@router.post("/", response_model=AppointmentRead, status_code=201)
async def create_appointment(data: AppointmentCreate, db: AsyncSession = Depends(get_db)):
    # Verify client exists
    client_result = await db.execute(select(Client).where(Client.id == data.client_id))
    client = client_result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    # Compute end_datetime
    end_dt = data.start_datetime + timedelta(minutes=data.duration_minutes)

    appt = Appointment(
        client_id=data.client_id,
        service_type=data.service_type,
        duration_minutes=data.duration_minutes,
        price=data.price,
        start_datetime=data.start_datetime,
        end_datetime=end_dt,
        notes=data.notes,
        deposit_paid=data.deposit_paid,
        deposit_amount=data.deposit_amount,
    )
    db.add(appt)
    await db.flush()

    # Sync to Google Calendar
    if google_calendar_service.is_configured():
        event_id = await google_calendar_service.create_event(db, appt, client)
        if event_id:
            appt.google_event_id = event_id

    await db.refresh(appt)
    result = {**{c.key: getattr(appt, c.key) for c in appt.__table__.columns},
               "client_name": client.full_name, "client_phone": client.phone,
               "price": float(appt.price), "deposit_amount": float(appt.deposit_amount)}
    return result


@router.get("/{appointment_id}", response_model=AppointmentRead)
async def get_appointment(appointment_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Appointment, Client)
        .join(Client, Appointment.client_id == Client.id)
        .where(Appointment.id == appointment_id)
    )
    row = result.one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Appointment not found")
    appt, client = row
    return {**{c.key: getattr(appt, c.key) for c in appt.__table__.columns},
            "client_name": client.full_name, "client_phone": client.phone,
            "price": float(appt.price), "deposit_amount": float(appt.deposit_amount)}


@router.put("/{appointment_id}", response_model=AppointmentRead)
async def update_appointment(
    appointment_id: int, data: AppointmentUpdate, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Appointment, Client)
        .join(Client, Appointment.client_id == Client.id)
        .where(Appointment.id == appointment_id)
    )
    row = result.one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Appointment not found")
    appt, client = row

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(appt, field, value)

    # Recompute end_datetime if start or duration changed
    if data.start_datetime or data.duration_minutes:
        appt.end_datetime = appt.start_datetime + timedelta(minutes=appt.duration_minutes)

    # Sync to Google Calendar
    if appt.google_event_id and google_calendar_service.is_configured():
        await google_calendar_service.update_event(db, appt.google_event_id, appt, client)

    await db.flush()
    await db.refresh(appt)
    return {**{c.key: getattr(appt, c.key) for c in appt.__table__.columns},
            "client_name": client.full_name, "client_phone": client.phone,
            "price": float(appt.price), "deposit_amount": float(appt.deposit_amount)}


@router.delete("/{appointment_id}")
async def cancel_appointment(
    appointment_id: int,
    reason: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Appointment).where(Appointment.id == appointment_id))
    appt = result.scalar_one_or_none()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")

    appt.status = "cancelled"
    appt.cancellation_reason = reason

    # Delete from Google Calendar
    if appt.google_event_id and google_calendar_service.is_configured():
        await google_calendar_service.delete_event(db, appt.google_event_id)
        appt.google_event_id = None

    await db.commit()

    # Notify waitlist (first entry for this service)
    from app.models.client import WaitlistEntry
    from app.services.twilio_service import twilio_service
    from app.models.communication import SmsMessage
    from app.config import get_settings as _get_settings
    _settings = _get_settings()

    waitlist_result = await db.execute(
        select(WaitlistEntry, Client)
        .join(Client, WaitlistEntry.client_id == Client.id)
        .where(WaitlistEntry.status == "waiting")
        .order_by(WaitlistEntry.created_at.asc())
        .limit(1)
    )
    waitlist_row = waitlist_result.one_or_none()
    if waitlist_row:
        entry, wl_client = waitlist_row
        slot_time = appt.start_datetime.strftime("%A, %B %d at %I:%M %p")
        body = (
            f"Hi {wl_client.full_name.split()[0]}! A slot just opened up: {slot_time}. "
            f"Reply BOOK to claim it! — {_settings.stylist_name}"
        )
        sid = twilio_service.send_sms(wl_client.phone, body)
        db.add(SmsMessage(
            client_id=wl_client.id,
            phone_number=wl_client.phone,
            direction="outbound",
            body=body,
            twilio_sid=sid,
            status="sent",
            message_type="waitlist_notification",
        ))
        from datetime import datetime as _dt
        entry.notified_at = _dt.now()
        entry.status = "offered"
        await db.commit()

    return {"message": "Appointment cancelled"}


@router.post("/{appointment_id}/complete")
async def complete_appointment(appointment_id: int, db: AsyncSession = Depends(get_db)):
    """Mark appointment as completed and create aftercare sequence."""
    from app.models.report import AftercareSequence

    result = await db.execute(
        select(Appointment, Client)
        .join(Client, Appointment.client_id == Client.id)
        .where(Appointment.id == appointment_id)
    )
    row = result.one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Appointment not found")
    appt, client = row

    appt.status = "completed"

    # Update client stats
    client.total_visits += 1
    client.last_visit_date = appt.start_datetime.date()
    client.total_spent = float(client.total_spent) + float(appt.price)
    client.is_lapsed = False
    if not client.first_visit_date:
        client.first_visit_date = appt.start_datetime.date()

    # Create aftercare sequence (only for extension services)
    existing_seq = await db.execute(
        select(AftercareSequence).where(AftercareSequence.appointment_id == appointment_id)
    )
    if not existing_seq.scalar_one_or_none():
        seq = AftercareSequence(appointment_id=appointment_id, client_id=client.id)
        db.add(seq)

    await db.commit()
    return {"message": "Appointment completed", "aftercare_sequence_created": True}


@router.post("/{appointment_id}/no-show")
async def mark_no_show(appointment_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Appointment).where(Appointment.id == appointment_id))
    appt = result.scalar_one_or_none()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")
    appt.status = "no_show"
    await db.commit()
    return {"message": "Marked as no-show"}
