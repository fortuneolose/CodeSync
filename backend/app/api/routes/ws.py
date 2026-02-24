from __future__ import annotations

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from jose import JWTError

from app.services.security import decode_access_token
from app.ws.handler import handle_session_ws

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/{slug}")
async def ws_endpoint(
    slug: str,
    websocket: WebSocket,
    token: str = Query(..., description="JWT access token"),
) -> None:
    # Authenticate via query param (browsers cannot set WS headers)
    try:
        payload = decode_access_token(token)
        user_id: str | None = payload.get("sub")
        if not user_id:
            await websocket.close(code=4001)
            return
    except JWTError:
        await websocket.close(code=4001)
        return

    await handle_session_ws(slug, websocket, user_id)
