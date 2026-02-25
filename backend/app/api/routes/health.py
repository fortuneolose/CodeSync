import httpx
from fastapi import APIRouter
from app.services.ai_service import _API_KEY, _has_key

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    return {"status": "ok"}


@router.get("/health/ai")
async def ai_diagnostic():
    """Diagnose OpenAI connectivity without going through the full AI pipeline."""
    result = {
        "key_configured": _has_key(),
        "key_prefix": _API_KEY[:10] + "..." if _API_KEY else "(not set)",
    }
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                "https://api.openai.com/v1/models",
                headers={"Authorization": f"Bearer {_API_KEY}"},
            )
            result["http_status"] = resp.status_code
            result["reachable"] = True
    except httpx.ConnectError as e:
        result["reachable"] = False
        result["error_type"] = "ConnectError"
        result["error"] = str(e)
    except httpx.TimeoutException as e:
        result["reachable"] = False
        result["error_type"] = "Timeout"
        result["error"] = str(e)
    except Exception as e:
        result["reachable"] = False
        result["error_type"] = type(e).__name__
        result["error"] = str(e)
    return result
