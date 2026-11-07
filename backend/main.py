"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.api import auth, chat, documents, images, ingestion, rag
from backend.config.settings import get_settings
from backend.core.logging_config import configure_logging
from backend.services.auth_service import AuthService
from backend.services.chat_service import ChatService
from backend.services.document_service import DocumentService
from backend.services.embedding_service import EmbeddingService
from backend.services.image_service import ImageService
from backend.services.ingestion_service import IngestionService
from backend.services.metadata_store import MetadataStore
from backend.services.retrieval_service import RetrievalService
from backend.services.vector_store import VectorStore

configure_logging()
logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    """Initialize persistent services once per API process."""
    for directory in (
        settings.document_storage_dir,
        settings.image_storage_dir,
        settings.vector_storage_dir,
        settings.metadata_database.parent,
    ):
        directory.mkdir(parents=True, exist_ok=True)
    metadata_store = MetadataStore(settings.metadata_database)
    vector_store = VectorStore(settings.vector_storage_dir)
    embedding_service = EmbeddingService(settings)
    retrieval_service = RetrievalService(settings, vector_store, embedding_service)
    application.state.settings = settings
    application.state.metadata_store = metadata_store
    application.state.vector_store = vector_store
    application.state.embedding_service = embedding_service
    application.state.retrieval_service = retrieval_service
    application.state.auth_service = AuthService(settings)
    application.state.document_service = DocumentService(
        settings, metadata_store, vector_store
    )
    application.state.image_service = ImageService(settings, metadata_store)
    application.state.ingestion_service = IngestionService(
        settings, metadata_store, vector_store, embedding_service
    )
    application.state.chat_service = ChatService(settings, retrieval_service)
    logger.info("Healthcare assistant API started")
    yield
    logger.info("Healthcare assistant API stopped")


app = FastAPI(title=settings.api_title, version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.frontend_origins.split(",") if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception(
        "Unhandled API error",
        extra={"path": request.url.path, "error": str(exc)},
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected server error occurred."},
    )


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(auth.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(documents.router, prefix="/api")
app.include_router(images.router, prefix="/api")
app.include_router(ingestion.router, prefix="/api")
app.include_router(rag.router, prefix="/api")
