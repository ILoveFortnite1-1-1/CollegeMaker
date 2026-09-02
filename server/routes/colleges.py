"""Colleges Discovery, Detail & Enrichment Endpoints."""
import math
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Request, Response
from server.config import settings
from server.models.canonical import CanonicalCollege
from server.models.portfolio import StudentPreferences
from server.services.fit_scorer import fit_scorer
from server.services.gemini import gemini_service
from server.services.ledger import ledger_service
from server.services.portfolio import portfolio_service
from server.services.precedence import merge_college_records
from server.services.scorecard import scorecard_service

router = APIRouter(prefix="/api/colleges", tags=["colleges"])


async def _get_guest_preferences(request: Request) -> Optional[StudentPreferences]:
    """Extract student preferences from guest portfolio cookie if present."""
    cookie_id = request.cookies.get(settings.COOKIE_NAME)
    if cookie_id:
        portfolio, _, _ = await portfolio_service.get_or_create_portfolio(cookie_id)
        return portfolio.preferences
    return None


@router.get("")
async def list_colleges(
    request: Request,
    q: Optional[str] = Query(None, description="Search term for name, alias, or city"),
    query: Optional[str] = Query(None, description="Alternative alias for search query term"),
    state: Optional[str] = Query(None, description="2-letter state code filter"),
    control: Optional[str] = Query(None, description="public, private_nonprofit, or any"),
    type: Optional[str] = Query(None, description="public, private, or any"),
    max_cost: Optional[int] = Query(None, description="Maximum average annual net price"),
    min_admit_rate: Optional[float] = Query(None, description="Minimum acceptance rate (0.0 - 1.0)"),
    max_admit_rate: Optional[float] = Query(None, description="Maximum acceptance rate (0.0 - 1.0)"),
    location_type: Optional[str] = Query(None, description="Urban, Suburban, Rural, Town"),
    sort_by: str = Query("name_asc", description="Sort criteria: name_asc, name_desc, cost_asc, admit_asc, earnings_desc, name, net_price"),
    order: Optional[str] = Query(None, description="asc or desc"),
    page: int = Query(1, description="Page number"),
    page_size: int = Query(20, description="Page size"),
    limit: Optional[int] = Query(None, description="Alternative page size limit"),
    offset: Optional[int] = Query(None, description="Pagination offset"),
):
    """Search and filter colleges with pagination and dynamic student fit scoring."""
    search_term = q or query

    prefs = await _get_guest_preferences(request)

    # Normalize control / type filter
    filter_control = control
    if type and not control:
        if type.lower() == "public":
            filter_control = "public"
        elif type.lower() in ["private", "private_nonprofit"]:
            filter_control = "private_nonprofit"

    # Normalize sort criteria
    effective_sort = sort_by
    if order:
        ord_lower = order.lower()
        if sort_by in ["name", "canonical_name"]:
            effective_sort = "name_asc" if ord_lower == "asc" else "name_desc"
        elif sort_by in ["net_price", "cost"]:
            effective_sort = "cost_asc" if ord_lower == "asc" else "cost_desc"
        elif sort_by in ["admissions", "acceptance_rate", "admit_rate"]:
            effective_sort = "admit_asc" if ord_lower == "asc" else "admit_desc"
        elif sort_by in ["earnings", "median_earnings"]:
            effective_sort = "earnings_desc" if ord_lower == "desc" else "earnings_asc"

    actual_page_size = limit if limit is not None else page_size
    if actual_page_size < 0:
        raise HTTPException(status_code=400, detail="Limit must be non-negative.")
    if actual_page_size == 0:
        return {
            "items": [],
            "colleges": [],
            "total": 0,
            "page": 1,
            "page_size": 0,
            "total_pages": 0,
        }

    effective_page = max(1, page)
    if offset is not None:
        if offset < 0:
            raise HTTPException(status_code=400, detail="Offset must be non-negative.")
        effective_page = (offset // actual_page_size) + 1

    colleges, total = await scorecard_service.search_colleges(
        query=search_term,
        state=state,
        control=filter_control,
        max_cost=max_cost,
        min_admit_rate=min_admit_rate,
        max_admit_rate=max_admit_rate,
        location_type=location_type,
        sort_by=effective_sort,
        page=effective_page,
        page_size=actual_page_size,
    )

    # Attach fit scores to items
    api_items = []
    for c in colleges:
        fit_res = fit_scorer.evaluate_college_fit(c, prefs)
        c.fit_score = fit_res.overall_score
        c.fit_category = fit_res.category
        c.fit_breakdown = fit_res.to_breakdown_dict()
        api_items.append(c.to_api_dict())

    total_pages = max(1, math.ceil(total / actual_page_size)) if actual_page_size > 0 else 0

    return {
        "items": api_items,
        "colleges": api_items,
        "total": total,
        "page": effective_page,
        "page_size": actual_page_size,
        "total_pages": total_pages,
    }


@router.get("/{id}")
async def get_college_detail(id: str, request: Request):
    """Retrieve full canonical college profile with field-level provenance metadata."""
    if ".." in id or "/" in id or "\\" in id:
        raise HTTPException(status_code=400, detail="Invalid college ID.")
    prefs = await _get_guest_preferences(request)
    college = await scorecard_service.get_college_by_id(id)

    if not college:
        raise HTTPException(status_code=404, detail=f"College with ID '{id}' not found.")

    fit_res = fit_scorer.evaluate_college_fit(college, prefs)
    college.fit_score = fit_res.overall_score
    college.fit_category = fit_res.category
    college.fit_breakdown = fit_res.to_breakdown_dict()

    return college.to_api_dict()


@router.post("/{id}/refresh")
async def refresh_college_data(id: str, request: Request):
    """Trigger AI qualitative enrichment and Scorecard refresh with source precedence merge & audit ledger."""
    college = await scorecard_service.get_college_by_id(id)
    if not college:
        raise HTTPException(status_code=404, detail=f"College with ID '{id}' not found.")

    # 1. Run Gemini enrichment pipeline
    qual, claims, run, events = await gemini_service.enrich_college(college, force_refresh=True)

    # 2. Construct incoming temporary candidate college
    incoming_candidate = college.model_copy(deep=True)
    incoming_candidate.qualitative = qual
    incoming_candidate.evidence_claims = claims

    # 3. Apply source precedence hierarchy merge
    merged_college, merge_events = merge_college_records(college, incoming_candidate, run_id=run.run_id)
    all_events = events + merge_events

    # 4. Commit to Knowledge Ledger (Markdown & JSONL)
    await ledger_service.record_events(all_events, run_metadata=run)

    # 5. Persist merged record into database and cache
    await scorecard_service.save_college(merged_college)

    # Attach fit score
    prefs = await _get_guest_preferences(request)
    fit_res = fit_scorer.evaluate_college_fit(merged_college, prefs)
    merged_college.fit_score = fit_res.overall_score
    merged_college.fit_category = fit_res.category
    merged_college.fit_breakdown = fit_res.model_dump()

    return {
        "status": "success",
        "run_id": run.run_id,
        "college": merged_college.to_api_dict(),
        "run": run,
        "events_recorded": len(all_events),
    }
