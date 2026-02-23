from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from app.database import get_db
from app.models.appointment import Appointment
from app.models.client import Client
from app.models.lead import ExtensionLead
from app.models.report import AftercareSequence
from app.models.inventory import InventoryProduct
from app.models.communication import SmsMessage

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/alerts")
async def get_alerts(db: AsyncSession = Depends(get_db)):
    """
    Aggregated alert panel — surfaces all items that need attention:
    - Low-stock inventory
    - Lapsed clients needing outreach
    - Leads with overdue follow-ups
    - Aftercare sequences due today
    - Appointments with needs_review status (GCal conflicts)
    - No-show appointments pending re-engagement
    """
    now = datetime.now()
    alerts = []

    # --- Low stock ---
    low_stock_result = await db.execute(
        select(InventoryProduct).where(
            and_(
                InventoryProduct.is_active == True,  # noqa: E712
                InventoryProduct.current_stock <= InventoryProduct.reorder_threshold,
            )
        )
    )
    low_stock_items = low_stock_result.scalars().all()
    for item in low_stock_items:
        alerts.append(
            {
                "type": "low_stock",
                "severity": "warning",
                "title": f"Low stock: {item.name}",
                "detail": f"{item.current_stock} {item.stock_unit} remaining (threshold: {item.reorder_threshold})",
                "link": "/inventory",
                "item_id": item.id,
            }
        )

    # --- Lapsed clients ---
    lapsed_result = await db.execute(
        select(func.count(Client.id)).where(Client.is_lapsed == True)  # noqa: E712
    )
    lapsed_count = lapsed_result.scalar() or 0
    if lapsed_count > 0:
        alerts.append(
            {
                "type": "lapsed_clients",
                "severity": "info",
                "title": f"{lapsed_count} lapsed client{'s' if lapsed_count != 1 else ''}",
                "detail": "Haven't visited in 90+ days — consider sending outreach",
                "link": "/clients?filter=lapsed",
                "count": lapsed_count,
            }
        )

    # --- Overdue lead follow-ups ---
    overdue_leads_result = await db.execute(
        select(func.count(ExtensionLead.id)).where(
            and_(
                ExtensionLead.next_follow_up_at <= now,
                ExtensionLead.pipeline_stage.notin_(["lost", "booked"]),
            )
        )
    )
    overdue_leads = overdue_leads_result.scalar() or 0
    if overdue_leads > 0:
        alerts.append(
            {
                "type": "lead_followup",
                "severity": "warning",
                "title": f"{overdue_leads} lead follow-up{'s' if overdue_leads != 1 else ''} due",
                "detail": "Leads awaiting your follow-up contact",
                "link": "/leads",
                "count": overdue_leads,
            }
        )

    # --- Aftercare D3 due ---
    d3_threshold = now - timedelta(days=3)
    d3_result = await db.execute(
        select(func.count(AftercareSequence.id))
        .join(Appointment, AftercareSequence.appointment_id == Appointment.id)
        .where(
            and_(
                AftercareSequence.d3_sent_at.is_(None),
                Appointment.end_datetime <= d3_threshold,
                Appointment.status == "completed",
            )
        )
    )
    d3_count = d3_result.scalar() or 0
    if d3_count > 0:
        alerts.append(
            {
                "type": "aftercare_d3",
                "severity": "info",
                "title": f"{d3_count} day-3 aftercare due",
                "detail": "Clients who had appointments 3+ days ago haven't received their check-in",
                "link": "/aftercare",
                "count": d3_count,
            }
        )

    # --- Aftercare W2 due ---
    w2_threshold = now - timedelta(days=14)
    w2_result = await db.execute(
        select(func.count(AftercareSequence.id))
        .join(Appointment, AftercareSequence.appointment_id == Appointment.id)
        .where(
            and_(
                AftercareSequence.w2_sent_at.is_(None),
                AftercareSequence.d3_sent_at.is_not(None),
                Appointment.end_datetime <= w2_threshold,
                Appointment.status == "completed",
            )
        )
    )
    w2_count = w2_result.scalar() or 0
    if w2_count > 0:
        alerts.append(
            {
                "type": "aftercare_w2",
                "severity": "info",
                "title": f"{w2_count} week-2 aftercare due",
                "detail": "Clients due for their 2-week follow-up and upsell message",
                "link": "/aftercare",
                "count": w2_count,
            }
        )

    # --- Calendar conflicts (needs_review) ---
    conflicts_result = await db.execute(
        select(func.count(Appointment.id)).where(
            Appointment.status == "needs_review"
        )
    )
    conflicts_count = conflicts_result.scalar() or 0
    if conflicts_count > 0:
        alerts.append(
            {
                "type": "calendar_conflict",
                "severity": "error",
                "title": f"{conflicts_count} calendar conflict{'s' if conflicts_count != 1 else ''}",
                "detail": "Appointments imported from Google Calendar need review",
                "link": "/appointments",
                "count": conflicts_count,
            }
        )

    # --- No-shows needing re-engagement ---
    no_show_threshold = now - timedelta(days=7)
    no_show_result = await db.execute(
        select(func.count(Appointment.id)).where(
            and_(
                Appointment.status == "no_show",
                Appointment.start_datetime >= no_show_threshold,
            )
        )
    )
    no_show_count = no_show_result.scalar() or 0
    if no_show_count > 0:
        alerts.append(
            {
                "type": "no_show",
                "severity": "warning",
                "title": f"{no_show_count} recent no-show{'s' if no_show_count != 1 else ''}",
                "detail": "Consider sending re-engagement messages",
                "link": "/appointments?status=no_show",
                "count": no_show_count,
            }
        )

    return {
        "alerts": alerts,
        "total": len(alerts),
        "has_errors": any(a["severity"] == "error" for a in alerts),
    }


@router.get("/today")
async def get_today_overview(db: AsyncSession = Depends(get_db)):
    """Today's schedule and quick stats."""
    now = datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)

    result = await db.execute(
        select(Appointment, Client)
        .join(Client, Appointment.client_id == Client.id)
        .where(
            and_(
                Appointment.start_datetime >= today_start,
                Appointment.start_datetime <= today_end,
                Appointment.status.in_(["scheduled", "completed"]),
            )
        )
        .order_by(Appointment.start_datetime)
    )
    rows = result.all()

    appointments = []
    total_revenue = 0.0
    for appt, client in rows:
        if appt.status == "completed" and appt.price:
            total_revenue += float(appt.price)
        appointments.append(
            {
                "id": appt.id,
                "client_name": client.full_name,
                "service_type": appt.service_type,
                "start_time": appt.start_datetime.strftime("%H:%M"),
                "end_time": appt.end_datetime.strftime("%H:%M") if appt.end_datetime else None,
                "status": appt.status,
                "price": float(appt.price) if appt.price else None,
            }
        )

    return {
        "date": today_start.strftime("%Y-%m-%d"),
        "appointments": appointments,
        "total_appointments": len(appointments),
        "completed_count": sum(1 for a in appointments if a["status"] == "completed"),
        "revenue_today": total_revenue,
    }
