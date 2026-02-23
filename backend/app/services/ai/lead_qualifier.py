"""
AI service for extension lead qualification and quote generation.
- qualify_lead(): structured output via forced tool call
- generate_quote_stream(): streaming personalized quote text
- draft_follow_up(): short follow-up SMS text
"""
import json
from typing import AsyncGenerator
from app.services.ai.client import anthropic_client, MODEL
from app.config import get_settings

settings = get_settings()

# ---------------------------------------------------------------------------
# Qualification tool definition
# ---------------------------------------------------------------------------

QUALIFY_TOOL = {
    "name": "qualify_lead",
    "description": "Return a structured qualification assessment for this extension lead.",
    "input_schema": {
        "type": "object",
        "properties": {
            "score": {
                "type": "integer",
                "description": "Lead score from 0 (completely unqualified) to 100 (perfect fit, ready to book)"
            },
            "tier": {
                "type": "string",
                "enum": ["hot", "warm", "cold", "unqualified"],
                "description": "hot=ready to book, warm=interested but needs nurturing, cold=unsure, unqualified=wrong fit"
            },
            "recommended_extension_type": {
                "type": "string",
                "description": "Best extension type for this client's hair and goals"
            },
            "concerns": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Potential concerns or risks with this client (e.g., hair too thin, budget mismatch)"
            },
            "recommended_action": {
                "type": "string",
                "description": "Specific next action the stylist should take with this lead"
            },
            "consultation_priority": {
                "type": "string",
                "enum": ["immediate", "this_week", "flexible"],
                "description": "How urgently to schedule a consultation"
            }
        },
        "required": ["score", "tier", "recommended_extension_type", "concerns", "recommended_action", "consultation_priority"]
    }
}


def build_lead_context(lead_data: dict) -> str:
    """Build a comprehensive context string from lead data."""
    return f"""EXTENSION LEAD PROFILE:
Name: {lead_data.get('name', 'Unknown')}
Source: {lead_data.get('source', 'Unknown')}

HAIR PROFILE:
- Current hair length: {lead_data.get('hair_length', 'Not specified')}
- Hair texture: {lead_data.get('hair_texture', 'Not specified')}
- Desired length after extensions: {lead_data.get('desired_length', 'Not specified')}
- Desired color: {lead_data.get('desired_color', 'Not specified')}
- Preferred extension type: {lead_data.get('extension_type', 'Not specified / open to recommendation')}

BUDGET & TIMELINE:
- Budget range: {lead_data.get('budget_range', 'Not specified')}
- Timeline (when they want it done): {lead_data.get('timeline', 'Not specified')}

NOTES: {lead_data.get('notes', 'None')}

CONTEXT: This lead is inquiring about hair extension services at {settings.salon_name}.
{settings.stylist_name} specializes in tape-in, hand-tied weft, and keratin bond extensions.
Premium hair extension services typically range from $300–$1,400 depending on method and density.
Assess this lead's fit, readiness, and recommended next steps."""


async def qualify_lead(lead_data: dict) -> dict:
    """
    Run AI qualification on a lead.
    Returns structured qualification data using forced tool call.
    """
    response = anthropic_client.messages.create(
        model=MODEL,
        max_tokens=1024,
        tools=[QUALIFY_TOOL],
        tool_choice={"type": "tool", "name": "qualify_lead"},
        messages=[{
            "role": "user",
            "content": build_lead_context(lead_data)
        }]
    )

    # The response is guaranteed to be a tool_use block due to tool_choice
    for block in response.content:
        if block.type == "tool_use" and block.name == "qualify_lead":
            return block.input

    return {
        "score": 50,
        "tier": "warm",
        "recommended_extension_type": "tape-in (consultation needed)",
        "concerns": ["Incomplete lead information"],
        "recommended_action": "Schedule consultation to gather more information",
        "consultation_priority": "flexible"
    }


# ---------------------------------------------------------------------------
# Quote generation (streaming)
# ---------------------------------------------------------------------------

async def generate_quote_stream(lead_data: dict) -> AsyncGenerator[str, None]:
    """
    Stream a personalized quote message for an extension lead.
    Yields SSE-formatted data strings for the frontend QuoteBuilder.
    """
    import json as _json

    system = f"""You are {settings.stylist_name} of {settings.salon_name}, writing a personalized quote message for a potential extension client.

Write in first person as {settings.stylist_name}. Be warm, professional, and specific to their hair goals.
Include:
1. A warm opening that references their specific hair situation
2. The recommended extension type and why it's right for them
3. An investment range for their service
4. What's included (consultation, install, aftercare guide)
5. A soft call-to-action to book a complimentary consultation

Keep it under 200 words. Sound like a real person, not a template. Avoid generic filler phrases."""

    lead_context = f"""Write a quote message for this client:
{build_lead_context(lead_data)}

Their AI qualification: {lead_data.get('ai_qualification_tier', 'warm')} lead.
Recommended extension type: {lead_data.get('recommended_extension_type', 'tape-in extensions')}."""

    with anthropic_client.messages.stream(
        model=MODEL,
        max_tokens=512,
        system=system,
        messages=[{"role": "user", "content": lead_context}]
    ) as stream:
        for text in stream.text_stream:
            yield f"data: {_json.dumps({'type': 'text', 'content': text})}\n\n"

    yield f"data: {_json.dumps({'type': 'done'})}\n\n"


# ---------------------------------------------------------------------------
# Follow-up SMS drafting
# ---------------------------------------------------------------------------

async def draft_follow_up_sms(lead_data: dict) -> str:
    """Draft a personalized follow-up SMS for a lead who hasn't responded."""
    days_since_inquiry = lead_data.get("days_since_inquiry", 7)
    follow_up_count = lead_data.get("follow_up_count", 0)

    if follow_up_count == 0:
        tone_instruction = "This is the first follow-up. Be warm and curious, not pushy."
    elif follow_up_count == 1:
        tone_instruction = "This is the second follow-up. Create gentle urgency — mention limited availability."
    else:
        tone_instruction = "This is a final follow-up. Be gracious, leave the door open for the future."

    response = anthropic_client.messages.create(
        model=MODEL,
        max_tokens=200,
        system=f"""You are {settings.stylist_name} sending a follow-up text to a potential extension client.
Write a SHORT, personal SMS (under 160 characters ideally, max 320 characters).
{tone_instruction}
Sign off as {settings.stylist_name}. Sound human, not automated.""",
        messages=[{
            "role": "user",
            "content": f"""Draft a follow-up for:
Name: {lead_data.get('name')}
Days since initial inquiry: {days_since_inquiry}
They were interested in: {lead_data.get('extension_type', 'extensions')}
Follow-up number: {follow_up_count + 1}"""
        }]
    )

    text_blocks = [b for b in response.content if b.type == "text"]
    return text_blocks[0].text if text_blocks else f"Hi {lead_data.get('name', '')}! Just following up on your extension inquiry. Would love to get you in for a free consultation!"


# ---------------------------------------------------------------------------
# Lapsed client outreach SMS
# ---------------------------------------------------------------------------

async def draft_lapsed_outreach(client_data: dict) -> str:
    """Draft a personalized re-engagement SMS for a lapsed client."""
    response = anthropic_client.messages.create(
        model=MODEL,
        max_tokens=200,
        system=f"""You are {settings.stylist_name} texting a client you haven't seen in a while.
Write a warm, personal SMS under 160 characters.
Reference their last service naturally. Sound like you genuinely miss seeing them.
Don't use generic "we miss you" phrasing. Be specific and personal.
Sign as {settings.stylist_name}.""",
        messages=[{
            "role": "user",
            "content": f"""Draft a re-engagement message:
Client: {client_data.get('full_name')}
Last service: {client_data.get('last_service', 'hair appointment')}
Weeks since last visit: {client_data.get('weeks_since_visit', 12)}
Total visits: {client_data.get('total_visits', 'several')}"""
        }]
    )

    text_blocks = [b for b in response.content if b.type == "text"]
    return text_blocks[0].text if text_blocks else f"Hi {client_data.get('full_name', '')}! It's been a while — I'd love to see you again! Reply BOOK to grab a slot. - {settings.stylist_name}"
