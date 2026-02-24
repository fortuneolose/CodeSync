from __future__ import annotations

import pytest
from httpx import AsyncClient

REGISTER_URL = "/api/auth/register"
LOGIN_URL    = "/api/auth/login"
REFRESH_URL  = "/api/auth/refresh"
LOGOUT_URL   = "/api/auth/logout"
ME_URL       = "/api/auth/me"

USER = {"username": "testuser", "email": "test@example.com", "password": "password123"}

# Remove unused db fixture import



async def register(client: AsyncClient, **overrides):
    return await client.post(REGISTER_URL, json={**USER, **overrides})


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
    r = await register(client)
    assert r.status_code == 201
    body = r.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["user"]["username"] == "testuser"


@pytest.mark.asyncio
async def test_register_duplicate_username(client: AsyncClient):
    await register(client)
    r = await register(client, email="other@example.com")
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    await register(client)
    r = await register(client, username="other")
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_login_with_username(client: AsyncClient):
    await register(client)
    r = await client.post(LOGIN_URL, json={"username_or_email": "testuser", "password": "password123"})
    assert r.status_code == 200
    assert "access_token" in r.json()


@pytest.mark.asyncio
async def test_login_with_email(client: AsyncClient):
    await register(client)
    r = await client.post(LOGIN_URL, json={"username_or_email": "test@example.com", "password": "password123"})
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    await register(client)
    r = await client.post(LOGIN_URL, json={"username_or_email": "testuser", "password": "wrong"})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_me_authenticated(client: AsyncClient):
    reg = await register(client)
    token = reg.json()["access_token"]
    r = await client.get(ME_URL, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["username"] == "testuser"


@pytest.mark.asyncio
async def test_me_unauthenticated(client: AsyncClient):
    r = await client.get(ME_URL)
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_refresh_token_rotation(client: AsyncClient):
    reg = await register(client)
    old_refresh = reg.json()["refresh_token"]
    r = await client.post(REFRESH_URL, json={"refresh_token": old_refresh})
    assert r.status_code == 200
    body = r.json()
    assert "access_token" in body
    assert "refresh_token" in body
    # Old token must now be invalid
    r2 = await client.post(REFRESH_URL, json={"refresh_token": old_refresh})
    assert r2.status_code == 401


@pytest.mark.asyncio
async def test_logout_revokes_token(client: AsyncClient):
    reg = await register(client)
    refresh = reg.json()["refresh_token"]
    r = await client.post(LOGOUT_URL, json={"refresh_token": refresh})
    assert r.status_code == 204
    r2 = await client.post(REFRESH_URL, json={"refresh_token": refresh})
    assert r2.status_code == 401
