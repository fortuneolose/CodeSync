from __future__ import annotations

import secrets
import string

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.session import Session, SessionMember
from app.schemas.session import SessionCreate, SessionUpdate


def _generate_slug(length: int = 10) -> str:
    alphabet = string.ascii_lowercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


async def _unique_slug(db: AsyncSession) -> str:
    for _ in range(10):
        slug = _generate_slug()
        exists = await db.execute(select(Session).where(Session.slug == slug))
        if exists.scalar_one_or_none() is None:
            return slug
    raise RuntimeError("Could not generate a unique slug")


async def create_session(db: AsyncSession, data: SessionCreate, owner_id: str) -> Session:
    slug = await _unique_slug(db)
    session = Session(
        slug=slug,
        title=data.title,
        language=data.language,
        is_public=data.is_public,
        owner_id=owner_id,
    )
    db.add(session)
    await db.flush()  # get session.id before creating member

    member = SessionMember(session_id=session.id, user_id=owner_id, role="owner")
    db.add(member)
    await db.commit()
    await db.refresh(session)
    return session


async def get_session_by_slug(db: AsyncSession, slug: str) -> Session | None:
    result = await db.execute(
        select(Session)
        .where(Session.slug == slug)
        .options(selectinload(Session.members).selectinload(SessionMember.user))
    )
    return result.scalar_one_or_none()


async def list_sessions_for_user(db: AsyncSession, user_id: str) -> list[Session]:
    result = await db.execute(
        select(Session)
        .join(SessionMember, SessionMember.session_id == Session.id)
        .where(SessionMember.user_id == user_id)
        .order_by(Session.updated_at.desc())
    )
    return list(result.scalars().all())


async def update_session(db: AsyncSession, session: Session, data: SessionUpdate) -> Session:
    if data.title is not None:
        session.title = data.title
    if data.language is not None:
        session.language = data.language
    if data.content is not None:
        session.content = data.content
    if data.is_public is not None:
        session.is_public = data.is_public
    await db.commit()
    await db.refresh(session)
    return session


async def delete_session(db: AsyncSession, session: Session) -> None:
    await db.delete(session)
    await db.commit()


async def join_session(db: AsyncSession, session: Session, user_id: str) -> SessionMember | None:
    """Add user as editor if not already a member. Returns None if already joined."""
    exists = await db.execute(
        select(SessionMember).where(
            SessionMember.session_id == session.id,
            SessionMember.user_id == user_id,
        )
    )
    if exists.scalar_one_or_none():
        return None
    member = SessionMember(session_id=session.id, user_id=user_id, role="editor")
    db.add(member)
    await db.commit()
    return member
