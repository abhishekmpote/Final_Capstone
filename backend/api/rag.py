"""Document retrieval endpoint."""

from fastapi import APIRouter, Depends, HTTPException, Request

from backend.core.exceptions import ConfigurationError
from backend.core.security import authenticated_user
from backend.models.schemas import SearchRequest, SearchResponse

router = APIRouter(prefix="/rag", tags=["retrieval"])


@router.post("/search", response_model=SearchResponse)
def search(
    payload: SearchRequest,
    request: Request,
    _username: str = Depends(authenticated_user),
) -> SearchResponse:
    try:
        results = request.app.state.retrieval_service.search(
            payload.query,
            payload.top_k,
            payload.filters,
            payload.search_mode,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return SearchResponse(
        query=payload.query, search_mode=payload.search_mode, results=results
    )
