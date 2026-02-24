from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import RefreshToken
from app.services.security import (
    generate_refresh_token,
    hash_refresh_token,
    refresh_token_expiry,
)


async def create_refresh_token(db: AsyncSession, user_id: str) -> str:
    raw = generate_refresh_token()
    token = RefreshToken(
        user_id=user_id,
        token_hash=hash_refresh_token(raw),
        expires_at=refresh_token_expiry(),
    )
    db.add(token)
    await db.commit()
    return raw


async def rotate_refresh_token(db: AsyncSession, raw_token: str) -> tuple[str, str] | None:
    """Validate old token, revoke it, and issue a new pair.
    Returns (new_raw_token, user_id) or None if invalid/expired/revoked.
    """
    token_hash = hash_refresh_token(raw_token)
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    record = result.scalar_one_or_none()

    if record is None:
        return None
    if record.revoked:
        return None
    # SQLite stores naive datetimes; normalise both sides for comparison
    expires = record.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    if expires < datetime.now(timezone.utc):
        return None

    # Revoke old token
    record.revoked = True
    await db.flush()

    # Issue new token
    new_raw = generate_refresh_token()
    new_record = RefreshToken(
        user_id=record.user_id,
        token_hash=hash_refresh_token(new_raw),
        expires_at=refresh_token_expiry(),
    )
    db.add(new_record)
    await db.commit()
    return new_raw, record.user_id


async def revoke_refresh_token(db: AsyncSession, raw_token: str) -> bool:
    token_hash = hash_refresh_token(raw_token)
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    record = result.scalar_one_or_none()
    if record is None or record.revoked:
        return False
    record.revoked = True
    await db.commit()
    return True
