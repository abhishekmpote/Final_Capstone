"""Tests for persisted file metadata and dashboard counts."""

import tempfile
import unittest
from pathlib import Path

from backend.services.metadata_store import MetadataStore


class MetadataStoreTests(unittest.TestCase):
    def test_document_status_and_dashboard_counts_are_persisted(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            store = MetadataStore(Path(temporary_directory) / "metadata.sqlite3")
            store.create_document(
                {
                    "document_id": "doc-1",
                    "filename": "guide.pdf",
                    "uploaded_at": store.timestamp_now(),
                    "file_type": "pdf",
                    "file_size": 1024,
                    "processing_status": "pending",
                    "category": "policy",
                    "department": None,
                    "patient_id": None,
                    "error": None,
                }
            )
            store.update_document_status("doc-1", "indexed")
            store.create_image(
                {
                    "image_id": "image-1",
                    "filename": "report.png",
                    "uploaded_at": store.timestamp_now(),
                    "file_type": "png",
                    "file_size": 512,
                }
            )

            self.assertEqual(store.get_document("doc-1")["processing_status"], "indexed")
            self.assertEqual(store.dashboard_counts(), {
                "total_documents": 1,
                "indexed_documents": 1,
                "pending_documents": 0,
                "failed_documents": 0,
                "total_images": 1,
            })
            self.assertEqual(len(store.list_images()), 1)
            self.assertTrue(store.delete_image("image-1"))
            self.assertFalse(store.delete_image("image-1"))


if __name__ == "__main__":
    unittest.main()
