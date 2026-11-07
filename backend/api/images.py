"""Image upload and vision-analysis endpoints."""

import logging

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile

from backend.core.exceptions import ConfigurationError
from backend.core.security import authenticated_user
from backend.models.schemas import (
    ImageAnalysisRequest,
    ImageAnalysisResponse,
    ImageListResponse,
    ImageUploadResponse,
)
from backend.utils.file_validator import (
    IMAGE_EXTENSIONS,
    read_upload,
    validate_extension,
    validate_image_payload,
)

router = APIRouter(prefix="/images", tags=["images"])
logger = logging.getLogger(__name__)


@router.post("/upload", response_model=ImageUploadResponse, status_code=201)
async def upload_image(
    request: Request,
    file: UploadFile = File(...),
    _username: str = Depends(authenticated_user),
) -> ImageUploadResponse:
    try:
        extension = validate_extension(file.filename or "", IMAGE_EXTENSIONS)
        content = await read_upload(
            file, request.app.state.settings.max_upload_size_mb * 1024 * 1024
        )
        validate_image_payload(content, extension)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    record = request.app.state.image_service.save(
        file.filename or "upload", extension, content
    )
    return ImageUploadResponse(**record)


@router.get("", response_model=ImageListResponse)
def list_images(
    request: Request, _username: str = Depends(authenticated_user)
) -> ImageListResponse:
    return ImageListResponse(images=request.app.state.metadata_store.list_images())


@router.post("/analyze", response_model=ImageAnalysisResponse)
async def analyze_image(
    payload: ImageAnalysisRequest,
    request: Request,
    _username: str = Depends(authenticated_user),
) -> ImageAnalysisResponse:
    try:
        analysis = await request.app.state.image_service.analyze(
            payload.image_id, payload.question
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ConfigurationError as exc:
        logger.error("Image analysis is not configured", extra={"error": str(exc)})
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except RuntimeError as exc:
        logger.exception("Image analysis failed")
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return ImageAnalysisResponse(image_id=payload.image_id, analysis=analysis)
