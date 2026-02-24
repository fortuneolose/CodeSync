"""
y-websocket protocol handler for a collaborative editing session.

Protocol summary
────────────────
1. Client connects  → server replays all stored Yjs updates as SYNC_STEP2 messages,
   then sends an empty SYNC_STEP1 to invite the client to share anything it has.
2. SYNC_STEP1 received from client (with its state vector)
   → server sends all stored updates again as SYNC_STEP2 (safe: Yjs is idempotent).
3. SYNC_STEP2 / SYNC_UPDATE received from client
   → store payload, broadcast as SYNC_UPDATE to all other clients in session.
4. MSG_AWARENESS received
   → broadcast to all other clients (ephemeral, not stored).
"""
from __future__ import annotations

from fastapi import WebSocket, WebSocketDisconnect

from .connection_manager import manager
from .yjs_utils import (
    MSG_AWARENESS,
    MSG_SYNC,
    SYNC_STEP1,
    SYNC_STEP2,
    SYNC_UPDATE,
    encode_sync_step1,
    encode_sync_step2,
    encode_sync_update,
    parse_message,
)


async def handle_session_ws(slug: str, ws: WebSocket, user_id: str) -> None:
    await manager.connect(slug, ws, user_id)
    try:
        # ── Initial sync: replay all stored updates to the new client ──────
        stored = await manager.get_stored_updates(slug)
        for raw_update in stored:
            await manager.send(ws, encode_sync_step2(raw_update))

        # Invite the client to share anything it has that we might be missing
        await manager.send(ws, encode_sync_step1())

        # ── Main message loop ──────────────────────────────────────────────
        while True:
            data: bytes = await ws.receive_bytes()
            msg_type, sync_type, payload = parse_message(data)

            if msg_type == MSG_SYNC:
                if sync_type == SYNC_STEP1:
                    # Client state vector received — replay all stored updates
                    stored = await manager.get_stored_updates(slug)
                    for raw_update in stored:
                        await manager.send(ws, encode_sync_step2(raw_update))

                elif sync_type in (SYNC_STEP2, SYNC_UPDATE):
                    # New Yjs update — persist it and fan out to peers
                    if payload:
                        await manager.store_update(slug, payload)
                        await manager.broadcast(slug, encode_sync_update(payload), exclude=ws)

            elif msg_type == MSG_AWARENESS:
                # Cursor positions / online users — relay only, never stored
                await manager.broadcast(slug, data, exclude=ws)

    except WebSocketDisconnect:
        pass
    finally:
        await manager.disconnect(slug, ws)
