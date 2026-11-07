"""Document ingestion trigger and status endpoints."""

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request

from backend.core.security import authenticated_user
from backend.models.schemas import IngestionStatusResponse

router = APIRouter(prefix="/ingestion", tags=["ingestion"])


@router.post("/{document_id}", response_model=IngestionStatusResponse, status_code=202)
def trigger_ingestion(
    document_id: str,
    request: Request,
    background_tasks: BackgroundTasks,
    _username: str = Depends(authenticated_user),
) -> IngestionStatusResponse:
    record = request.app.state.metadata_store.get_document(document_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Document not found.")
    request.app.state.metadata_store.update_document_status(document_id, "pending")
    background_tasks.add_task(request.app.state.ingestion_service.process, document_id)
    return IngestionStatusResponse(document_id=document_id, status="pending")


@router.get("/status/{document_id}", response_model=IngestionStatusResponse)
def ingestion_status(
    document_id: str,
    request: Request,
    _username: str = Depends(authenticated_user),
) -> IngestionStatusResponse:
    record = request.app.state.metadata_store.get_document(document_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Document not found.")
    return IngestionStatusResponse(
        document_id=document_id,
        status=record["processing_status"],
        error=record["error"],
    )
