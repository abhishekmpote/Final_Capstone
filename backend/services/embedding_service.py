"""Local, configurable sentence-transformer embeddings."""

from functools import cached_property

from backend.config.settings import Settings
from backend.core.exceptions import ConfigurationError


class EmbeddingService:
    """Generate embeddings using a locally hosted Sentence Transformers model."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    @cached_property
    def _model(self):
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise ConfigurationError(
                "Install backend dependencies to enable semantic search."
            ) from exc
        try:
            return SentenceTransformer(
                self.settings.embedding_model, device=self.settings.embedding_device
            )
        except Exception as exc:
            raise ConfigurationError(
                f"Unable to load embedding model '{self.settings.embedding_model}': {exc}"
            ) from exc

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Return normalized vector representations for input text."""
        if not texts:
            return []
        vectors = self._model.encode(
            texts,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        return vectors.tolist()
