"""
FAQ Chatbot AI service.
Handles streaming conversations for both the web chat widget and inbound SMS.
Uses tool use to check availability and pricing in real time.
"""
import json
import asyncio
from typing import AsyncGenerator
from app.services.ai.client import anthropic_client, MODEL
from app.config import get_settings

settings = get_settings()

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

def build_system_prompt() -> str:
    return f"""You are {settings.stylist_name}'s friendly virtual assistant for {settings.salon_name}.
You help clients get answers 24/7 — even when {settings.stylist_name} is with another client or off the clock.

Your personality: warm, knowledgeable, professional. You sound like a real person, not a bot.

KEY INFORMATION:
- Salon: {settings.salon_name}
- Stylist: {settings.stylist_name}
- Hours: {settings.salon_hours_start} – {settings.salon_hours_end} (Mon–Sat)
- Timezone: {settings.salon_timezone}
- Booking: {settings.booking_link or "Contact us to book"}

SERVICES & PRICING (approximate — confirm with stylist for exact quotes):
- Tape-In Extensions (partial set): $300–$500
- Tape-In Extensions (full head): $500–$900
- Hand-Tied Weft Extensions: $800–$1,400
- Keratin Bond Extensions: $700–$1,200
- Extension Removal: $75–$150
- Extension Reuse/Re-tape: $150–$250
- Haircut (clients only): $65–$95
- Color (balayage/highlights): $200–$400

EXTENSION CARE BASICS:
- Wash 2-3x per week with sulfate-free shampoo
- Brush gently from ends up, morning and night
- Use a silk pillowcase or loosely braid before sleep
- Avoid heat directly at bonds/tapes
- Come in every 6–8 weeks for maintenance

FREQUENTLY ASKED QUESTIONS:
- How long do extensions last? Tape-ins: 6–8 weeks before move-up. Hand-tied: 8–12 weeks. With good care, hair can be reused 2–3 times.
- Does the consultation cost anything? No, consultations are complimentary.
- Do you only use your own hair brand? Yes, {settings.salon_name} uses {settings.stylist_name}'s exclusive extension line for quality control.
- Can I color my extensions? Pre-colored extensions are available. Post-install coloring is not recommended.

When a client asks about booking or availability, use the check_availability tool to provide real information.
When a client asks about exact service pricing, use the get_service_pricing tool.

If you don't know something specific, say: "Great question — I'll make sure {settings.stylist_name} follows up with you personally. Can I get your name and best contact number?"

Keep responses concise. For SMS, aim for under 160 characters when possible.
Never make up prices. Always encourage booking a free consultation for custom quotes."""


# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------

AVAILABILITY_TOOL = {
    "name": "check_availability",
    "description": "Check available appointment slots for a given date and service. Call this when a client asks about booking or availability.",
    "input_schema": {
        "type": "object",
        "properties": {
            "date": {
                "type": "string",
                "description": "Date to check in YYYY-MM-DD format"
            },
            "service": {
                "type": "string",
                "description": "Service the client is interested in"
            }
        },
        "required": ["date"]
    }
}

PRICING_TOOL = {
    "name": "get_service_pricing",
    "description": "Get current pricing for a specific service. Use this to provide accurate pricing information.",
    "input_schema": {
        "type": "object",
        "properties": {
            "service_name": {
                "type": "string",
                "description": "Name of the service to get pricing for"
            }
        },
        "required": ["service_name"]
    }
}

TOOLS = [AVAILABILITY_TOOL, PRICING_TOOL]


# ---------------------------------------------------------------------------
# Tool execution (called when Claude requests a tool)
# ---------------------------------------------------------------------------

async def execute_tool(tool_name: str, tool_input: dict) -> str:
    """Execute a tool call and return the result as a string."""
    if tool_name == "check_availability":
        # In a real deployment this would call the calendar service
        # For now return a helpful placeholder
        date = tool_input.get("date", "")
        service = tool_input.get("service", "the requested service")
        return (
            f"I can check availability for {date}. "
            f"To see real-time slots and book, please visit: {settings.booking_link or 'contact us directly'}. "
            f"{settings.stylist_name} typically has morning and afternoon slots available Tuesday–Saturday."
        )

    if tool_name == "get_service_pricing":
        service = tool_input.get("service_name", "")
        pricing_map = {
            "tape": "Tape-In Extensions range from $300 (partial) to $900 (full head), depending on length and density needed.",
            "weft": "Hand-Tied Weft Extensions start at $800 for a starter set, up to $1,400+ for a full installation.",
            "keratin": "Keratin Bond Extensions are typically $700–$1,200 depending on head size and desired fullness.",
            "removal": "Extension removal is $75–$150. We recommend booking removal with your next installation.",
            "cut": "Haircuts for extension clients are $65–$95.",
            "color": "Color services (balayage, highlights) range from $200–$400.",
        }
        service_lower = service.lower()
        for key, price in pricing_map.items():
            if key in service_lower:
                return price
        return f"Pricing for {service} varies based on your hair goals. A free consultation will give you an exact quote tailored to you."

    return f"Tool {tool_name} is not available."


# ---------------------------------------------------------------------------
# Streaming chat (for web widget SSE)
# ---------------------------------------------------------------------------

async def stream_chat_response(
    messages: list[dict],
    channel: str = "web"
) -> AsyncGenerator[str, None]:
    """
    Stream an AI response for the FAQ chatbot.
    Yields SSE-formatted data strings.
    Handles tool calls by executing them and continuing the conversation.
    """
    system = build_system_prompt()
    current_messages = list(messages)

    # Loop to handle potential tool calls
    while True:
        with anthropic_client.messages.stream(
            model=MODEL,
            max_tokens=1024,
            system=system,
            tools=TOOLS,
            messages=current_messages,
        ) as stream:
            collected_text = ""
            for text in stream.text_stream:
                collected_text += text
                yield f"data: {json.dumps({'type': 'text', 'content': text})}\n\n"

            final_message = stream.get_final_message()

        if final_message.stop_reason == "end_turn":
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
            break

        if final_message.stop_reason == "tool_use":
            # Append assistant message with tool use blocks
            current_messages.append({"role": "assistant", "content": final_message.content})

            # Execute all tool calls
            tool_results = []
            for block in final_message.content:
                if block.type == "tool_use":
                    result = await execute_tool(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    })

            current_messages.append({"role": "user", "content": tool_results})
            # Continue loop to get the response after tool execution
        else:
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
            break


# ---------------------------------------------------------------------------
# Non-streaming chat (for SMS responses)
# ---------------------------------------------------------------------------

async def get_sms_response(messages: list[dict]) -> str:
    """
    Non-streaming response for SMS. Returns the final text response.
    Handles tool calls synchronously.
    """
    system = build_system_prompt()
    current_messages = list(messages)

    while True:
        response = anthropic_client.messages.create(
            model=MODEL,
            max_tokens=512,
            system=system,
            tools=TOOLS,
            messages=current_messages,
        )

        if response.stop_reason == "end_turn":
            text_blocks = [b for b in response.content if b.type == "text"]
            return text_blocks[0].text if text_blocks else "Sorry, I couldn't process that. Please try again."

        if response.stop_reason == "tool_use":
            current_messages.append({"role": "assistant", "content": response.content})
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    result = await execute_tool(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    })
            current_messages.append({"role": "user", "content": tool_results})
        else:
            text_blocks = [b for b in response.content if b.type == "text"]
            return text_blocks[0].text if text_blocks else "Sorry, I couldn't process that."
