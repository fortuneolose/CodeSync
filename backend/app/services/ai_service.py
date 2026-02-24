"""
Pluggable AI service.

Uses OpenAI when OPENAI_API_KEY is set; falls back to a deterministic stub
so the app is fully functional without an API key.
"""
from __future__ import annotations

import json
from typing import AsyncIterator

from app.core.config import settings


# ── System prompts ─────────────────────────────────────────────────────────

def _explain_prompt(language: str) -> str:
    return (
        f"You are an expert {language} engineer and educator. "
        "Explain the provided code clearly and concisely. "
        "Use plain English, mention key concepts, and call out any gotchas."
    )


def _refactor_prompt(language: str) -> str:
    return (
        f"You are an expert {language} engineer focused on code quality. "
        "Suggest concrete improvements to the code: better names, reduced complexity, "
        "idiomatic patterns, and performance wins where applicable. "
        "Show the refactored code first, then a brief rationale."
    )


def _chat_system_prompt(language: str, code: str) -> str:
    context = f"\n\nCurrent editor content ({language}):\n```{language}\n{code[:4000]}\n```" if code.strip() else ""
    return (
        f"You are an expert programming assistant specialising in {language}. "
        "Answer questions about the user's code clearly and concisely."
        f"{context}"
    )


# ── Streaming helpers ───────────────────────────────────────────────────────

def _sse(content: str) -> str:
    return f"data: {json.dumps({'content': content})}\n\n"


_SSE_DONE = "data: [DONE]\n\n"


async def _stub_stream(text: str) -> AsyncIterator[str]:
    """Word-by-word fake stream so the UI looks identical with or without a key."""
    for word in text.split(" "):
        yield _sse(word + " ")
    yield _SSE_DONE


async def _openai_stream(messages: list[dict]) -> AsyncIterator[str]:
    from openai import AsyncOpenAI
    client = AsyncOpenAI(api_key=settings.openai_api_key)
    stream = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        stream=True,
        max_tokens=1024,
        temperature=0.3,
    )
    async for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield _sse(delta)
    yield _SSE_DONE


def _has_key() -> bool:
    return bool(settings.openai_api_key and not settings.openai_api_key.startswith("sk-..."))


# ── Public API ──────────────────────────────────────────────────────────────

async def explain_stream(code: str, language: str) -> AsyncIterator[str]:
    if not _has_key():
        stub = (
            f"[AI stub — set OPENAI_API_KEY to enable]\n\n"
            f"This {language} code snippet contains {len(code.splitlines())} lines. "
            "It appears to define logic that processes data. "
            "Add your OpenAI key to get a real explanation."
        )
        async for chunk in _stub_stream(stub):
            yield chunk
        return

    messages = [
        {"role": "system", "content": _explain_prompt(language)},
        {"role": "user", "content": f"```{language}\n{code}\n```"},
    ]
    async for chunk in _openai_stream(messages):
        yield chunk


async def refactor_stream(code: str, language: str) -> AsyncIterator[str]:
    if not _has_key():
        stub = (
            f"[AI stub — set OPENAI_API_KEY to enable]\n\n"
            f"Suggested refactoring for your {language} code:\n\n"
            f"```{language}\n# Your refactored code would appear here\n{code}\n```\n\n"
            "Add your OpenAI key to get real refactoring suggestions."
        )
        async for chunk in _stub_stream(stub):
            yield chunk
        return

    messages = [
        {"role": "system", "content": _refactor_prompt(language)},
        {"role": "user", "content": f"```{language}\n{code}\n```"},
    ]
    async for chunk in _openai_stream(messages):
        yield chunk


async def chat_stream(
    code: str,
    language: str,
    message: str,
    history: list[dict],
) -> AsyncIterator[str]:
    if not _has_key():
        stub = (
            f"[AI stub] You asked: \"{message}\"\n\n"
            "This is a placeholder response. "
            "Set OPENAI_API_KEY in backend/.env to enable real AI chat."
        )
        async for chunk in _stub_stream(stub):
            yield chunk
        return

    messages = [{"role": "system", "content": _chat_system_prompt(language, code)}]
    for h in history[-10:]:  # keep last 10 exchanges
        messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": message})

    async for chunk in _openai_stream(messages):
        yield chunk
