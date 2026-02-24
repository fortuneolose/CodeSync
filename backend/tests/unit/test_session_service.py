import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.session import SessionCreate, SessionUpdate
from app.schemas.user import UserCreate
from app.services.user_service import create_user
from app.services.session_service import (
    create_session,
    delete_session,
    get_session_by_slug,
    list_sessions_for_user,
    update_session,
)


@pytest.mark.asyncio
async def test_create_session_generates_slug(db_session: AsyncSession):
    user = await create_user(db_session, UserCreate(username="slgtest", email="slg@x.com", password="pass1234"))
    sess = await create_session(db_session, SessionCreate(title="My Session"), owner_id=user.id)
    assert len(sess.slug) >= 8
    assert sess.owner_id == user.id
    assert len(sess.members) == 1
    assert sess.members[0].role == "owner"


@pytest.mark.asyncio
async def test_get_by_slug(db_session: AsyncSession):
    user = await create_user(db_session, UserCreate(username="sluglkp", email="sl@x.com", password="pass1234"))
    sess = await create_session(db_session, SessionCreate(title="T"), owner_id=user.id)
    found = await get_session_by_slug(db_session, sess.slug)
    assert found is not None
    assert found.id == sess.id


@pytest.mark.asyncio
async def test_list_sessions_for_user(db_session: AsyncSession):
    user = await create_user(db_session, UserCreate(username="lister", email="lst@x.com", password="pass1234"))
    await create_session(db_session, SessionCreate(title="A"), owner_id=user.id)
    await create_session(db_session, SessionCreate(title="B"), owner_id=user.id)
    sessions = await list_sessions_for_user(db_session, user.id)
    assert len(sessions) == 2


@pytest.mark.asyncio
async def test_update_session_fields(db_session: AsyncSession):
    user = await create_user(db_session, UserCreate(username="updater", email="upd@x.com", password="pass1234"))
    sess = await create_session(db_session, SessionCreate(title="Old"), owner_id=user.id)
    updated = await update_session(db_session, sess, SessionUpdate(title="New", language="typescript"))
    assert updated.title == "New"
    assert updated.language == "typescript"


@pytest.mark.asyncio
async def test_delete_session(db_session: AsyncSession):
    user = await create_user(db_session, UserCreate(username="deleter", email="del@x.com", password="pass1234"))
    sess = await create_session(db_session, SessionCreate(title="Del"), owner_id=user.id)
    await delete_session(db_session, sess)
    assert await get_session_by_slug(db_session, sess.slug) is None
