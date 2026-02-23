"""
APScheduler background jobs for automated SMS outreach.
Started in FastAPI lifespan context manager (main.py).
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from app.config import get_settings

settings = get_settings()
scheduler = AsyncIOScheduler()


async def send_appointment_reminders():
    """Send SMS reminders for appointments tomorrow."""
    from datetime import datetime, timedelta, date
    from app.database import AsyncSessionLocal
    from app.models.appointment import Appointment
    from app.models.client import Client
    from app.models.communication import SmsMessage
    from app.services.twilio_service import twilio_service
    from sqlalchemy import select, and_

    tomorrow = (datetime.now() + timedelta(days=1)).date()

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Appointment, Client)
            .join(Client, Appointment.client_id == Client.id)
            .where(
                and_(
                    Appointment.status == "scheduled",
                    # SQLite date comparison via string
                    Appointment.start_datetime >= datetime.combine(tomorrow, datetime.min.time()),
                    Appointment.start_datetime < datetime.combine(tomorrow + timedelta(days=1), datetime.min.time()),
                )
            )
        )
        rows = result.all()

        for appointment, client in rows:
            time_str = appointment.start_datetime.strftime("%I:%M %p")
            body = (
                f"Hi {client.full_name.split()[0]}! Reminder: you have {appointment.service_type} "
                f"tomorrow at {time_str}. Reply CANCEL to cancel. See you then! — {settings.stylist_name}"
            )
            sid = twilio_service.send_sms(client.phone, body)
            db.add(SmsMessage(
                client_id=client.id,
                appointment_id=appointment.id,
                phone_number=client.phone,
                direction="outbound",
                body=body,
                twilio_sid=sid,
                status="sent",
                message_type="reminder",
            ))

        await db.commit()
        print(f"[Scheduler] Sent {len(rows)} appointment reminders")


async def send_pending_aftercare():
    """Send D3 and W2 aftercare sequences that are due today."""
    from datetime import datetime, timedelta
    from app.database import AsyncSessionLocal
    from app.models.report import AftercareSequence
    from app.models.appointment import Appointment
    from app.models.client import Client
    from app.models.communication import SmsMessage
    from app.services.twilio_service import twilio_service
    from sqlalchemy import select, and_

    now = datetime.now()
    d3_threshold = now - timedelta(days=3)
    w2_threshold = now - timedelta(days=14)

    async with AsyncSessionLocal() as db:
        # D3 sequences
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
        for seq, appt, client in d3_result.all():
            body = (
                f"Hi {client.full_name.split()[0]}! It's been 3 days since your {appt.service_type}. "
                f"How are you loving your hair? Any aftercare questions? I'm here! "
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
            seq.d3_sent_at = now
            seq.d3_sms_id = sms.id

        # W2 sequences
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
        for seq, appt, client in w2_result.all():
            body = (
                f"Hi {client.full_name.split()[0]}! Two weeks already — how are your extensions wearing? "
                f"When you're ready for a refresh or your next appointment, reply BOOK and I'll sort you out! "
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
            seq.w2_sent_at = now
            seq.w2_sms_id = sms.id
            seq.upsell_offer_sent = True

        await db.commit()
        print("[Scheduler] Processed aftercare sequences")


async def flag_lapsed_clients():
    """Flag clients as lapsed if they haven't visited in 90+ days."""
    from datetime import datetime, timedelta
    from app.database import AsyncSessionLocal
    from app.models.client import Client
    from sqlalchemy import select, and_

    threshold = (datetime.now() - timedelta(days=90)).date()

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Client).where(
                and_(
                    Client.is_lapsed == False,  # noqa: E712
                    Client.last_visit_date.is_not(None),
                    Client.last_visit_date < threshold,
                )
            )
        )
        clients = result.scalars().all()
        for client in clients:
            client.is_lapsed = True
        await db.commit()
        print(f"[Scheduler] Flagged {len(clients)} clients as lapsed")


async def flag_leads_for_followup():
    """Surface leads that need follow-up today."""
    from datetime import datetime
    from app.database import AsyncSessionLocal
    from app.models.lead import ExtensionLead
    from sqlalchemy import select, and_

    now = datetime.now()

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(ExtensionLead).where(
                and_(
                    ExtensionLead.next_follow_up_at <= now,
                    ExtensionLead.pipeline_stage.notin_(["booked", "lost"]),
                )
            )
        )
        leads = result.scalars().all()
        # Just log — the UI surfaces these via the alerts endpoint
        print(f"[Scheduler] {len(leads)} leads need follow-up today")


def setup_scheduler():
    """Configure and return the scheduler with all jobs."""
    scheduler.add_job(
        send_appointment_reminders,
        CronTrigger(hour=settings.scheduler_reminder_hour, minute=0),
        id="appointment_reminders",
        replace_existing=True,
    )
    scheduler.add_job(
        send_pending_aftercare,
        CronTrigger(hour=settings.scheduler_aftercare_hour, minute=0),
        id="aftercare_sequences",
        replace_existing=True,
    )
    scheduler.add_job(
        flag_lapsed_clients,
        CronTrigger(day_of_week="mon", hour=settings.scheduler_aftercare_hour, minute=30),
        id="flag_lapsed",
        replace_existing=True,
    )
    scheduler.add_job(
        flag_leads_for_followup,
        CronTrigger(hour=settings.scheduler_followup_hour, minute=0),
        id="flag_followup",
        replace_existing=True,
    )
    return scheduler
