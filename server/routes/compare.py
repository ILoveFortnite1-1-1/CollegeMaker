from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Request
from server.config import settings
from server.services.comparison import comparison_service
from server.services.portfolio import portfolio_service
from server.services.scorecard import scorecard_service

router = APIRouter(prefix="/api/compare", tags=["compare"])


@router.get("")
async def compare_colleges_endpoint(
    request: Request,
    ids: Optional[str] = Query(None, description="Comma-separated college IDs to compare (2 to 6)"),
):
    """Generate normalized side-by-side comparison matrix, highlights, and analytics for 2–6 colleges."""
    if ids is None or str(ids).strip() == "":
        # Check if saved colleges in guest portfolio can be compared
        cookie_id = request.cookies.get(settings.COOKIE_NAME)
        if cookie_id:
            portfolio, _, _ = await portfolio_service.get_or_create_portfolio(cookie_id)
            if len(portfolio.colleges) >= 2:
                ids_list = [c.college_id for c in portfolio.colleges[:6]]
            else:
                raise HTTPException(
                    status_code=400,
                    detail="Please provide at least 2 college IDs via '?ids=id1,id2' or save 2+ colleges in your portfolio.",
                )
        else:
            raise HTTPException(
                status_code=400,
                detail="Please provide at least 2 college IDs via '?ids=id1,id2'.",
            )
    else:
        raw_list = [i.strip() for i in ids.split(",") if i.strip()]
        # Check for duplicates or single unique ID
        unique_list = []
        for i in raw_list:
            if i not in unique_list:
                unique_list.append(i)
        if len(unique_list) < 2:
            raise HTTPException(
                status_code=400,
                detail="Comparison requires at least 2 distinct colleges. Example: '?ids=166683,243744'",
            )
        ids_list = raw_list

    if len(ids_list) < 2:
        raise HTTPException(
            status_code=400,
            detail="Comparison requires at least 2 colleges. Example: '?ids=166683,243744'",
        )
    if len(ids_list) > 6:
        raise HTTPException(
            status_code=400,
            detail="Comparison supports a maximum of 6 colleges simultaneously.",
        )

    # Check if all IDs exist
    for cid in ids_list:
        c_check = await scorecard_service.get_college_by_id(cid)
        if not c_check:
            raise HTTPException(status_code=404, detail=f"College ID '{cid}' not found.")

    # Resolve preferences if available
    prefs = None
    cookie_id = request.cookies.get(settings.COOKIE_NAME)
    if cookie_id:
        portfolio, _, _ = await portfolio_service.get_or_create_portfolio(cookie_id)
        prefs = portfolio.preferences

    try:
        comparison_result = await comparison_service.compare_colleges(ids_list, prefs)
        colleges_api = [c.to_api_dict() for c in comparison_result["colleges"]]
        return {
            "colleges": colleges_api,
            "items": colleges_api,
            "metrics": comparison_result["metrics"],
            "matrix": comparison_result["metrics"],
            "comparison_matrix": comparison_result["metrics"],
            "best_in_class": comparison_result["best_in_class"],
            "highlights": comparison_result["best_in_class"],
            "summary_highlights": comparison_result["best_in_class"],
            "summary": comparison_result["summary"],
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
