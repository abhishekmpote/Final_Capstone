"""Image storage and vision-model analysis."""

import base64
from pathlib import Path
from uuid import uuid4

import httpx

from backend.config.settings import Settings
from backend.core.exceptions import ConfigurationError
from backend.services.metadata_store import MetadataStore


class ImageService:
    """Persist validated images and request analysis from a vision-capable LLM."""

    def __init__(self, settings: Settings, metadata_store: MetadataStore) -> None:
        self.settings = settings
        self.metadata_store = metadata_store
        self.settings.image_storage_dir.mkdir(parents=True, exist_ok=True)

    def save(self, filename: str, extension: str, content: bytes) -> dict[str, object]:
        image_id = uuid4().hex
        record: dict[str, object] = {
            "image_id": image_id,
            "filename": Path(filename).name,
            "uploaded_at": self.metadata_store.timestamp_now(),
            "file_type": extension.lstrip("."),
            "file_size": len(content),
        }
        (self.settings.image_storage_dir / f"{image_id}{extension}").write_bytes(content)
        try:
            self.metadata_store.create_image(record)
        except Exception:
            (self.settings.image_storage_dir / f"{image_id}{extension}").unlink(
                missing_ok=True
            )
            raise
        return record

    async def analyze(self, image_id: str, question: str) -> str:
        record = self.metadata_store.get_image(image_id)
        if record is None:
            raise FileNotFoundError(f"Image '{image_id}' was not found.")
        if not self.settings.llm_api_key:
            raise ConfigurationError(
                "Image analysis requires LLM_API_KEY and a vision-capable LLM_MODEL."
            )
        extension = Path(record["filename"]).suffix.lower()
        path = self.settings.image_storage_dir / f"{image_id}{extension}"
        encoded = base64.b64encode(path.read_bytes()).decode("ascii")
        mime_type = "image/png" if extension == ".png" else "image/jpeg"
        response = await _request_chat_completion(
            self.settings,
            [
                {
                    "role": "system",
                    "content": (
                        "You are an assistant that describes visible information in healthcare "
                        "images. Report only what is legible, distinguish observations from "
                        "uncertainty, do not diagnose or recommend treatment, and never infer "
                        "missing patient facts. State when the image is unreadable."
                    ),
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": question},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{encoded}",
                                "detail": "high",
                            },
                        },
                    ],
                },
            ],
        )
        return response


async def _request_chat_completion(settings: Settings, messages: list[dict]) -> str:
    if not settings.llm_api_key:
        raise ConfigurationError("Set LLM_API_KEY to enable AI analysis.")
    base_url = settings.llm_base_url.rstrip("/")
    headers = {"Authorization": f"Bearer {settings.llm_api_key}"}
    payload = {"model": settings.llm_model, "messages": messages, "temperature": 0.1}
    try:
        async with httpx.AsyncClient(timeout=settings.llm_timeout_seconds) as client:
            response = await client.post(
                f"{base_url}/chat/completions", headers=headers, json=payload
            )
            response.raise_for_status()
            result = response.json()
    except httpx.HTTPStatusError as exc:
        raise RuntimeError(
            f"LLM provider returned HTTP {exc.response.status_code}."
        ) from exc
    except httpx.RequestError as exc:
        raise RuntimeError(f"Unable to reach the configured LLM provider: {exc}") from exc
    try:
        content = result["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError("LLM provider returned an invalid response.") from exc
    if not isinstance(content, str) or not content.strip():
        raise RuntimeError("LLM provider returned an empty response.")
    return content.strip()
