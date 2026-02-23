# Salon Management App

AI-powered salon management for a solo hair stylist with her own extension line.

## Stack
- **Backend**: Python 3.12, FastAPI, SQLite (async SQLAlchemy + aiosqlite)
- **AI**: Claude Opus 4.6 (Anthropic) — chatbot, lead qualification, quote generation, inventory advisor, monthly reports
- **SMS**: Twilio
- **Calendar**: Google Calendar (OAuth2)
- **Frontend**: React 18 + TypeScript + Vite, Tailwind CSS, TanStack Query, FullCalendar, Recharts

---

## Quick Start

### Prerequisites
- Python 3.12+
- Node.js 20+ and npm

### 1. Backend

```bash
cd backend

# Create and activate virtual environment
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy and fill in environment variables
cp ../.env.example .env
# Edit .env with your API keys

# Start the API server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at http://localhost:8000
Interactive docs: http://localhost:8000/docs

### 2. Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start the dev server
npm run dev
```

Open http://localhost:5173

---

## Environment Variables

Copy `.env.example` to `backend/.env` and fill in:

| Variable | Description |
|---|---|
| `ANTHROPIC_API_KEY` | Get from https://console.anthropic.com |
| `TWILIO_ACCOUNT_SID` | Twilio Console |
| `TWILIO_AUTH_TOKEN` | Twilio Console |
| `TWILIO_PHONE_NUMBER` | Your Twilio phone number (E.164 format) |
| `GOOGLE_CLIENT_ID` | Google Cloud Console — OAuth2 credentials |
| `GOOGLE_CLIENT_SECRET` | Google Cloud Console |
| `SALON_NAME` | Your salon name |
| `STYLIST_NAME` | Your name |
| `SALON_TIMEZONE` | e.g. `America/New_York` |
| `BOOKING_LINK` | Your public booking URL |

> Twilio and Google Calendar are **optional for development**. The app runs in mock mode if credentials are missing.

---

## Features

### Dashboard
- Real-time KPIs (revenue, appointments, clients, leads)
- Action item alerts panel (low stock, lapsed clients, due aftercare, calendar conflicts)
- Upcoming appointments widget

### Clients
- Full client database with search
- Visit history and spending tracking
- Automatic lapsed client flagging (90+ days)
- AI-drafted re-engagement SMS

### Appointments
- FullCalendar view (month/week/day)
- Google Calendar sync (bidirectional)
- Mark complete → auto-creates aftercare sequence
- Waitlist management on cancellation

### Extension Leads Pipeline
- Kanban board by pipeline stage
- AI qualification scoring (0–100)
- Streaming quote generation
- Follow-up SMS automation

### Inventory
- Stock tracking with reorder thresholds
- AI-powered reorder recommendations
- Purchase order management

### Chat FAQ
- Streaming AI chatbot (Claude) for client FAQs
- Handles pricing, availability, aftercare questions
- Also handles inbound Twilio SMS

### Aftercare Sequences
- Day-3 check-in message
- Week-2 follow-up + upsell
- Automated via scheduled jobs (9am daily)

### Reports
- Monthly revenue and appointment stats
- Daily revenue bar chart
- Top services breakdown
- AI-generated business narrative with insights (adaptive thinking)

---

## Google Calendar Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a project → Enable Google Calendar API
3. Create OAuth2 credentials (Web application)
4. Add `http://localhost:8000/api/v1/calendar/callback` as authorized redirect URI
5. Copy Client ID and Secret to `.env`
6. In the app, go to Settings → Connect Google Calendar

## Twilio Setup

1. Create a [Twilio account](https://twilio.com)
2. Get a phone number
3. Set webhook URL to `https://your-domain.com/api/v1/sms/webhook` (requires public URL for inbound SMS — use [ngrok](https://ngrok.com) for local dev)
