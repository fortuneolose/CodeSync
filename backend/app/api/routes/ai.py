"""
AI assistant routes — all responses are Server-Sent Events (SSE) streams.

Endpoint pattern:  POST /api/ai/{operation}
Auth:              Bearer JWT required
Session check:     user must be a member of the session (slug in body)
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.ai import ChatRequest, ExplainRequest, RefactorRequest
from app.services import ai_service
from app.services.session_service import get_session_by_slug

router = APIRouter(prefix="/ai", tags=["ai"])


async def _assert_member(slug: str, user: User, db: AsyncSession):
    session = await get_session_by_slug(db, slug)
    if session is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Session not found")
    member_ids = {m.user_id for m in session.members}
    if user.id not in member_ids:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Access denied")
    return session


@router.post("/explain")
async def explain(
    data: ExplainRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    await _assert_member(data.slug, user, db)
    return StreamingResponse(
        ai_service.explain_stream(data.code, data.language),
        media_type="text/event-stream",
        headers={"X-Accel-Buffering": "no", "Cache-Control": "no-cache"},
    )


@router.post("/refactor")
async def refactor(
    data: RefactorRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    await _assert_member(data.slug, user, db)
    return StreamingResponse(
        ai_service.refactor_stream(data.code, data.language),
        media_type="text/event-stream",
        headers={"X-Accel-Buffering": "no", "Cache-Control": "no-cache"},
    )


@router.post("/chat")
async def chat(
    data: ChatRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    await _assert_member(data.slug, user, db)
    return StreamingResponse(
        ai_service.chat_stream(
            data.code,
            data.language,
            data.message,
            [h.model_dump() for h in data.history],
        ),
        media_type="text/event-stream",
        headers={"X-Accel-Buffering": "no", "Cache-Control": "no-cache"},
    )
