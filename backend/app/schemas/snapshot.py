from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field


class SnapshotCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=120)
    content: str
    language: str = "plaintext"


class SnapshotRead(BaseModel):
    id: str
    session_id: str
    title: str
    content: str
    language: str
    created_by: str | None
    created_at: datetime
    author_username: str | None = None

    model_config = {"from_attributes": True}


class RestoreResponse(BaseModel):
    content: str
    language: str
    snapshot_id: str
