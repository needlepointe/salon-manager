"""
AI service for inventory reorder recommendations.
Uses forced tool call to return structured, actionable recommendations.
"""
from app.services.ai.client import anthropic_client, MODEL
from app.config import get_settings

settings = get_settings()

REORDER_TOOL = {
    "name": "create_reorder_recommendation",
    "description": "Return structured inventory reorder recommendations based on current stock levels and usage patterns.",
    "input_schema": {
        "type": "object",
        "properties": {
            "recommendations": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "product_id": {"type": "integer"},
                        "product_name": {"type": "string"},
                        "current_stock": {"type": "number"},
                        "recommended_quantity": {"type": "number"},
                        "urgency": {
                            "type": "string",
                            "enum": ["immediate", "soon", "optional"]
                        },
                        "reason": {"type": "string"},
                        "estimated_cost": {"type": "number"}
                    },
                    "required": ["product_id", "product_name", "current_stock", "recommended_quantity", "urgency", "reason"]
                }
            },
            "summary": {
                "type": "string",
                "description": "Brief overall summary of the inventory situation and key actions needed"
            },
            "discontinue_suggestions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "product_id": {"type": "integer"},
                        "product_name": {"type": "string"},
                        "reason": {"type": "string"}
                    },
                    "required": ["product_id", "product_name", "reason"]
                },
                "description": "Products to consider discontinuing based on low usage"
            }
        },
        "required": ["recommendations", "summary"]
    }
}


async def get_reorder_recommendations(inventory_context: dict) -> dict:
    """
    Analyze inventory data and return structured reorder recommendations.

    inventory_context should contain:
    - low_stock_items: list of products below threshold
    - recent_usage: dict of product_id -> avg_weekly_usage
    - upcoming_services: list of services scheduled in next 14 days
    - all_products: full product list for discontinuation analysis
    """
    context_text = f"""INVENTORY ANALYSIS REQUEST for {settings.salon_name}

LOW STOCK ITEMS (below reorder threshold):
{_format_low_stock(inventory_context.get('low_stock_items', []))}

USAGE PATTERNS (avg weekly usage over last 30 days):
{_format_usage(inventory_context.get('recent_usage', {}))}

UPCOMING SERVICES (next 14 days — demand signal):
{_format_upcoming(inventory_context.get('upcoming_services', []))}

ALL ACTIVE PRODUCTS (for discontinuation analysis):
{_format_all_products(inventory_context.get('all_products', []))}

Based on this data, provide reorder recommendations that will keep the salon stocked efficiently.
Flag products that appear to be slow movers and might be worth discontinuing.
Consider the upcoming service schedule when assessing urgency."""

    response = anthropic_client.messages.create(
        model=MODEL,
        max_tokens=2048,
        tools=[REORDER_TOOL],
        tool_choice={"type": "tool", "name": "create_reorder_recommendation"},
        messages=[{"role": "user", "content": context_text}]
    )

    for block in response.content:
        if block.type == "tool_use" and block.name == "create_reorder_recommendation":
            return block.input

    return {"recommendations": [], "summary": "Unable to generate recommendations at this time.", "discontinue_suggestions": []}


def _format_low_stock(items: list) -> str:
    if not items:
        return "  (None currently below threshold)"
    lines = []
    for item in items:
        lines.append(
            f"  - {item['name']} (ID:{item['id']}): {item['current_stock']} {item['stock_unit']} "
            f"(threshold: {item['reorder_threshold']}, last ordered: {item.get('last_ordered_at', 'never')})"
        )
    return "\n".join(lines)


def _format_usage(usage: dict) -> str:
    if not usage:
        return "  (No usage data available)"
    lines = []
    for product_id, avg_usage in usage.items():
        lines.append(f"  - Product ID {product_id}: ~{avg_usage:.1f} units/week")
    return "\n".join(lines)


def _format_upcoming(services: list) -> str:
    if not services:
        return "  (No upcoming appointments)"
    from collections import Counter
    counts = Counter(services)
    lines = [f"  - {service}: {count} appointment(s)" for service, count in counts.most_common()]
    return "\n".join(lines)


def _format_all_products(products: list) -> str:
    if not products:
        return "  (No product data)"
    lines = []
    for p in products[:30]:  # limit to prevent huge prompts
        lines.append(
            f"  - {p['name']} (ID:{p['id']}): stock={p['current_stock']}, "
            f"weekly_usage={p.get('weekly_usage', 0):.1f}"
        )
    return "\n".join(lines)
