from app.ws.yjs_utils import (
    MSG_AWARENESS,
    MSG_SYNC,
    SYNC_STEP1,
    SYNC_STEP2,
    SYNC_UPDATE,
    encode_sync_step1,
    encode_sync_step2,
    encode_sync_update,
    parse_message,
    read_var_uint,
    write_var_uint,
)


def test_var_uint_round_trip():
    for n in [0, 1, 127, 128, 255, 1000, 0xFFFF]:
        encoded = write_var_uint(n)
        decoded, pos = read_var_uint(encoded, 0)
        assert decoded == n
        assert pos == len(encoded)


def test_sync_step1_round_trips():
    sv = b"\x01\x02\x03"
    msg = encode_sync_step1(sv)
    mt, st, payload = parse_message(msg)
    assert mt == MSG_SYNC
    assert st == SYNC_STEP1
    assert payload == sv


def test_sync_step2_round_trips():
    update = b"\xde\xad\xbe\xef"
    msg = encode_sync_step2(update)
    mt, st, payload = parse_message(msg)
    assert mt == MSG_SYNC
    assert st == SYNC_STEP2
    assert payload == update


def test_sync_update_round_trips():
    update = bytes(range(32))
    msg = encode_sync_update(update)
    mt, st, payload = parse_message(msg)
    assert mt == MSG_SYNC
    assert st == SYNC_UPDATE
    assert payload == update


def test_empty_payload():
    msg = encode_sync_step2(b"")
    mt, st, payload = parse_message(msg)
    assert mt == MSG_SYNC
    assert st == SYNC_STEP2
    assert payload == b""


def test_parse_invalid_returns_minus_one():
    mt, st, _ = parse_message(b"")
    assert mt == -1
    mt, st, _ = parse_message(b"\xff")
    assert mt == -1
