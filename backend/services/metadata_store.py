"""SQLite persistence for uploaded file metadata and processing state."""

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator


class MetadataStore:
    """Persist document and image metadata independently of the vector index."""

    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.database_path, timeout=30)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def initialize(self) -> None:
        """Create metadata tables if they do not already exist."""
        with self._connection() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    document_id TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    uploaded_at TEXT NOT NULL,
                    file_type TEXT NOT NULL,
                    file_size INTEGER NOT NULL,
                    processing_status TEXT NOT NULL,
                    category TEXT,
                    department TEXT,
                    patient_id TEXT,
                    error TEXT
                );
                CREATE TABLE IF NOT EXISTS images (
                    image_id TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    uploaded_at TEXT NOT NULL,
                    file_type TEXT NOT NULL,
                    file_size INTEGER NOT NULL
                );
                """
            )

    def create_document(self, document: dict[str, Any]) -> None:
        with self._connection() as connection:
            connection.execute(
                """
                INSERT INTO documents (
                    document_id, filename, uploaded_at, file_type, file_size,
                    processing_status, category, department, patient_id, error
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    document["document_id"],
                    document["filename"],
                    document["uploaded_at"],
                    document["file_type"],
                    document["file_size"],
                    document["processing_status"],
                    document.get("category"),
                    document.get("department"),
                    document.get("patient_id"),
                    document.get("error"),
                ),
            )

    def get_document(self, document_id: str) -> dict[str, Any] | None:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT * FROM documents WHERE document_id = ?", (document_id,)
            ).fetchone()
        return dict(row) if row else None

    def list_documents(self) -> list[dict[str, Any]]:
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT * FROM documents ORDER BY uploaded_at DESC"
            ).fetchall()
        return [dict(row) for row in rows]

    def update_document_status(
        self, document_id: str, status: str, error: str | None = None
    ) -> None:
        with self._connection() as connection:
            connection.execute(
                """
                UPDATE documents SET processing_status = ?, error = ?
                WHERE document_id = ?
                """,
                (status, error, document_id),
            )

    def delete_document(self, document_id: str) -> bool:
        with self._connection() as connection:
            cursor = connection.execute(
                "DELETE FROM documents WHERE document_id = ?", (document_id,)
            )
        return cursor.rowcount > 0

    def create_image(self, image: dict[str, Any]) -> None:
        with self._connection() as connection:
            connection.execute(
                """
                INSERT INTO images (image_id, filename, uploaded_at, file_type, file_size)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    image["image_id"],
                    image["filename"],
                    image["uploaded_at"],
                    image["file_type"],
                    image["file_size"],
                ),
            )

    def get_image(self, image_id: str) -> dict[str, Any] | None:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT * FROM images WHERE image_id = ?", (image_id,)
            ).fetchone()
        return dict(row) if row else None

    def list_images(self) -> list[dict[str, Any]]:
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT * FROM images ORDER BY uploaded_at DESC"
            ).fetchall()
        return [dict(row) for row in rows]

    def delete_image(self, image_id: str) -> bool:
        with self._connection() as connection:
            cursor = connection.execute(
                "DELETE FROM images WHERE image_id = ?", (image_id,)
            )
        return cursor.rowcount > 0

    def dashboard_counts(self) -> dict[str, int]:
        with self._connection() as connection:
            document_counts = connection.execute(
                """
                SELECT COUNT(*) AS total,
                    SUM(CASE WHEN processing_status = 'indexed' THEN 1 ELSE 0 END) AS indexed,
                    SUM(CASE WHEN processing_status IN ('pending', 'processing') THEN 1 ELSE 0 END) AS pending,
                    SUM(CASE WHEN processing_status = 'failed' THEN 1 ELSE 0 END) AS failed
                FROM documents
                """
            ).fetchone()
            image_count = connection.execute("SELECT COUNT(*) FROM images").fetchone()[0]
        return {
            "total_documents": document_counts["total"] or 0,
            "indexed_documents": document_counts["indexed"] or 0,
            "pending_documents": document_counts["pending"] or 0,
            "failed_documents": document_counts["failed"] or 0,
            "total_images": image_count,
        }

    @staticmethod
    def timestamp_now() -> str:
        """Return a sortable UTC timestamp."""
        return datetime.now(timezone.utc).isoformat()
