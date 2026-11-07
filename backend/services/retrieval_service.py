"""Filtered semantic and hybrid retrieval over indexed document chunks."""

import re
from typing import Any

from backend.config.settings import Settings
from backend.services.embedding_service import EmbeddingService
from backend.services.vector_store import VectorStore
from backend.models.schemas import SourceReference

ALLOWED_FILTERS = {
    "document_id",
    "category",
    "department",
    "patient_id",
    "file_type",
}


class RetrievalService:
    """Combine vector similarity and lexical matching with traceable sources."""

    def __init__(
        self,
        settings: Settings,
        vector_store: VectorStore,
        embedding_service: EmbeddingService,
    ) -> None:
        self.settings = settings
        self.vector_store = vector_store
        self.embedding_service = embedding_service

    def search(
        self,
        query: str,
        top_k: int | None,
        filters: dict[str, str],
        search_mode: str,
    ) -> list[SourceReference]:
        where = self._build_where(filters)
        limit = top_k or self.settings.retrieval_top_k
        if self.vector_store.count() == 0:
            return []

        query_vector = self.embedding_service.embed([query])[0]
        semantic = self.vector_store.semantic_search(query_vector, limit * 4, where)
        candidates: dict[str, dict[str, Any]] = {}
        for item in semantic:
            similarity = max(0.0, min(1.0, 1.0 - float(item["distance"])))
            item["semantic_score"] = similarity
            candidates[item["id"]] = item

        if search_mode == "hybrid":
            query_terms = set(re.findall(r"[\w-]+", query.lower()))
            for item in self.vector_store.all_chunks(where):
                text_terms = set(re.findall(r"[\w-]+", item["document"].lower()))
                lexical_score = len(query_terms & text_terms) / max(1, len(query_terms))
                if lexical_score > 0:
                    current = candidates.get(item["id"], item)
                    current["lexical_score"] = lexical_score
                    current.setdefault("semantic_score", 0.0)
                    candidates[item["id"]] = current

        ranked: list[tuple[float, dict[str, Any]]] = []
        for item in candidates.values():
            semantic_score = float(item.get("semantic_score", 0.0))
            lexical_score = float(item.get("lexical_score", 0.0))
            score = (
                semantic_score
                if search_mode == "semantic"
                else 0.7 * semantic_score + 0.3 * lexical_score
            )
            if score >= 0.15:
                ranked.append((score, item))
        ranked.sort(key=lambda result: result[0], reverse=True)

        sources: list[SourceReference] = []
        seen_passages: set[str] = set()
        for score, item in ranked:
            passage = " ".join(item["document"].split())
            if passage in seen_passages:
                continue
            seen_passages.add(passage)
            metadata = item["metadata"]
            sources.append(
                SourceReference(
                    document_id=str(metadata["document_id"]),
                    filename=str(metadata["filename"]),
                    page_number=metadata.get("page_number"),
                    chunk_id=str(item["id"]),
                    relevance_score=round(score, 4),
                    passage=passage,
                    metadata={
                        key: value
                        for key, value in metadata.items()
                        if key not in {"document_id", "filename", "page_number"}
                    },
                )
            )
            if len(sources) >= limit:
                break
        return sources

    @staticmethod
    def _build_where(filters: dict[str, str]) -> dict[str, Any] | None:
        unknown = set(filters) - ALLOWED_FILTERS
        if unknown:
            raise ValueError(f"Unsupported metadata filter(s): {', '.join(sorted(unknown))}.")
        if not filters:
            return None
        conditions = [{key: value} for key, value in filters.items()]
        return conditions[0] if len(conditions) == 1 else {"$and": conditions}
