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
import os
from collections import defaultdict

import redis.asyncio as aioredis
from fastapi import WebSocket

from app.core.config import settings

# Unique ID for this process/instance so we can skip our own pub/sub messages.
_INSTANCE_ID = os.urandom(8).hex().encode()
_SEP = b"|"  # separates instance-id prefix from payload in Redis messages

_VALID_REDIS_SCHEMES = ("redis://", "rediss://", "unix://")


def _redis_configured() -> bool:
    return any(settings.redis_url.startswith(s) for s in _VALID_REDIS_SCHEMES)


def _channel(slug: str) -> str:
    return f"session:{slug}:channel"


class ConnectionManager:
    def __init__(self) -> None:
        # slug -> {ws: user_id}
        self._connections: dict[str, dict[WebSocket, str]] = defaultdict(dict)
        self._lock = asyncio.Lock()
        self._redis: aioredis.Redis | None = None
        # In-memory fallback when Redis is not configured
        self._mem: dict[str, list[bytes]] = defaultdict(list)
        # slug -> asyncio.Task running the pub/sub listener
        self._pubsub_tasks: dict[str, asyncio.Task] = {}

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

    # ── Redis pub/sub listener ─────────────────────────────────────────────

    async def _pubsub_listener(self, slug: str) -> None:
        """Subscribe to the Redis channel for this session and forward any
        messages published by *other* backend instances to our local sockets."""
        r = await self._r()
        if r is None:
            return
        pubsub = r.pubsub()
        await pubsub.subscribe(_channel(slug))
        try:
            async for message in pubsub.listen():
                if message["type"] != "message":
                    continue
                raw: bytes = message["data"]
                # Strip the instance-id prefix; skip messages from ourselves
                if _SEP not in raw:
                    continue
                sender_id, data = raw.split(_SEP, 1)
                if sender_id == _INSTANCE_ID:
                    continue
                # Deliver to all local connections for this slug
                dead: list[WebSocket] = []
                for ws in list(self._connections[slug]):
                    try:
                        await ws.send_bytes(data)
                    except Exception:
                        dead.append(ws)
                async with self._lock:
                    for ws in dead:
                        self._connections[slug].pop(ws, None)
        except asyncio.CancelledError:
            pass
        finally:
            await pubsub.unsubscribe(_channel(slug))
            await pubsub.aclose()

    async def _ensure_pubsub(self, slug: str) -> None:
        """Start a pub/sub listener task for the slug if one isn't running."""
        r = await self._r()
        if r is None:
            return
        task = self._pubsub_tasks.get(slug)
        if task is None or task.done():
            self._pubsub_tasks[slug] = asyncio.ensure_future(
                self._pubsub_listener(slug)
            )

    async def _maybe_cancel_pubsub(self, slug: str) -> None:
        """Cancel the pub/sub listener when the last client for a slug leaves."""
        if self._connections[slug]:
            return
        task = self._pubsub_tasks.pop(slug, None)
        if task and not task.done():
            task.cancel()

    # ── Connection lifecycle ───────────────────────────────────────────────

    async def connect(self, slug: str, ws: WebSocket, user_id: str) -> None:
        await ws.accept()
        async with self._lock:
            self._connections[slug][ws] = user_id
        await self._ensure_pubsub(slug)

    async def disconnect(self, slug: str, ws: WebSocket) -> None:
        async with self._lock:
            self._connections[slug].pop(ws, None)
        await self._maybe_cancel_pubsub(slug)

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
        # Deliver to local connections on this instance
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

        # Publish to Redis so other backend instances forward it to their clients.
        # Prefix with our instance ID so the listener skips our own messages.
        r = await self._r()
        if r is not None:
            try:
                await r.publish(_channel(slug), _INSTANCE_ID + _SEP + data)
            except Exception:
                pass

    async def send(self, ws: WebSocket, data: bytes) -> None:
        try:
            await ws.send_bytes(data)
        except Exception:
            pass


manager = ConnectionManager()
