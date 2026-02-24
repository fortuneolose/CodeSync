from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.session import Session
from app.models.snapshot import Snapshot
from app.schemas.snapshot import SnapshotCreate
from app.ws.connection_manager import manager


async def create_snapshot(
    db: AsyncSession,
    session: Session,
    data: SnapshotCreate,
    user_id: str,
) -> Snapshot:
    snap = Snapshot(
        session_id=session.id,
        title=data.title,
        content=data.content,
        language=data.language,
        created_by=user_id,
    )
    db.add(snap)
    await db.commit()
    await db.refresh(snap)
    return snap


async def list_snapshots(db: AsyncSession, session_id: str) -> list[Snapshot]:
    result = await db.execute(
        select(Snapshot)
        .where(Snapshot.session_id == session_id)
        .options(selectinload(Snapshot.author))
        .order_by(Snapshot.created_at.desc())
    )
    return list(result.scalars().all())


async def get_snapshot(db: AsyncSession, snapshot_id: str) -> Snapshot | None:
    result = await db.execute(
        select(Snapshot)
        .where(Snapshot.id == snapshot_id)
        .options(selectinload(Snapshot.author))
    )
    return result.scalar_one_or_none()


async def delete_snapshot(db: AsyncSession, snap: Snapshot) -> None:
    await db.delete(snap)
    await db.commit()


async def restore_snapshot(
    db: AsyncSession,
    session: Session,
    snap: Snapshot,
) -> None:
    """Restore session content from snapshot:
    1. Update DB content field.
    2. Clear Redis Yjs update log so next connections start fresh.
    3. Broadcast a restore control message over WebSocket.
    """
    import json
    session.content = snap.content
    session.language = snap.language
    await db.commit()

    # Clear Yjs update history for this session (best-effort; skip if Redis unavailable)
    try:
        await manager.clear_updates(session.slug)
    except Exception:
        pass

    # Notify all connected clients (best-effort)
    try:
        msg = json.dumps({
            "type": "session:restored",
            "content": snap.content,
            "language": snap.language,
            "snapshot_id": snap.id,
        }).encode()
        from app.ws.yjs_utils import write_var_uint
        framed = write_var_uint(100) + write_var_uint(len(msg)) + msg
        await manager.broadcast(session.slug, framed)
    except Exception:
        pass
