"""Knowledge Ledger and Audit Endpoints."""
from fastapi import APIRouter, HTTPException, Query
from server.config import settings
from server.services.ledger import ledger_service
from server.services.scorecard import scorecard_service

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


@router.get("/colleges/{id}")
async def get_college_audit_events(id: str):
    """Retrieve full append-only audit event history for a specific college."""
    college = await scorecard_service.get_college_by_id(id)
    events = await ledger_service.get_events_for_college(id)

    if not college and not events:
        raise HTTPException(status_code=404, detail=f"No college or audit history found for ID '{id}'.")

    return {
        "college_id": id,
        "college_name": college.name if college else "Unknown College",
        "total_events": len(events),
        "events": events,
    }


@router.get("/export")
async def export_knowledge_index():
    """Retrieve indexed audit summary across all colleges with provenance updates."""
    summary = await ledger_service.export_knowledge_summary()
    recent_events = await ledger_service.get_all_events(limit=50)

    return {
        "total_colleges_audited": len(summary),
        "summary": summary,
        "recent_events": recent_events,
    }


@router.get("/raw")
async def get_raw_ledger_content(format: str = Query("markdown", description="markdown or jsonl")):
    """Retrieve raw text content of knowledge ledgers."""
    if format == "markdown":
        if settings.LEDGER_MD_PATH.exists():
            return {"format": "markdown", "content": settings.LEDGER_MD_PATH.read_text(encoding="utf-8")}
        return {"format": "markdown", "content": ""}
    elif format == "jsonl":
        if settings.LEDGER_JSONL_PATH.exists():
            return {"format": "jsonl", "content": settings.LEDGER_JSONL_PATH.read_text(encoding="utf-8")}
        return {"format": "jsonl", "content": ""}
    else:
        raise HTTPException(status_code=400, detail="Invalid format. Use 'markdown' or 'jsonl'.")
