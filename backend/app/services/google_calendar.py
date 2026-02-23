"""
Google Calendar integration service.
Handles OAuth2 flow and all calendar CRUD operations.
Tokens are stored in the app_settings table (key: google_tokens).
"""
import json
from datetime import datetime, timedelta, date
from typing import Optional
from app.config import get_settings

settings = get_settings()

SCOPES = ["https://www.googleapis.com/auth/calendar"]


class GoogleCalendarService:
    def __init__(self):
        self._service = None
        self._configured = bool(
            settings.google_client_id and settings.google_client_secret
        )

    def is_configured(self) -> bool:
        return self._configured

    def get_auth_url(self) -> str:
        """Generate the Google OAuth2 authorization URL."""
        from google_auth_oauthlib.flow import Flow
        flow = self._create_flow()
        auth_url, _ = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent",
        )
        return auth_url

    async def handle_oauth_callback(self, code: str, db) -> bool:
        """Exchange auth code for tokens and store in DB."""
        from google_auth_oauthlib.flow import Flow
        from app.models.report import AppSetting
        from sqlalchemy import select

        try:
            flow = self._create_flow()
            flow.fetch_token(code=code)
            creds = flow.credentials

            token_data = {
                "token": creds.token,
                "refresh_token": creds.refresh_token,
                "token_uri": creds.token_uri,
                "client_id": creds.client_id,
                "client_secret": creds.client_secret,
                "scopes": list(creds.scopes) if creds.scopes else [],
            }

            # Upsert into app_settings
            result = await db.execute(
                select(AppSetting).where(AppSetting.key == "google_tokens")
            )
            setting = result.scalar_one_or_none()
            if setting:
                setting.value = json.dumps(token_data)
            else:
                db.add(AppSetting(key="google_tokens", value=json.dumps(token_data)))
            await db.commit()
            self._service = None  # Reset so it gets recreated with new tokens
            return True
        except Exception as e:
            print(f"Google OAuth error: {e}")
            return False

    async def get_service(self, db):
        """Get an authenticated Google Calendar service, refreshing tokens if needed."""
        if not self._configured:
            raise RuntimeError("Google Calendar is not configured.")

        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build
        from app.models.report import AppSetting
        from sqlalchemy import select

        result = await db.execute(
            select(AppSetting).where(AppSetting.key == "google_tokens")
        )
        setting = result.scalar_one_or_none()
        if not setting or not setting.value:
            raise RuntimeError("Google Calendar not connected. Please authorize first.")

        token_data = json.loads(setting.value)
        creds = Credentials(
            token=token_data["token"],
            refresh_token=token_data.get("refresh_token"),
            token_uri=token_data.get("token_uri", "https://oauth2.googleapis.com/token"),
            client_id=token_data["client_id"],
            client_secret=token_data["client_secret"],
            scopes=token_data.get("scopes", SCOPES),
        )

        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            # Save refreshed token
            token_data["token"] = creds.token
            setting.value = json.dumps(token_data)
            await db.commit()

        return build("calendar", "v3", credentials=creds)

    async def create_event(self, db, appointment, client) -> Optional[str]:
        """Create a Google Calendar event for an appointment. Returns event ID."""
        try:
            service = await self.get_service(db)
            event = {
                "summary": f"{client.full_name} — {appointment.service_type}",
                "description": (
                    f"Service: {appointment.service_type}\n"
                    f"Price: ${float(appointment.price):.2f}\n"
                    f"Phone: {client.phone}\n"
                    f"Notes: {appointment.notes or 'None'}"
                ),
                "start": {
                    "dateTime": appointment.start_datetime.isoformat(),
                    "timeZone": settings.salon_timezone,
                },
                "end": {
                    "dateTime": appointment.end_datetime.isoformat(),
                    "timeZone": settings.salon_timezone,
                },
                "reminders": {
                    "useDefault": False,
                    "overrides": [
                        {"method": "popup", "minutes": 60},
                        {"method": "popup", "minutes": 1440},  # 24h
                    ],
                },
            }
            result = service.events().insert(calendarId="primary", body=event).execute()
            return result.get("id")
        except Exception as e:
            print(f"Google Calendar create_event error: {e}")
            return None

    async def update_event(self, db, google_event_id: str, appointment, client) -> bool:
        """Update an existing Google Calendar event."""
        try:
            service = await self.get_service(db)
            event = service.events().get(calendarId="primary", eventId=google_event_id).execute()
            event["summary"] = f"{client.full_name} — {appointment.service_type}"
            event["description"] = (
                f"Service: {appointment.service_type}\n"
                f"Price: ${float(appointment.price):.2f}\n"
                f"Phone: {client.phone}\n"
                f"Notes: {appointment.notes or 'None'}"
            )
            event["start"]["dateTime"] = appointment.start_datetime.isoformat()
            event["end"]["dateTime"] = appointment.end_datetime.isoformat()
            service.events().update(calendarId="primary", eventId=google_event_id, body=event).execute()
            return True
        except Exception as e:
            print(f"Google Calendar update_event error: {e}")
            return False

    async def delete_event(self, db, google_event_id: str) -> bool:
        """Delete a Google Calendar event."""
        try:
            service = await self.get_service(db)
            service.events().delete(calendarId="primary", eventId=google_event_id).execute()
            return True
        except Exception as e:
            print(f"Google Calendar delete_event error: {e}")
            return False

    async def get_available_slots(
        self,
        db,
        check_date: date,
        duration_minutes: int = 60
    ) -> list[str]:
        """Return available booking slots as ISO datetime strings."""
        try:
            service = await self.get_service(db)
            start_of_day = datetime.combine(check_date, datetime.strptime(settings.salon_hours_start, "%H:%M").time())
            end_of_day = datetime.combine(check_date, datetime.strptime(settings.salon_hours_end, "%H:%M").time())

            # Get busy times
            body = {
                "timeMin": start_of_day.isoformat() + "Z",
                "timeMax": end_of_day.isoformat() + "Z",
                "items": [{"id": "primary"}],
            }
            freebusy = service.freebusy().query(body=body).execute()
            busy = freebusy.get("calendars", {}).get("primary", {}).get("busy", [])

            # Build list of busy intervals
            busy_intervals = [
                (
                    datetime.fromisoformat(b["start"].replace("Z", "")),
                    datetime.fromisoformat(b["end"].replace("Z", "")),
                )
                for b in busy
            ]

            # Generate 30-minute slots and filter out busy ones
            slots = []
            slot_start = start_of_day
            while slot_start + timedelta(minutes=duration_minutes) <= end_of_day:
                slot_end = slot_start + timedelta(minutes=duration_minutes)
                # Check if this slot overlaps any busy period
                is_free = all(
                    slot_end <= busy_start or slot_start >= busy_end
                    for busy_start, busy_end in busy_intervals
                )
                if is_free:
                    slots.append(slot_start.isoformat())
                slot_start += timedelta(minutes=30)  # 30-min increments

            return slots
        except Exception as e:
            print(f"Google Calendar get_available_slots error: {e}")
            return []

    async def sync_from_google(self, db) -> list[dict]:
        """Pull events from Google Calendar for the next 90 days."""
        try:
            service = await self.get_service(db)
            now = datetime.utcnow().isoformat() + "Z"
            end = (datetime.utcnow() + timedelta(days=90)).isoformat() + "Z"
            events_result = (
                service.events()
                .list(
                    calendarId="primary",
                    timeMin=now,
                    timeMax=end,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )
            return events_result.get("items", [])
        except Exception as e:
            print(f"Google Calendar sync error: {e}")
            return []

    async def check_connection(self, db) -> dict:
        """Check if Google Calendar is connected and working."""
        if not self._configured:
            return {"connected": False, "reason": "Google credentials not configured"}
        try:
            service = await self.get_service(db)
            cal = service.calendars().get(calendarId="primary").execute()
            return {"connected": True, "calendar_name": cal.get("summary", "Primary")}
        except RuntimeError as e:
            return {"connected": False, "reason": str(e)}
        except Exception as e:
            return {"connected": False, "reason": f"Connection error: {str(e)}"}

    def _create_flow(self):
        from google_auth_oauthlib.flow import Flow
        return Flow.from_client_config(
            {
                "web": {
                    "client_id": settings.google_client_id,
                    "client_secret": settings.google_client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [settings.google_redirect_uri],
                }
            },
            scopes=SCOPES,
            redirect_uri=settings.google_redirect_uri,
        )


# Singleton
google_calendar_service = GoogleCalendarService()
