"""Document upload, listing, status, and deletion endpoints."""

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Request, UploadFile

from backend.core.security import authenticated_user
from backend.models.schemas import (
    DashboardResponse,
    DocumentListResponse,
    DocumentMetadata,
    DocumentUploadResponse,
)
from backend.utils.file_validator import DOCUMENT_EXTENSIONS, read_upload, validate_extension

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentUploadResponse, status_code=201)
async def upload_document(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    category: str | None = Form(default=None, max_length=128),
    department: str | None = Form(default=None, max_length=128),
    patient_id: str | None = Form(default=None, max_length=128),
    _username: str = Depends(authenticated_user),
) -> DocumentUploadResponse:
    """Validate, persist, and automatically queue a healthcare document."""
    try:
        extension = validate_extension(file.filename or "", DOCUMENT_EXTENSIONS)
        content = await read_upload(
            file, request.app.state.settings.max_upload_size_mb * 1024 * 1024
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    service = request.app.state.document_service
    record = service.save(
        file.filename or "upload",
        extension,
        content,
        category.strip() if category else None,
        department.strip() if department else None,
        patient_id.strip() if patient_id else None,
    )
    background_tasks.add_task(
        request.app.state.ingestion_service.process, str(record["document_id"])
    )
    return DocumentUploadResponse(**record)


@router.get("", response_model=DocumentListResponse)
def list_documents(
    request: Request, _username: str = Depends(authenticated_user)
) -> DocumentListResponse:
    return DocumentListResponse(
        documents=request.app.state.metadata_store.list_documents()
    )


@router.get("/dashboard", response_model=DashboardResponse)
def dashboard(
    request: Request, _username: str = Depends(authenticated_user)
) -> DashboardResponse:
    return DashboardResponse(**request.app.state.metadata_store.dashboard_counts())


@router.get("/{document_id}/status", response_model=DocumentMetadata)
def document_status(
    document_id: str,
    request: Request,
    _username: str = Depends(authenticated_user),
) -> DocumentMetadata:
    record = request.app.state.metadata_store.get_document(document_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Document not found.")
    return DocumentMetadata(**record)


@router.delete("/{document_id}", status_code=204)
def delete_document(
    document_id: str,
    request: Request,
    _username: str = Depends(authenticated_user),
) -> None:
    if not request.app.state.document_service.delete(document_id):
        raise HTTPException(status_code=404, detail="Document not found.")
