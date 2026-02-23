from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # App
    app_secret_key: str = "dev-secret-key-change-in-production"
    app_base_url: str = "http://localhost:8000"
    # Comma-separated list of allowed frontend origins (add your Vercel URL here)
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    # Database
    database_url: str = "sqlite+aiosqlite:///./salon.db"

    # Anthropic
    anthropic_api_key: str = ""

    # Twilio
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_phone_number: str = ""

    # Google Calendar
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/api/v1/calendar/callback"

    # Salon configuration
    salon_name: str = "The Salon"
    stylist_name: str = "Your Stylist"
    salon_timezone: str = "America/New_York"
    salon_hours_start: str = "09:00"
    salon_hours_end: str = "18:00"
    booking_link: str = ""

    # Scheduler
    scheduler_reminder_hour: int = 8
    scheduler_aftercare_hour: int = 9
    scheduler_followup_hour: int = 11


@lru_cache
def get_settings() -> Settings:
    return Settings()
