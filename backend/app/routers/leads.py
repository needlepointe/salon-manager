import json
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models.lead import ExtensionLead
from app.models.communication import SmsMessage
from app.schemas.lead import LeadCreate, LeadUpdate, LeadRead, LeadPipelineSummary
from app.services.ai.lead_qualifier import qualify_lead, generate_quote_stream, draft_follow_up_sms
from app.services.twilio_service import twilio_service

router = APIRouter(prefix="/leads", tags=["leads"])


@router.get("/pipeline-summary", response_model=LeadPipelineSummary)
async def get_pipeline_summary(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ExtensionLead.pipeline_stage, func.count(ExtensionLead.id))
        .group_by(ExtensionLead.pipeline_stage)
    )
    counts = dict(result.all())
    return LeadPipelineSummary(**{k: counts.get(k, 0) for k in LeadPipelineSummary.model_fields})


@router.get("/", response_model=list[LeadRead])
async def list_leads(
    stage: str | None = Query(None),
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    query = select(ExtensionLead)
    if stage:
        query = query.where(ExtensionLead.pipeline_stage == stage)
    query = query.order_by(ExtensionLead.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/", response_model=LeadRead, status_code=201)
async def create_lead(data: LeadCreate, db: AsyncSession = Depends(get_db)):
    lead = ExtensionLead(**data.model_dump())
    db.add(lead)
    await db.flush()
    await db.refresh(lead)
    return lead


@router.get("/{lead_id}", response_model=LeadRead)
async def get_lead(lead_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ExtensionLead).where(ExtensionLead.id == lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@router.put("/{lead_id}", response_model=LeadRead)
async def update_lead(lead_id: int, data: LeadUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ExtensionLead).where(ExtensionLead.id == lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(lead, field, value)
    await db.flush()
    await db.refresh(lead)
    return lead


@router.post("/{lead_id}/qualify")
async def qualify_lead_endpoint(lead_id: int, db: AsyncSession = Depends(get_db)):
    """Run AI qualification scoring on a lead."""
    result = await db.execute(select(ExtensionLead).where(ExtensionLead.id == lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    lead_data = {
        "name": lead.name,
        "source": lead.source,
        "hair_length": lead.hair_length,
        "hair_texture": lead.hair_texture,
        "desired_length": lead.desired_length,
        "desired_color": lead.desired_color,
        "extension_type": lead.extension_type,
        "budget_range": lead.budget_range,
        "timeline": lead.timeline,
        "notes": lead.notes,
    }

    qualification = await qualify_lead(lead_data)

    # Update lead with qualification results
    lead.ai_qualification_score = qualification.get("score")
    lead.ai_qualification_tier = qualification.get("tier")
    lead.ai_qualification_notes = json.dumps({
        "recommended_extension_type": qualification.get("recommended_extension_type"),
        "concerns": qualification.get("concerns", []),
        "recommended_action": qualification.get("recommended_action"),
        "consultation_priority": qualification.get("consultation_priority"),
    })
    if lead.pipeline_stage == "new":
        lead.pipeline_stage = "qualified"

    await db.commit()
    return qualification


@router.post("/{lead_id}/generate-quote")
async def generate_quote_endpoint(lead_id: int, db: AsyncSession = Depends(get_db)):
    """Stream an AI-generated personalized quote for this lead."""
    result = await db.execute(select(ExtensionLead).where(ExtensionLead.id == lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    lead_data = {
        "name": lead.name,
        "hair_length": lead.hair_length,
        "hair_texture": lead.hair_texture,
        "desired_length": lead.desired_length,
        "desired_color": lead.desired_color,
        "extension_type": lead.extension_type,
        "budget_range": lead.budget_range,
        "ai_qualification_tier": lead.ai_qualification_tier,
        "recommended_extension_type": (
            json.loads(lead.ai_qualification_notes).get("recommended_extension_type")
            if lead.ai_qualification_notes
            else lead.extension_type
        ),
    }

    return StreamingResponse(
        generate_quote_stream(lead_data),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/{lead_id}/send-quote")
async def send_quote(lead_id: int, quote_text: str, db: AsyncSession = Depends(get_db)):
    """Send the finalized quote via SMS."""
    result = await db.execute(select(ExtensionLead).where(ExtensionLead.id == lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    sid = twilio_service.send_sms(lead.phone, quote_text)
    db.add(SmsMessage(
        lead_id=lead.id,
        phone_number=lead.phone,
        direction="outbound",
        body=quote_text,
        twilio_sid=sid,
        status="sent",
        message_type="quote",
    ))
    lead.quote_text = quote_text
    lead.quote_sent_at = datetime.now()
    lead.pipeline_stage = "quoted"
    lead.next_follow_up_at = datetime.now() + timedelta(days=3)
    await db.commit()
    return {"message": "Quote sent", "twilio_sid": sid}


@router.post("/{lead_id}/follow-up")
async def send_follow_up(lead_id: int, db: AsyncSession = Depends(get_db)):
    """Draft and send an AI follow-up SMS to a lead."""
    result = await db.execute(select(ExtensionLead).where(ExtensionLead.id == lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    days_since = 0
    if lead.created_at:
        days_since = (datetime.now() - lead.created_at).days

    lead_data = {
        "name": lead.name,
        "days_since_inquiry": days_since,
        "extension_type": lead.extension_type or "extensions",
        "follow_up_count": lead.follow_up_count,
    }

    body = await draft_follow_up_sms(lead_data)
    sid = twilio_service.send_sms(lead.phone, body)

    db.add(SmsMessage(
        lead_id=lead.id,
        phone_number=lead.phone,
        direction="outbound",
        body=body,
        twilio_sid=sid,
        status="sent",
        message_type="follow_up",
    ))
    lead.follow_up_count += 1
    lead.last_follow_up_at = datetime.now()
    lead.next_follow_up_at = datetime.now() + timedelta(days=7)
    if lead.pipeline_stage == "quoted":
        lead.pipeline_stage = "follow_up"

    await db.commit()
    return {"message": "Follow-up sent", "body": body, "twilio_sid": sid}
