from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, extract
from app.database import get_db
from app.models.report import Report, AftercareSequence
from app.models.appointment import Appointment
from app.models.client import Client
from app.models.lead import ExtensionLead
from app.services.ai.report_generator import generate_report_stream

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/")
async def list_reports(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Report).order_by(Report.report_month.desc()).limit(24)
    )
    reports = result.scalars().all()
    return [
        {
            "id": r.id,
            "report_month": r.report_month,
            "revenue_total": r.revenue_total,
            "appointments_count": r.appointments_count,
            "new_clients_count": r.new_clients_count,
            "has_ai_summary": bool(r.ai_summary_text),
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in reports
    ]


@router.get("/dashboard-stats")
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    """Real-time KPIs for the dashboard."""
    now = datetime.now()
    current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Revenue this month
    revenue_result = await db.execute(
        select(func.sum(Appointment.price)).where(
            and_(
                Appointment.status == "completed",
                Appointment.start_datetime >= current_month_start,
            )
        )
    )
    revenue_month = revenue_result.scalar() or 0.0

    # Appointments this month
    appt_result = await db.execute(
        select(func.count(Appointment.id)).where(
            and_(
                Appointment.status == "completed",
                Appointment.start_datetime >= current_month_start,
            )
        )
    )
    appts_month = appt_result.scalar() or 0

    # Total clients
    total_clients_result = await db.execute(select(func.count(Client.id)))
    total_clients = total_clients_result.scalar() or 0

    # Lapsed clients
    lapsed_result = await db.execute(
        select(func.count(Client.id)).where(Client.is_lapsed == True)  # noqa: E712
    )
    lapsed_count = lapsed_result.scalar() or 0

    # Active leads in pipeline (not lost/booked)
    active_leads_result = await db.execute(
        select(func.count(ExtensionLead.id)).where(
            ExtensionLead.pipeline_stage.notin_(["lost", "booked"])
        )
    )
    active_leads = active_leads_result.scalar() or 0

    # Upcoming appointments (next 7 days)
    from datetime import timedelta

    upcoming_result = await db.execute(
        select(func.count(Appointment.id)).where(
            and_(
                Appointment.status == "scheduled",
                Appointment.start_datetime >= now,
                Appointment.start_datetime <= now + timedelta(days=7),
            )
        )
    )
    upcoming_count = upcoming_result.scalar() or 0

    return {
        "revenue_this_month": float(revenue_month),
        "appointments_this_month": appts_month,
        "total_clients": total_clients,
        "lapsed_clients": lapsed_count,
        "active_leads": active_leads,
        "upcoming_7_days": upcoming_count,
    }


@router.get("/{month}")
async def get_report(month: str, db: AsyncSession = Depends(get_db)):
    """Fetch report for a month (format: YYYY-MM)."""
    result = await db.execute(
        select(Report).where(Report.report_month == month)
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return {
        "id": report.id,
        "report_month": report.report_month,
        "revenue_total": report.revenue_total,
        "appointments_count": report.appointments_count,
        "new_clients_count": report.new_clients_count,
        "lapsed_recovered": report.lapsed_recovered,
        "leads_converted": report.leads_converted,
        "top_services_json": report.top_services_json,
        "ai_summary_text": report.ai_summary_text,
        "charts_data_json": report.charts_data_json,
        "created_at": report.created_at.isoformat() if report.created_at else None,
    }


@router.post("/{month}/generate")
async def generate_report(month: str, db: AsyncSession = Depends(get_db)):
    """Compute report data from DB for a given month (YYYY-MM)."""
    try:
        year, mon = map(int, month.split("-"))
    except ValueError:
        raise HTTPException(status_code=400, detail="Month must be in YYYY-MM format")

    month_start = datetime(year, mon, 1)
    if mon == 12:
        month_end = datetime(year + 1, 1, 1)
    else:
        month_end = datetime(year, mon + 1, 1)

    # Revenue + appointments
    appt_result = await db.execute(
        select(
            func.count(Appointment.id),
            func.sum(Appointment.price),
        ).where(
            and_(
                Appointment.status == "completed",
                Appointment.start_datetime >= month_start,
                Appointment.start_datetime < month_end,
            )
        )
    )
    row = appt_result.one()
    appt_count = row[0] or 0
    revenue = float(row[1] or 0)

    # New clients this month
    new_clients_result = await db.execute(
        select(func.count(Client.id)).where(
            and_(
                Client.created_at >= month_start,
                Client.created_at < month_end,
            )
        )
    )
    new_clients = new_clients_result.scalar() or 0

    # Lapsed clients recovered (had appointment this month but was lapsed)
    # (simplified: clients with last_visit_date in this month who have >1 visits)
    lapsed_recovered_result = await db.execute(
        select(func.count(Client.id)).where(
            and_(
                Client.last_visit_date >= month_start.date(),
                Client.last_visit_date < month_end.date(),
                Client.total_visits > 1,
                Client.is_lapsed == False,  # noqa: E712
            )
        )
    )
    lapsed_recovered = lapsed_recovered_result.scalar() or 0

    # Leads converted this month
    leads_converted_result = await db.execute(
        select(func.count(ExtensionLead.id)).where(
            and_(
                ExtensionLead.pipeline_stage == "booked",
                ExtensionLead.updated_at >= month_start,
                ExtensionLead.updated_at < month_end,
            )
        )
    )
    leads_converted = leads_converted_result.scalar() or 0

    # Top services by count
    top_services_result = await db.execute(
        select(
            Appointment.service_type,
            func.count(Appointment.id).label("count"),
            func.sum(Appointment.price).label("revenue"),
        )
        .where(
            and_(
                Appointment.status == "completed",
                Appointment.start_datetime >= month_start,
                Appointment.start_datetime < month_end,
            )
        )
        .group_by(Appointment.service_type)
        .order_by(func.count(Appointment.id).desc())
        .limit(5)
    )
    top_services = [
        {"service": row[0], "count": row[1], "revenue": float(row[2] or 0)}
        for row in top_services_result.all()
    ]

    # Charts data: daily revenue for the month
    daily_result = await db.execute(
        select(
            func.date(Appointment.start_datetime).label("day"),
            func.sum(Appointment.price).label("revenue"),
        )
        .where(
            and_(
                Appointment.status == "completed",
                Appointment.start_datetime >= month_start,
                Appointment.start_datetime < month_end,
            )
        )
        .group_by(func.date(Appointment.start_datetime))
        .order_by(func.date(Appointment.start_datetime))
    )
    daily_revenue = [
        {"date": str(row[0]), "revenue": float(row[1] or 0)}
        for row in daily_result.all()
    ]

    # Upsert report
    existing_result = await db.execute(
        select(Report).where(Report.report_month == month)
    )
    report = existing_result.scalar_one_or_none()
    if not report:
        report = Report(report_month=month)
        db.add(report)

    report.revenue_total = revenue
    report.appointments_count = appt_count
    report.new_clients_count = new_clients
    report.lapsed_recovered = lapsed_recovered
    report.leads_converted = leads_converted
    report.top_services_json = top_services
    report.charts_data_json = {"daily_revenue": daily_revenue}

    await db.commit()
    await db.refresh(report)

    return {
        "message": "Report generated",
        "report_month": month,
        "revenue_total": revenue,
        "appointments_count": appt_count,
        "new_clients_count": new_clients,
    }


@router.post("/{month}/ai-summary")
async def generate_ai_summary(month: str, db: AsyncSession = Depends(get_db)):
    """Stream AI narrative for an existing report."""
    result = await db.execute(
        select(Report).where(Report.report_month == month)
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(
            status_code=404,
            detail="Report not found. Run POST /{month}/generate first.",
        )

    # Get previous month for comparison
    year, mon = map(int, month.split("-"))
    if mon == 1:
        prev_month = f"{year - 1}-12"
    else:
        prev_month = f"{year}-{mon - 1:02d}"

    prev_result = await db.execute(
        select(Report).where(Report.report_month == prev_month)
    )
    prev_report = prev_result.scalar_one_or_none()

    report_data = {
        "month": month,
        "revenue_total": report.revenue_total,
        "appointments_count": report.appointments_count,
        "new_clients_count": report.new_clients_count,
        "lapsed_recovered": report.lapsed_recovered,
        "leads_converted": report.leads_converted,
        "top_services": report.top_services_json,
    }

    prev_data = None
    if prev_report:
        prev_data = {
            "month": prev_month,
            "revenue_total": prev_report.revenue_total,
            "appointments_count": prev_report.appointments_count,
            "new_clients_count": prev_report.new_clients_count,
        }

    async def stream_and_save():
        full_text = []
        async for chunk in generate_report_stream(report_data, prev_data):
            full_text.append(chunk)
            yield chunk
        # Save the completed summary
        from app.database import AsyncSessionLocal
        async with AsyncSessionLocal() as save_db:
            save_result = await save_db.execute(
                select(Report).where(Report.report_month == month)
            )
            r = save_result.scalar_one_or_none()
            if r:
                r.ai_summary_text = "".join(full_text)
                await save_db.commit()

    return StreamingResponse(stream_and_save(), media_type="text/plain")
