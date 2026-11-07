"""Document parsing, chunking, embedding, and vector indexing."""

import logging
from pathlib import Path
from uuid import uuid4

from backend.config.settings import Settings
from backend.core.exceptions import DocumentProcessingError
from backend.services.embedding_service import EmbeddingService
from backend.services.metadata_store import MetadataStore
from backend.services.vector_store import VectorStore
from backend.utils.document_parser import extract_pages
from backend.utils.text_chunker import split_text

logger = logging.getLogger(__name__)


class IngestionService:
    """Turn uploaded files into traceable, searchable document chunks."""

    def __init__(
        self,
        settings: Settings,
        metadata_store: MetadataStore,
        vector_store: VectorStore,
        embedding_service: EmbeddingService,
    ) -> None:
        self.settings = settings
        self.metadata_store = metadata_store
        self.vector_store = vector_store
        self.embedding_service = embedding_service

    def process(self, document_id: str) -> None:
        """Ingest a document and persist failures as an explicit status."""
        record = self.metadata_store.get_document(document_id)
        if record is None:
            raise DocumentProcessingError(f"Document '{document_id}' does not exist.")
        self.metadata_store.update_document_status(document_id, "processing")
        try:
            path = self.settings.document_storage_dir / (
                document_id + Path(record["filename"]).suffix.lower()
            )
            pages = extract_pages(path.name, path.read_bytes())
            chunks: list[str] = []
            chunk_metadata: list[dict[str, str | int | float | bool]] = []
            for page_number, page_text in pages:
                page_chunks = split_text(
                    page_text, self.settings.chunk_size, self.settings.chunk_overlap
                )
                for chunk in page_chunks:
                    chunks.append(chunk)
                    metadata: dict[str, str | int | float | bool] = {
                        "document_id": document_id,
                        "filename": record["filename"],
                        "page_number": page_number,
                        "file_type": record["file_type"],
                        "chunk_index": len(chunks) - 1,
                    }
                    for field in ("category", "department", "patient_id"):
                        if record.get(field):
                            metadata[field] = record[field]
                    chunk_metadata.append(metadata)
            if not chunks:
                raise DocumentProcessingError(
                    "No text could be extracted. The file may be empty, scanned, or corrupted."
                )
            embeddings = self.embedding_service.embed(chunks)
            ids = [f"{document_id}:{index}:{uuid4().hex[:8]}" for index in range(len(chunks))]
            self.vector_store.delete_document(document_id)
            self.vector_store.upsert(ids, embeddings, chunks, chunk_metadata)
            self.metadata_store.update_document_status(document_id, "indexed")
            logger.info(
                "Document ingestion completed",
                extra={"document_id": document_id, "chunk_count": len(chunks)},
            )
        except Exception as exc:
            self.metadata_store.update_document_status(document_id, "failed", str(exc))
            logger.exception(
                "Document ingestion failed",
                extra={"document_id": document_id, "error": str(exc)},
            )
