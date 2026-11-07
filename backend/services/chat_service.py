"""Grounded conversational response generation."""

import uuid

import httpx

from backend.config.settings import Settings
from backend.core.exceptions import ConfigurationError
from backend.models.schemas import ChatRequest, ChatResponse
from backend.services.retrieval_service import RetrievalService


class ChatService:
    """Retrieve supporting passages and generate answers constrained to sources."""

    def __init__(self, settings: Settings, retrieval_service: RetrievalService) -> None:
        self.settings = settings
        self.retrieval_service = retrieval_service

    async def answer(self, request: ChatRequest) -> ChatResponse:
        sources = self.retrieval_service.search(
            request.question,
            request.top_k,
            request.filters,
            "hybrid",
        )
        conversation_id = request.conversation_id or str(uuid.uuid4())
        if not sources:
            return ChatResponse(
                conversation_id=conversation_id,
                answer=(
                    "I couldn't find relevant information in the indexed documents. "
                    "Please upload or index a relevant source before relying on an answer."
                ),
                sources=[],
                metadata={"grounded": True, "retrieved_chunks": 0},
            )
        if not self.settings.llm_api_key:
            raise ConfigurationError(
                "Grounded response generation requires LLM_API_KEY. "
                "Configure an OpenAI-compatible provider in the backend environment."
            )

        source_context = "\n\n".join(
            f"[{index}] Source: {source.filename}"
            f"{f', page {source.page_number}' if source.page_number else ''}\n"
            f"{source.passage}"
            for index, source in enumerate(sources, 1)
        )
        messages: list[dict[str, str]] = [
            {
                "role": "system",
                "content": (
                    "Answer the user's question using only the supplied source passages. "
                    "Cite factual statements with the source number, for example [1]. "
                    "If the passages do not contain the answer, say that the indexed sources "
                    "do not provide it. Never fabricate patient data, medical facts, policies, "
                    "or citations. Do not diagnose or recommend treatment.\n\n"
                    f"Retrieved passages:\n{source_context}"
                ),
            }
        ]
        for message in request.history[-12:]:
            role = message.get("role")
            content = message.get("content", "")
            if role in {"user", "assistant"} and content.strip():
                messages.append({"role": role, "content": content[:4000]})
        messages.append({"role": "user", "content": request.question})

        answer = await _complete(self.settings, messages)
        return ChatResponse(
            conversation_id=conversation_id,
            answer=answer,
            sources=sources,
            metadata={"grounded": True, "retrieved_chunks": len(sources)},
        )


async def _complete(settings: Settings, messages: list[dict[str, str]]) -> str:
    base_url = settings.llm_base_url.rstrip("/")
    try:
        async with httpx.AsyncClient(timeout=settings.llm_timeout_seconds) as client:
            response = await client.post(
                f"{base_url}/chat/completions",
                headers={"Authorization": f"Bearer {settings.llm_api_key}"},
                json={
                    "model": settings.llm_model,
                    "messages": messages,
                    "temperature": 0.1,
                },
            )
            response.raise_for_status()
            payload = response.json()
    except httpx.HTTPStatusError as exc:
        raise RuntimeError(
            f"LLM provider returned HTTP {exc.response.status_code}."
        ) from exc
    except httpx.RequestError as exc:
        raise RuntimeError(f"Unable to reach the configured LLM provider: {exc}") from exc
    try:
        answer = payload["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError("LLM provider returned an invalid response.") from exc
    if not isinstance(answer, str) or not answer.strip():
        raise RuntimeError("LLM provider returned an empty response.")
    return answer.strip()
