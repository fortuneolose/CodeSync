import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.user import UserCreate
from app.services.user_service import (
    create_user,
    get_user_by_email,
    get_user_by_id,
    get_user_by_username,
    get_user_by_username_or_email,
)

DATA = UserCreate(username="testusr", email="test@example.com", password="password1")


@pytest.mark.asyncio
async def test_create_user_persists(db_session: AsyncSession):
    user = await create_user(db_session, DATA)
    assert user.id is not None
    assert user.username == "testusr"
    assert user.hashed_password != "password1"


@pytest.mark.asyncio
async def test_get_by_username(db_session: AsyncSession):
    await create_user(db_session, DATA)
    found = await get_user_by_username(db_session, "testusr")
    assert found is not None
    assert found.email == "test@example.com"


@pytest.mark.asyncio
async def test_get_by_email(db_session: AsyncSession):
    await create_user(db_session, DATA)
    found = await get_user_by_email(db_session, "test@example.com")
    assert found is not None


@pytest.mark.asyncio
async def test_get_by_username_or_email_both_work(db_session: AsyncSession):
    user = await create_user(db_session, DATA)
    by_name = await get_user_by_username_or_email(db_session, "testusr")
    by_email = await get_user_by_username_or_email(db_session, "test@example.com")
    assert by_name.id == user.id
    assert by_email.id == user.id


@pytest.mark.asyncio
async def test_get_by_id_not_found(db_session: AsyncSession):
    result = await get_user_by_id(db_session, "nonexistent-id")
    assert result is None


@pytest.mark.asyncio
async def test_username_is_lowercased(db_session: AsyncSession):
    data = UserCreate(username="MixedCase", email="mc@x.com", password="pass1234")
    user = await create_user(db_session, data)
    assert user.username == "mixedcase"
