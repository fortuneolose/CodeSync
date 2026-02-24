from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


SUPPORTED_LANGUAGES = [
    "python", "javascript", "typescript", "java", "cpp", "c",
    "go", "rust", "html", "css", "json", "markdown", "plaintext",
]


class SessionCreate(BaseModel):
    title: str = Field("Untitled", min_length=1, max_length=120)
    language: str = Field("python")
    is_public: bool = False

    def model_post_init(self, __context):
        if self.language not in SUPPORTED_LANGUAGES:
            self.language = "plaintext"


class SessionUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=120)
    language: str | None = None
    content: str | None = None
    is_public: bool | None = None


class SessionMemberRead(BaseModel):
    user_id: str
    username: str
    role: str
    joined_at: datetime

    model_config = {"from_attributes": True}


class SessionRead(BaseModel):
    id: str
    slug: str
    title: str
    language: str
    content: str
    is_public: bool
    owner_id: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SessionReadWithMembers(SessionRead):
    members: list[SessionMemberRead] = []
