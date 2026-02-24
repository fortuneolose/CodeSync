from __future__ import annotations

import pytest
from httpx import AsyncClient

REG = "/api/auth/register"
SESSIONS = "/api/sessions"

USER_A = {"username": "alice123", "email": "alice@x.com", "password": "pass1234"}
USER_B = {"username": "bobby123", "email": "bobby@x.com", "password": "pass1234"}


async def auth_header(client: AsyncClient, user: dict) -> dict[str, str]:
    r = await client.post(REG, json=user)
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_create_session(client: AsyncClient):
    hdrs = await auth_header(client, USER_A)
    r = await client.post(SESSIONS, json={"title": "My Session", "language": "python"}, headers=hdrs)
    assert r.status_code == 201
    body = r.json()
    assert body["title"] == "My Session"
    assert body["language"] == "python"
    assert "slug" in body


@pytest.mark.asyncio
async def test_list_sessions(client: AsyncClient):
    hdrs = await auth_header(client, USER_A)
    await client.post(SESSIONS, json={"title": "S1"}, headers=hdrs)
    await client.post(SESSIONS, json={"title": "S2"}, headers=hdrs)
    r = await client.get(SESSIONS, headers=hdrs)
    assert r.status_code == 200
    assert len(r.json()) == 2


@pytest.mark.asyncio
async def test_get_session_by_slug(client: AsyncClient):
    hdrs = await auth_header(client, USER_A)
    created = (await client.post(SESSIONS, json={"title": "T"}, headers=hdrs)).json()
    r = await client.get(f"{SESSIONS}/{created['slug']}", headers=hdrs)
    assert r.status_code == 200
    assert r.json()["slug"] == created["slug"]
    assert len(r.json()["members"]) == 1


@pytest.mark.asyncio
async def test_update_session(client: AsyncClient):
    hdrs = await auth_header(client, USER_A)
    slug = (await client.post(SESSIONS, json={"title": "Old"}, headers=hdrs)).json()["slug"]
    r = await client.patch(f"{SESSIONS}/{slug}", json={"title": "New", "language": "go"}, headers=hdrs)
    assert r.status_code == 200
    assert r.json()["title"] == "New"
    assert r.json()["language"] == "go"


@pytest.mark.asyncio
async def test_delete_session(client: AsyncClient):
    hdrs = await auth_header(client, USER_A)
    slug = (await client.post(SESSIONS, json={"title": "Del"}, headers=hdrs)).json()["slug"]
    r = await client.delete(f"{SESSIONS}/{slug}", headers=hdrs)
    assert r.status_code == 204
    r2 = await client.get(f"{SESSIONS}/{slug}", headers=hdrs)
    assert r2.status_code == 404


@pytest.mark.asyncio
async def test_non_owner_cannot_update(client: AsyncClient):
    hdrs_a = await auth_header(client, USER_A)
    hdrs_b = await auth_header(client, USER_B)
    slug = (await client.post(SESSIONS, json={"title": "A's", "is_public": True}, headers=hdrs_a)).json()["slug"]
    r = await client.patch(f"{SESSIONS}/{slug}", json={"title": "Hacked"}, headers=hdrs_b)
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_join_public_session(client: AsyncClient):
    hdrs_a = await auth_header(client, USER_A)
    hdrs_b = await auth_header(client, USER_B)
    slug = (await client.post(SESSIONS, json={"title": "Public", "is_public": True}, headers=hdrs_a)).json()["slug"]
    r = await client.post(f"{SESSIONS}/{slug}/join", headers=hdrs_b)
    assert r.status_code == 200
    details = (await client.get(f"{SESSIONS}/{slug}", headers=hdrs_b)).json()
    assert len(details["members"]) == 2


@pytest.mark.asyncio
async def test_join_private_session_denied(client: AsyncClient):
    hdrs_a = await auth_header(client, USER_A)
    hdrs_b = await auth_header(client, USER_B)
    slug = (await client.post(SESSIONS, json={"title": "Private", "is_public": False}, headers=hdrs_a)).json()["slug"]
    r = await client.post(f"{SESSIONS}/{slug}/join", headers=hdrs_b)
    assert r.status_code == 403
