from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import (
    AccessTokenResponse,
    LoginRequest,
    RefreshRequest,
    TokenResponse,
)
from app.schemas.user import UserCreate, UserRead
from app.services.security import create_access_token, verify_password
from app.services.token_service import (
    create_refresh_token,
    revoke_refresh_token,
    rotate_refresh_token,
)
from app.services.user_service import (
    create_user,
    get_user_by_email,
    get_user_by_username,
    get_user_by_username_or_email,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(data: UserCreate, db: AsyncSession = Depends(get_db)):
    if await get_user_by_username(db, data.username):
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Username already taken")
    if await get_user_by_email(db, data.email):
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Email already registered")

    user = await create_user(db, data)
    access_token = create_access_token(user.id)
    refresh_token = await create_refresh_token(db, user.id)
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserRead.model_validate(user),
    )


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await get_user_by_username_or_email(db, data.username_or_email)
    if user is None or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Account disabled")

    access_token = create_access_token(user.id)
    refresh_token = await create_refresh_token(db, user.id)
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserRead.model_validate(user),
    )


@router.post("/refresh", response_model=AccessTokenResponse)
async def refresh(data: RefreshRequest, db: AsyncSession = Depends(get_db)):
    result = await rotate_refresh_token(db, data.refresh_token)
    if result is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")
    new_refresh_raw, user_id = result
    access_token = create_access_token(user_id)
    # Return the new refresh token in a custom header so clients can store it
    from fastapi.responses import JSONResponse
    return JSONResponse(
        content={"access_token": access_token, "token_type": "bearer", "refresh_token": new_refresh_raw}
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(data: RefreshRequest, db: AsyncSession = Depends(get_db)):
    await revoke_refresh_token(db, data.refresh_token)


@router.get("/me", response_model=UserRead)
async def me(current_user: User = Depends(get_current_user)):
    return UserRead.model_validate(current_user)
