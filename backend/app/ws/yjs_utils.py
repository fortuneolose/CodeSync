"""
Minimal y-websocket binary protocol helpers.

Message format (lib0 encoding):
  [msgType:varuint][...payload]

Sync messages (msgType = 0):
  [0][syncType:varuint][dataLen:varuint][...data]
  syncType 0 = SYNC_STEP1  (client sends its state vector)
  syncType 1 = SYNC_STEP2  (server sends full update)
  syncType 2 = SYNC_UPDATE (incremental update)

Awareness messages (msgType = 1):
  [1][dataLen:varuint][...data]
"""

from __future__ import annotations

MSG_SYNC = 0
MSG_AWARENESS = 1

SYNC_STEP1 = 0
SYNC_STEP2 = 1
SYNC_UPDATE = 2


# ── Variable-length uint (lib0 encoding) ───────────────────────────────────

def write_var_uint(n: int) -> bytes:
    buf = []
    while n > 0x7F:
        buf.append((n & 0x7F) | 0x80)
        n >>= 7
    buf.append(n & 0x7F)
    return bytes(buf)


def read_var_uint(data: bytes, pos: int) -> tuple[int, int]:
    num, shift = 0, 0
    while pos < len(data):
        b = data[pos]; pos += 1
        num |= (b & 0x7F) << shift
        if not (b & 0x80):
            break
        shift += 7
    return num, pos


# ── Message builders ───────────────────────────────────────────────────────

def _sync_msg(sync_type: int, payload: bytes) -> bytes:
    return bytes([MSG_SYNC]) + write_var_uint(sync_type) + write_var_uint(len(payload)) + payload


def encode_sync_step1(state_vector: bytes = b"\x00") -> bytes:
    return _sync_msg(SYNC_STEP1, state_vector)


def encode_sync_step2(update: bytes) -> bytes:
    return _sync_msg(SYNC_STEP2, update)


def encode_sync_update(update: bytes) -> bytes:
    return _sync_msg(SYNC_UPDATE, update)


# ── Message parser ─────────────────────────────────────────────────────────

def parse_message(data: bytes) -> tuple[int, int, bytes]:
    """Return (msg_type, sync_sub_type, payload).

    For MSG_AWARENESS, sync_sub_type is 0 (unused).
    Returns (-1, -1, b"") on parse failure.
    """
    if len(data) < 2:
        return -1, -1, b""
    pos = 0
    msg_type, pos = read_var_uint(data, pos)

    if msg_type == MSG_SYNC:
        sync_type, pos = read_var_uint(data, pos)
        data_len, pos = read_var_uint(data, pos)
        payload = data[pos: pos + data_len]
        return msg_type, sync_type, payload

    if msg_type == MSG_AWARENESS:
        data_len, pos = read_var_uint(data, pos)
        payload = data[pos: pos + data_len]
        return msg_type, 0, payload

    return msg_type, 0, data[1:]
