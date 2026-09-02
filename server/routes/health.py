"""Health & System Status Endpoint."""
from datetime import datetime, timezone
from fastapi import APIRouter
from server.config import settings
from server.services.scorecard import scorecard_service

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
async def get_health():
    """Check health and connectivity of database, Scorecard cache, AI pipeline, and knowledge ledger."""
    db_ok = False
    colleges_count = 0
    try:
        _, count = await scorecard_service.search_colleges(page=1, page_size=1)
        colleges_count = count
        db_ok = True
    except Exception:
        db_ok = False

    gemini_ready = bool(settings.GEMINI_API_KEY and not settings.GEMINI_API_KEY.startswith("your_"))
    scorecard_ready = bool(settings.COLLEGE_SCORECARD_API_KEY)
    ledger_ok = settings.LEDGER_MD_PATH.exists() and settings.LEDGER_JSONL_PATH.exists()

    db_info = {
        "status": "connected" if db_ok else "error",
        "indexed_colleges": colleges_count,
        "path": str(settings.DATABASE_PATH),
    }

    scorecard_info = {
        "status": "live" if scorecard_ready else "seed_fallback_mode",
        "key_configured": scorecard_ready,
    }

    gemini_info = {
        "status": "live" if gemini_ready else "preview_mode",
        "key_configured": gemini_ready,
    }

    ledger_info = {
        "status": "active" if ledger_ok else "initializing",
        "markdown_path": str(settings.LEDGER_MD_PATH),
        "jsonl_path": str(settings.LEDGER_JSONL_PATH),
    }

    return {
        "status": "healthy" if db_ok else "degraded",
        "database": db_info,
        "db": db_info,
        "scorecard": scorecard_info,
        "scorecard_api": scorecard_info,
        "gemini": gemini_info,
        "ai": gemini_info,
        "gemini_api": gemini_info,
        "ledger": ledger_info,
        "knowledge": ledger_info,
        "knowledge_ledger": ledger_info,
        "services": {
            "database": db_info,
            "scorecard": scorecard_info,
            "gemini": gemini_info,
            "ai": gemini_info,
            "ledger": ledger_info,
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
