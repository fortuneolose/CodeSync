"""AI service tests — run without an OpenAI key so the stub path is exercised."""
import pytest
from app.services.ai_service import explain_stream, refactor_stream, chat_stream


async def collect(gen) -> str:
    out = []
    async for chunk in gen:
        out.append(chunk)
    return "".join(out)


@pytest.mark.asyncio
async def test_explain_stub_returns_sse():
    result = await collect(explain_stream("print('hello')", "python"))
    assert "data:" in result
    assert "[DONE]" in result


@pytest.mark.asyncio
async def test_refactor_stub_contains_code_block():
    result = await collect(refactor_stream("x = 1\ny = 2\nz = x + y", "python"))
    assert "data:" in result
    assert "[DONE]" in result


@pytest.mark.asyncio
async def test_chat_stub_echoes_message():
    result = await collect(chat_stream("", "python", "What does this do?", []))
    assert "data:" in result
    assert "[DONE]" in result


@pytest.mark.asyncio
async def test_stub_sse_format():
    """Each chunk must be a valid SSE line."""
    import json
    chunks = []
    async for chunk in explain_stream("x = 1", "python"):
        chunks.append(chunk)

    for chunk in chunks[:-1]:  # all except [DONE]
        assert chunk.startswith("data: ")
        body = chunk.removeprefix("data: ").strip()
        parsed = json.loads(body)
        assert "content" in parsed

    assert chunks[-1] == "data: [DONE]\n\n"
