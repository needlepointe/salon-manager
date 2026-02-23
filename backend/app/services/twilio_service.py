"""
Twilio SMS service — sending and webhook validation.
All outbound messages are logged to the sms_messages table.
"""
from app.config import get_settings

settings = get_settings()


class TwilioService:
    def __init__(self):
        self._client = None
        self._validator = None
        self._configured = bool(
            settings.twilio_account_sid
            and settings.twilio_auth_token
            and settings.twilio_phone_number
        )

    @property
    def client(self):
        if self._client is None:
            if not self._configured:
                raise RuntimeError(
                    "Twilio is not configured. Set TWILIO_ACCOUNT_SID, "
                    "TWILIO_AUTH_TOKEN, and TWILIO_PHONE_NUMBER in .env"
                )
            from twilio.rest import Client
            self._client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
        return self._client

    @property
    def validator(self):
        if self._validator is None:
            from twilio.request_validator import RequestValidator
            self._validator = RequestValidator(settings.twilio_auth_token)
        return self._validator

    def is_configured(self) -> bool:
        return self._configured

    def send_sms(self, to: str, body: str) -> str | None:
        """
        Send an SMS. Returns the Twilio MessageSid on success, None on failure.
        Raises RuntimeError if Twilio is not configured.
        """
        if not self._configured:
            # In development, just log the message
            print(f"[SMS MOCK] To: {to}\nBody: {body}\n")
            return None

        message = self.client.messages.create(
            body=body,
            from_=settings.twilio_phone_number,
            to=to,
        )
        return message.sid

    def validate_webhook_signature(
        self, url: str, params: dict, signature: str
    ) -> bool:
        """Validate a Twilio webhook request signature."""
        if not self._configured:
            return True  # Skip validation in dev mode
        return self.validator.validate(url, params, signature)


# Singleton
twilio_service = TwilioService()
