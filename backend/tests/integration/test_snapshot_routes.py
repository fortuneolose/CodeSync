from __future__ import annotations

import pytest
from httpx import AsyncClient

REG = "/api/auth/register"
SESSIONS = "/api/sessions"

USER = {"username": "snapuser", "email": "snap@x.com", "password": "pass1234"}
USER_B = {"username": "snapuser2", "email": "snap2@x.com", "password": "pass1234"}


async def auth(client: AsyncClient, user: dict) -> dict:
    r = await client.post(REG, json=user)
    d = r.json()
    return {"Authorization": f"Bearer {d['access_token']}"}


async def make_session(client: AsyncClient, hdrs: dict) -> str:
    r = await client.post(SESSIONS, json={"title": "S"}, headers=hdrs)
    return r.json()["slug"]


@pytest.mark.asyncio
async def test_create_and_list_snapshot(client: AsyncClient):
    hdrs = await auth(client, USER)
    slug = await make_session(client, hdrs)

    r = await client.post(
        f"/api/sessions/{slug}/snapshots",
        json={"title": "v1", "content": "print(1)", "language": "python"},
        headers=hdrs,
    )
    assert r.status_code == 201
    snap = r.json()
    assert snap["title"] == "v1"
    assert snap["author_username"] == "snapuser"

    r2 = await client.get(f"/api/sessions/{slug}/snapshots", headers=hdrs)
    assert r2.status_code == 200
    assert len(r2.json()) == 1


@pytest.mark.asyncio
async def test_restore_snapshot(client: AsyncClient):
    hdrs = await auth(client, USER)
    slug = await make_session(client, hdrs)

    snap_id = (await client.post(
        f"/api/sessions/{slug}/snapshots",
        json={"title": "v1", "content": "original", "language": "python"},
        headers=hdrs,
    )).json()["id"]

    r = await client.post(f"/api/sessions/{slug}/snapshots/{snap_id}/restore", headers=hdrs)
    assert r.status_code == 200
    assert r.json()["content"] == "original"
    assert r.json()["snapshot_id"] == snap_id


@pytest.mark.asyncio
async def test_non_owner_cannot_restore(client: AsyncClient):
    hdrs_a = await auth(client, USER)
    hdrs_b = await auth(client, USER_B)
    slug = (await client.post(
        SESSIONS,
        json={"title": "A", "is_public": True},
        headers=hdrs_a,
    )).json()["slug"]
    await client.post(f"{SESSIONS}/{slug}/join", headers=hdrs_b)

    snap_id = (await client.post(
        f"/api/sessions/{slug}/snapshots",
        json={"title": "v1", "content": "x", "language": "python"},
        headers=hdrs_a,
    )).json()["id"]

    r = await client.post(
        f"/api/sessions/{slug}/snapshots/{snap_id}/restore", headers=hdrs_b
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_delete_snapshot(client: AsyncClient):
    hdrs = await auth(client, USER)
    slug = await make_session(client, hdrs)

    snap_id = (await client.post(
        f"/api/sessions/{slug}/snapshots",
        json={"title": "del", "content": "x", "language": "python"},
        headers=hdrs,
    )).json()["id"]

    r = await client.delete(f"/api/sessions/{slug}/snapshots/{snap_id}", headers=hdrs)
    assert r.status_code == 204
    r2 = await client.get(f"/api/sessions/{slug}/snapshots", headers=hdrs)
    assert r2.json() == []
