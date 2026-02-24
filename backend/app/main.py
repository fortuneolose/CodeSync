from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.session import engine
from app.db.base import Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup (migrations via Alembic in production)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title="CodeSync API",
    description="Real-time collaborative code editor backend",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
from app.api.routes import health  # noqa: E402
from app.api.routes import auth    # noqa: E402

app.include_router(health.router, prefix="/api")
app.include_router(auth.router,   prefix="/api")


@app.get("/")
async def root():
    return {"service": "codesync-api", "version": "0.1.0"}
