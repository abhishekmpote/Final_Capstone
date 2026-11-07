"""Request and response models shared by API routers."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=128)
    password: str = Field(min_length=1, max_length=256)


class LoginResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_at: datetime
    username: str
    message: str = "Login successful."


class SourceReference(BaseModel):
    document_id: str
    filename: str
    page_number: int | None = None
    chunk_id: str
    relevance_score: float
    passage: str
    metadata: dict[str, str | int | float | bool | None] = Field(default_factory=dict)


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=10000)
    conversation_id: str | None = None
    history: list[dict[str, str]] = Field(default_factory=list, max_length=30)
    top_k: int | None = Field(default=None, ge=1, le=20)
    filters: dict[str, str] = Field(default_factory=dict)


class ChatResponse(BaseModel):
    conversation_id: str
    answer: str
    sources: list[SourceReference]
    metadata: dict[str, str | int | float | bool | None] = Field(default_factory=dict)


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=10000)
    top_k: int | None = Field(default=None, ge=1, le=20)
    filters: dict[str, str] = Field(default_factory=dict)
    search_mode: Literal["semantic", "hybrid"] = "hybrid"


class SearchResponse(BaseModel):
    query: str
    search_mode: str
    results: list[SourceReference]


class DocumentMetadata(BaseModel):
    document_id: str
    filename: str
    uploaded_at: datetime
    file_type: str
    file_size: int
    processing_status: str
    category: str | None = None
    department: str | None = None
    patient_id: str | None = None
    error: str | None = None


class DocumentListResponse(BaseModel):
    documents: list[DocumentMetadata]


class ImageMetadata(BaseModel):
    image_id: str
    filename: str
    uploaded_at: datetime
    file_type: str
    file_size: int


class ImageListResponse(BaseModel):
    images: list[ImageMetadata]


class ImageUploadResponse(ImageMetadata):
    message: str = "Image uploaded successfully."


class ImageAnalysisRequest(BaseModel):
    image_id: str = Field(min_length=1)
    question: str = Field(
        default="Extract and explain the readable information in this image.",
        max_length=2000,
    )


class ImageAnalysisResponse(BaseModel):
    image_id: str
    analysis: str
    disclaimer: str = (
        "Image-based output may be incomplete or inaccurate and must be verified by a qualified healthcare professional."
    )


class DashboardResponse(BaseModel):
    total_documents: int
    indexed_documents: int
    pending_documents: int
    failed_documents: int
    total_images: int


class IngestionStatusResponse(BaseModel):
    document_id: str
    status: str
    error: str | None = None


class DocumentUploadResponse(DocumentMetadata):
    message: str = "Document uploaded; ingestion has been queued."
