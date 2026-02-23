import json
import secrets
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.communication import ChatSession
from app.schemas.communication import ChatSessionCreate, ChatSessionRead, SendMessageRequest
from app.services.ai.chat_agent import stream_chat_response

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/session", response_model=ChatSessionRead, status_code=201)
async def create_session(data: ChatSessionCreate, db: AsyncSession = Depends(get_db)):
    """Start a new chat session."""
    token = secrets.token_urlsafe(32)
    session = ChatSession(
        session_token=token,
        client_id=data.client_id,
        channel=data.channel,
        messages_json="[]",
    )
    db.add(session)
    await db.flush()
    await db.refresh(session)
    return session


@router.get("/session/{token}/history", response_model=ChatSessionRead)
async def get_session_history(token: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ChatSession).where(ChatSession.session_token == token)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    return session


@router.post("/session/{token}/message")
async def send_message(
    token: str,
    body: SendMessageRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Send a message to the FAQ chatbot and stream the response.
    Appends the user message and AI response to the session history.
    """
    result = await db.execute(
        select(ChatSession).where(ChatSession.session_token == token)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")

    # Parse existing messages
    try:
        messages = json.loads(session.messages_json)
    except Exception:
        messages = []

    # Add user message
    messages.append({"role": "user", "content": body.content})

    # We need to collect the full response to save it, while also streaming
    # We do this by streaming and buffering simultaneously
    collected_response = []

    async def stream_and_save():
        nonlocal messages, collected_response
        assistant_text = ""

        async for chunk in stream_chat_response(messages, session.channel):
            yield chunk
            # Parse text chunks to accumulate the response
            if chunk.startswith("data: "):
                try:
                    event = json.loads(chunk[6:])
                    if event.get("type") == "text":
                        assistant_text += event.get("content", "")
                    elif event.get("type") == "done":
                        # Save the full conversation to DB
                        messages.append({"role": "assistant", "content": assistant_text})
                        # Use a fresh DB session to save (the stream context may have expired)
                        from app.database import AsyncSessionLocal
                        async with AsyncSessionLocal() as save_db:
                            save_result = await save_db.execute(
                                select(ChatSession).where(ChatSession.session_token == token)
                            )
                            save_session = save_result.scalar_one_or_none()
                            if save_session:
                                save_session.messages_json = json.dumps(messages)
                                await save_db.commit()
                except Exception:
                    pass

    return StreamingResponse(
        stream_and_save(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.delete("/session/{token}")
async def end_session(token: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ChatSession).where(ChatSession.session_token == token)
    )
    session = result.scalar_one_or_none()
    if session:
        await db.delete(session)
        await db.commit()
    return {"message": "Session ended"}
