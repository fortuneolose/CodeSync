"""
WebSocket connection registry with Redis-backed persistence and pub/sub.

Each collaborative session is identified by its slug.

Storage layout in Redis:
  session:{slug}:updates   — RPUSH list of raw binary Yjs update payloads
  session:{slug}:channel   — pub/sub channel name for cross-instance fanout

Awareness (cursor positions, online users) is ephemeral:
  it is broadcast to local connections only and never persisted.
"""
from __future__ import annotations

import asyncio
from collections import defaultdict

import redis.asyncio as aioredis
from fastapi import WebSocket

from app.core.config import settings

_VALID_REDIS_SCHEMES = ("redis://", "rediss://", "unix://")


def _redis_configured() -> bool:
    return any(settings.redis_url.startswith(s) for s in _VALID_REDIS_SCHEMES)


class ConnectionManager:
    def __init__(self) -> None:
        # slug -> {ws: user_id}
        self._connections: dict[str, dict[WebSocket, str]] = defaultdict(dict)
        self._lock = asyncio.Lock()
        self._redis: aioredis.Redis | None = None
        # In-memory fallback when Redis is not configured
        self._mem: dict[str, list[bytes]] = defaultdict(list)

    # ── Redis (with in-memory fallback) ────────────────────────────────────

    async def _r(self) -> aioredis.Redis | None:
        if not _redis_configured():
            return None
        if self._redis is None:
            self._redis = aioredis.from_url(settings.redis_url, decode_responses=False)
        return self._redis

    async def get_stored_updates(self, slug: str) -> list[bytes]:
        r = await self._r()
        if r is None:
            return list(self._mem[slug])
        return await r.lrange(f"session:{slug}:updates", 0, -1)

    async def store_update(self, slug: str, update: bytes) -> None:
        r = await self._r()
        if r is None:
            self._mem[slug].append(update)
            return
        await r.rpush(f"session:{slug}:updates", update)

    async def clear_updates(self, slug: str) -> None:
        r = await self._r()
        if r is None:
            self._mem.pop(slug, None)
            return
        await r.delete(f"session:{slug}:updates")

    # ── Connection lifecycle ───────────────────────────────────────────────

    async def connect(self, slug: str, ws: WebSocket, user_id: str) -> None:
        await ws.accept()
        async with self._lock:
            self._connections[slug][ws] = user_id

    async def disconnect(self, slug: str, ws: WebSocket) -> None:
        async with self._lock:
            self._connections[slug].pop(ws, None)

    def peer_count(self, slug: str) -> int:
        return len(self._connections[slug])

    def connected_user_ids(self, slug: str) -> list[str]:
        return list(self._connections[slug].values())

    # ── Broadcast helpers ──────────────────────────────────────────────────

    async def broadcast(
        self,
        slug: str,
        data: bytes,
        exclude: WebSocket | None = None,
    ) -> None:
        dead: list[WebSocket] = []
        for ws in list(self._connections[slug]):
            if ws is exclude:
                continue
            try:
                await ws.send_bytes(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self._connections[slug].pop(ws, None)

    async def send(self, ws: WebSocket, data: bytes) -> None:
        try:
            await ws.send_bytes(data)
        except Exception:
            pass


manager = ConnectionManager()
