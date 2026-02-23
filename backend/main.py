from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import create_tables
from app.services.scheduler import setup_scheduler
from app.config import get_settings
from app.routers import (
    clients,
    appointments,
    calendar_sync,
    leads,
    inventory,
    chat,
    sms,
    aftercare,
    reports,
    dashboard,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await create_tables()
    scheduler = setup_scheduler()
    scheduler.start()
    print("Salon API started. Scheduler running.")
    yield
    # Shutdown
    scheduler.shutdown(wait=False)
    print("Salon API shutting down.")


app = FastAPI(
    title="Salon Management API",
    description="AI-powered salon management for hair stylists",
    version="1.0.0",
    lifespan=lifespan,
)

settings = get_settings()
cors_origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_PREFIX = "/api/v1"

app.include_router(clients.router, prefix=API_PREFIX)
app.include_router(appointments.router, prefix=API_PREFIX)
app.include_router(calendar_sync.router, prefix=API_PREFIX)
app.include_router(leads.router, prefix=API_PREFIX)
app.include_router(inventory.router, prefix=API_PREFIX)
app.include_router(chat.router, prefix=API_PREFIX)
app.include_router(sms.router, prefix=API_PREFIX)
app.include_router(aftercare.router, prefix=API_PREFIX)
app.include_router(reports.router, prefix=API_PREFIX)
app.include_router(dashboard.router, prefix=API_PREFIX)


@app.get("/")
async def root():
    return {"status": "ok", "message": "Salon Management API is running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
