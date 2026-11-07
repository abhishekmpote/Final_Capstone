"""Persistent ChromaDB collection for document chunks."""

from pathlib import Path
from typing import Any

from backend.core.exceptions import ConfigurationError


class VectorStore:
    """Wrap the document collection and keep ChromaDB out of API routes."""

    def __init__(self, storage_dir: Path) -> None:
        storage_dir.mkdir(parents=True, exist_ok=True)
        try:
            import chromadb
        except ImportError as exc:
            raise ConfigurationError("Install backend dependencies to enable vector storage.") from exc
        self._client = chromadb.PersistentClient(path=str(storage_dir))
        self._collection = self._client.get_or_create_collection(
            name="healthcare_documents",
            metadata={"hnsw:space": "cosine"},
        )

    def upsert(
        self,
        ids: list[str],
        embeddings: list[list[float]],
        documents: list[str],
        metadatas: list[dict[str, str | int | float | bool]],
    ) -> None:
        if ids:
            self._collection.upsert(
                ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas
            )

    def delete_document(self, document_id: str) -> None:
        self._collection.delete(where={"document_id": document_id})

    def count(self) -> int:
        return self._collection.count()

    def semantic_search(
        self,
        embedding: list[float],
        top_k: int,
        where: dict[str, Any] | None,
    ) -> list[dict[str, Any]]:
        if not self.count():
            return []
        arguments: dict[str, Any] = {
            "query_embeddings": [embedding],
            "n_results": min(top_k, self.count()),
            "include": ["documents", "metadatas", "distances"],
        }
        if where:
            arguments["where"] = where
        raw = self._collection.query(**arguments)
        identifiers = raw["ids"][0]
        documents = raw["documents"][0]
        metadatas = raw["metadatas"][0]
        distances = raw["distances"][0]
        return [
            {
                "id": identifiers[index],
                "document": documents[index],
                "metadata": metadatas[index],
                "distance": distances[index],
            }
            for index in range(len(identifiers))
        ]

    def all_chunks(self, where: dict[str, Any] | None) -> list[dict[str, Any]]:
        arguments: dict[str, Any] = {"include": ["documents", "metadatas"]}
        if where:
            arguments["where"] = where
        raw = self._collection.get(**arguments)
        return [
            {
                "id": raw["ids"][index],
                "document": raw["documents"][index],
                "metadata": raw["metadatas"][index],
            }
            for index in range(len(raw["ids"]))
        ]
