"""
AI service for monthly business report generation.
Uses adaptive thinking (Opus 4.6) for deeper business insights.
Supports streaming for the frontend to render the narrative progressively.
"""
import json
from typing import AsyncGenerator
from app.services.ai.client import anthropic_client, MODEL
from app.config import get_settings

settings = get_settings()

REPORT_SYSTEM_PROMPT = f"""You are a business analyst writing a monthly performance summary for {settings.stylist_name},
the owner of {settings.salon_name} — a boutique salon specializing in premium hair extensions.

Your audience is a solo stylist who is also the business owner. She wants:
1. Clear understanding of how the month went (no fluff)
2. Specific insights about what drove performance
3. Actionable recommendations she can implement immediately
4. Awareness of trends she should be tracking

Write directly to her in second person ("you earned", "your top service", "you should consider").
Lead with the most important insight. Be specific — cite actual numbers from the data.
Keep it under 400 words. No bullet-point walls — use short paragraphs.
End with 3 numbered action items for next month."""


async def generate_report_stream(report_data: dict) -> AsyncGenerator[str, None]:
    """
    Stream the AI-generated monthly business narrative.
    Uses adaptive thinking for deeper analysis.
    Yields SSE-formatted data strings.
    """
    report_text = _build_report_prompt(report_data)

    with anthropic_client.messages.stream(
        model=MODEL,
        max_tokens=16000,
        thinking={"type": "adaptive"},
        output_config={"effort": "high"},
        system=REPORT_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": report_text}]
    ) as stream:
        for event in stream:
            # Only stream the text content, skip thinking blocks
            if (
                hasattr(event, "type")
                and event.type == "content_block_delta"
                and hasattr(event, "delta")
                and hasattr(event.delta, "type")
                and event.delta.type == "text_delta"
            ):
                yield f"data: {json.dumps({'type': 'text', 'content': event.delta.text})}\n\n"

    yield f"data: {json.dumps({'type': 'done'})}\n\n"


async def generate_report_sync(report_data: dict) -> str:
    """Non-streaming version — returns complete report text."""
    report_text = _build_report_prompt(report_data)

    response = anthropic_client.messages.create(
        model=MODEL,
        max_tokens=16000,
        thinking={"type": "adaptive"},
        output_config={"effort": "high"},
        system=REPORT_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": report_text}]
    )

    text_blocks = [b for b in response.content if b.type == "text"]
    return text_blocks[0].text if text_blocks else "Report generation failed."


def _build_report_prompt(data: dict) -> str:
    """Build the detailed prompt from report data."""
    month = data.get("report_month", "Unknown")
    prev_month = data.get("prev_month", {})

    def fmt_currency(val):
        return f"${float(val):,.2f}" if val is not None else "N/A"

    def fmt_change(curr, prev):
        if prev and float(prev) > 0:
            change = ((float(curr) - float(prev)) / float(prev)) * 100
            direction = "up" if change >= 0 else "down"
            return f"({direction} {abs(change):.1f}% vs prior month)"
        return ""

    top_services = data.get("top_services_json")
    if isinstance(top_services, str):
        try:
            top_services = json.loads(top_services)
        except Exception:
            top_services = []

    services_text = ""
    if top_services:
        services_text = "\n".join(
            f"  - {s.get('service', 'Unknown')}: {s.get('count', 0)} appointments, "
            f"{fmt_currency(s.get('revenue', 0))}"
            for s in top_services[:5]
        )
    else:
        services_text = "  (No service breakdown available)"

    prompt = f"""MONTHLY BUSINESS REPORT — {month}

REVENUE:
  Total revenue: {fmt_currency(data.get('revenue_total'))} {fmt_change(data.get('revenue_total', 0), prev_month.get('revenue_total'))}
  Previous month: {fmt_currency(prev_month.get('revenue_total'))}
  Inventory spend: {fmt_currency(data.get('inventory_spend', 0))}
  Net profit estimate: {fmt_currency(float(data.get('revenue_total', 0)) - float(data.get('inventory_spend', 0)))}

APPOINTMENTS:
  Total completed: {data.get('appointments_count', 0)} {fmt_change(data.get('appointments_count', 0), prev_month.get('appointments_count'))}
  Previous month: {prev_month.get('appointments_count', 'N/A')}

CLIENTS:
  New clients this month: {data.get('new_clients_count', 0)}
  Lapsed clients recovered: {data.get('lapsed_recovered', 0)}
  Extension leads converted: {data.get('leads_converted', 0)}

TOP SERVICES:
{services_text}

ADDITIONAL CONTEXT:
{data.get('additional_notes', 'No additional context provided.')}

Please write a monthly performance summary based on this data."""

    return prompt
