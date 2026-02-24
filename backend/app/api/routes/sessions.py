from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.session import SessionCreate, SessionRead, SessionReadWithMembers, SessionUpdate
from app.services.session_service import (
    create_session,
    delete_session,
    get_session_by_slug,
    join_session,
    list_sessions_for_user,
    update_session,
)

router = APIRouter(prefix="/sessions", tags=["sessions"])


def _assert_owner(session, user: User):
    if session.owner_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Only the owner can perform this action")


@router.post("", response_model=SessionRead, status_code=status.HTTP_201_CREATED)
async def create(
    data: SessionCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await create_session(db, data, owner_id=user.id)


@router.get("", response_model=list[SessionRead])
async def list_mine(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await list_sessions_for_user(db, user.id)


@router.get("/{slug}", response_model=SessionReadWithMembers)
async def get_one(
    slug: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    session = await get_session_by_slug(db, slug)
    if session is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Session not found")
    # Must be a member or session is public
    member_ids = {m.user_id for m in session.members}
    if not session.is_public and user.id not in member_ids:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Access denied")

    from app.schemas.session import SessionMemberRead
    members = [
        SessionMemberRead(
            user_id=m.user_id,
            username=m.user.username,
            role=m.role,
            joined_at=m.joined_at,
        )
        for m in session.members
    ]
    return SessionReadWithMembers(
        id=session.id,
        slug=session.slug,
        title=session.title,
        language=session.language,
        content=session.content,
        is_public=session.is_public,
        owner_id=session.owner_id,
        created_at=session.created_at,
        updated_at=session.updated_at,
        members=members,
    )


@router.patch("/{slug}", response_model=SessionRead)
async def update(
    slug: str,
    data: SessionUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    session = await get_session_by_slug(db, slug)
    if session is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Session not found")
    _assert_owner(session, user)
    return await update_session(db, session, data)


@router.delete("/{slug}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(
    slug: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    session = await get_session_by_slug(db, slug)
    if session is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Session not found")
    _assert_owner(session, user)
    await delete_session(db, session)


@router.post("/{slug}/join", status_code=status.HTTP_200_OK)
async def join(
    slug: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    session = await get_session_by_slug(db, slug)
    if session is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Session not found")
    if not session.is_public:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Session is private")
    await join_session(db, session, user.id)
    return {"joined": True, "slug": slug}
