from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.services.google_calendar import google_calendar_service
from app.config import get_settings

router = APIRouter(prefix="/calendar", tags=["calendar"])
settings = get_settings()


@router.get("/status")
async def check_status(db: AsyncSession = Depends(get_db)):
    status = await google_calendar_service.check_connection(db)
    return status


@router.get("/auth-url")
async def get_auth_url():
    if not google_calendar_service.is_configured():
        raise HTTPException(
            status_code=400,
            detail="Google Calendar credentials are not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env"
        )
    url = google_calendar_service.get_auth_url()
    return {"auth_url": url}


@router.get("/callback")
async def oauth_callback(code: str, db: AsyncSession = Depends(get_db)):
    """Handle Google OAuth2 callback. Redirects to frontend settings page."""
    success = await google_calendar_service.handle_oauth_callback(code, db)
    if success:
        # Redirect to frontend settings with success flag
        return RedirectResponse(url="http://localhost:5173/settings?gcal=connected")
    else:
        return RedirectResponse(url="http://localhost:5173/settings?gcal=error")


@router.get("/slots")
async def get_available_slots(
    date: str,
    duration: int = 60,
    db: AsyncSession = Depends(get_db),
):
    """Get available booking slots for a date."""
    from datetime import date as date_type
    try:
        check_date = date_type.fromisoformat(date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    slots = await google_calendar_service.get_available_slots(db, check_date, duration)
    return {"date": date, "duration_minutes": duration, "available_slots": slots}


@router.post("/sync")
async def sync_from_google(db: AsyncSession = Depends(get_db)):
    """Pull events from Google Calendar and surface any discrepancies."""
    from app.models.appointment import Appointment

    events = await google_calendar_service.sync_from_google(db)

    synced = 0
    needs_review = []

    for event in events:
        event_id = event.get("id")
        if not event_id:
            continue

        # Check if we have this event
        result = await db.execute(
            select(Appointment).where(Appointment.google_event_id == event_id)
        )
        appt = result.scalar_one_or_none()

        if appt:
            # Check if times match
            event_start = event.get("start", {}).get("dateTime", "")
            if event_start:
                from datetime import datetime
                try:
                    gcal_start = datetime.fromisoformat(event_start.replace("Z", "+00:00")).replace(tzinfo=None)
                    db_start = appt.start_datetime
                    # If more than 5 min difference, flag for review
                    if abs((gcal_start - db_start).total_seconds()) > 300:
                        appt.status = "needs_review"
                        needs_review.append({"appointment_id": appt.id, "event_id": event_id})
                except Exception:
                    pass
            synced += 1

    await db.commit()
    return {
        "message": f"Sync complete. {synced} events checked.",
        "needs_review_count": len(needs_review),
        "needs_review": needs_review,
    }
