"""Document storage and metadata operations."""

import logging
from pathlib import Path
from uuid import uuid4

from backend.config.settings import Settings
from backend.services.metadata_store import MetadataStore
from backend.services.vector_store import VectorStore

logger = logging.getLogger(__name__)


class DocumentService:
    """Store uploaded documents under generated names and manage their metadata."""

    def __init__(
        self, settings: Settings, metadata_store: MetadataStore, vector_store: VectorStore
    ) -> None:
        self.settings = settings
        self.metadata_store = metadata_store
        self.vector_store = vector_store
        self.settings.document_storage_dir.mkdir(parents=True, exist_ok=True)

    def save(
        self,
        filename: str,
        extension: str,
        content: bytes,
        category: str | None,
        department: str | None,
        patient_id: str | None,
    ) -> dict[str, object]:
        """Persist a file and create its initial pending record."""
        document_id = uuid4().hex
        record: dict[str, object] = {
            "document_id": document_id,
            "filename": Path(filename).name,
            "uploaded_at": self.metadata_store.timestamp_now(),
            "file_type": extension.lstrip("."),
            "file_size": len(content),
            "processing_status": "pending",
            "category": category,
            "department": department,
            "patient_id": patient_id,
            "error": None,
        }
        target = self.settings.document_storage_dir / f"{document_id}{extension}"
        target.write_bytes(content)
        try:
            self.metadata_store.create_document(record)
        except Exception:
            target.unlink(missing_ok=True)
            logger.exception(
                "Unable to save document metadata",
                extra={"document_id": document_id},
            )
            raise
        return record

    def delete(self, document_id: str) -> bool:
        """Remove the document metadata, uploaded bytes, and indexed chunks."""
        record = self.metadata_store.get_document(document_id)
        if record is None:
            return False
        self.vector_store.delete_document(document_id)
        path = self.settings.document_storage_dir / (
            document_id + Path(record["filename"]).suffix.lower()
        )
        path.unlink(missing_ok=True)
        return self.metadata_store.delete_document(document_id)
