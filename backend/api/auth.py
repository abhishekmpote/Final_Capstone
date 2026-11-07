"""Authentication endpoints."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials

from backend.core.security import authenticated_user, bearer_scheme
from backend.models.schemas import LoginRequest, LoginResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, request: Request) -> LoginResponse:
    """Validate credentials and issue an expiring bearer token."""
    auth_service = request.app.state.auth_service
    try:
        valid = auth_service.authenticate(payload.username, payload.password)
    except FileNotFoundError as exc:
        logger.error("Authentication credentials are not configured", extra={"error": str(exc)})
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        logger.exception("Authentication credentials file is invalid")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc
    if not valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
        )
    token, expires_at = auth_service.issue_token(payload.username)
    return LoginResponse(
        access_token=token,
        expires_at=expires_at,
        username=payload.username,
    )


@router.post("/logout", status_code=204)
def logout(
    request: Request,
    _username: str = Depends(authenticated_user),
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> None:
    if credentials is not None:
        request.app.state.auth_service.revoke_token(credentials.credentials)
