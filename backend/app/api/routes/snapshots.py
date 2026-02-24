from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.snapshot import RestoreResponse, SnapshotCreate, SnapshotRead
from app.services.session_service import get_session_by_slug
from app.services.snapshot_service import (
    create_snapshot,
    delete_snapshot,
    get_snapshot,
    list_snapshots,
    restore_snapshot,
)

router = APIRouter(tags=["snapshots"])


async def _get_accessible_session(slug: str, user: User, db: AsyncSession):
    session = await get_session_by_slug(db, slug)
    if session is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Session not found")
    member_ids = {m.user_id for m in session.members}
    if user.id not in member_ids:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Access denied")
    return session


@router.post(
    "/sessions/{slug}/snapshots",
    response_model=SnapshotRead,
    status_code=status.HTTP_201_CREATED,
)
async def create(
    slug: str,
    data: SnapshotCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    session = await _get_accessible_session(slug, user, db)
    snap = await create_snapshot(db, session, data, user.id)
    return SnapshotRead(
        id=snap.id,
        session_id=snap.session_id,
        title=snap.title,
        content=snap.content,
        language=snap.language,
        created_by=snap.created_by,
        created_at=snap.created_at,
        author_username=snap.author.username if snap.author else None,
    )


@router.get("/sessions/{slug}/snapshots", response_model=list[SnapshotRead])
async def list_all(
    slug: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    session = await _get_accessible_session(slug, user, db)
    snaps = await list_snapshots(db, session.id)
    return [
        SnapshotRead(
            id=s.id,
            session_id=s.session_id,
            title=s.title,
            content=s.content,
            language=s.language,
            created_by=s.created_by,
            created_at=s.created_at,
            author_username=s.author.username if s.author else None,
        )
        for s in snaps
    ]


@router.post("/sessions/{slug}/snapshots/{snapshot_id}/restore", response_model=RestoreResponse)
async def restore(
    slug: str,
    snapshot_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    session = await _get_accessible_session(slug, user, db)
    if session.owner_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Only the owner can restore snapshots")
    snap = await get_snapshot(db, snapshot_id)
    if snap is None or snap.session_id != session.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Snapshot not found")
    await restore_snapshot(db, session, snap)
    return RestoreResponse(content=snap.content, language=snap.language, snapshot_id=snap.id)


@router.delete("/sessions/{slug}/snapshots/{snapshot_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(
    slug: str,
    snapshot_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    session = await _get_accessible_session(slug, user, db)
    snap = await get_snapshot(db, snapshot_id)
    if snap is None or snap.session_id != session.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Snapshot not found")
    await delete_snapshot(db, snap)
