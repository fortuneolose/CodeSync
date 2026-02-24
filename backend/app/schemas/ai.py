from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ExplainRequest(BaseModel):
    slug: str
    code: str = Field(..., max_length=16_000)
    language: str = "plaintext"


class RefactorRequest(BaseModel):
    slug: str
    code: str = Field(..., max_length=16_000)
    language: str = "plaintext"


class ChatRequest(BaseModel):
    slug: str
    code: str = Field("", max_length=16_000)
    language: str = "plaintext"
    message: str = Field(..., max_length=2_000)
    history: list[ChatMessage] = Field(default_factory=list, max_length=20)
