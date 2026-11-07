"""Conversational AI endpoint."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Request

from backend.core.exceptions import ConfigurationError
from backend.core.security import authenticated_user
from backend.models.schemas import ChatRequest, ChatResponse

router = APIRouter(prefix="/chat", tags=["chat"])
logger = logging.getLogger(__name__)


@router.post("", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    request: Request,
    _username: str = Depends(authenticated_user),
) -> ChatResponse:
    try:
        return await request.app.state.chat_service.answer(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ConfigurationError as exc:
        logger.error("Chat service is not configured", extra={"error": str(exc)})
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except RuntimeError as exc:
        logger.exception("Chat response generation failed")
        raise HTTPException(status_code=502, detail=str(exc)) from exc
