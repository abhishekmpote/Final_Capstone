"""File-based prototype authentication and in-memory bearer sessions."""

import json
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path

from backend.config.settings import Settings

class AuthService:
    """Load demonstration credentials and manage expiring API tokens."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._tokens: dict[str, tuple[str, datetime]] = {}

    def authenticate(self, username: str, password: str) -> bool:
        credentials_path: Path = self.settings.credentials_file
        if not credentials_path.is_file():
            raise FileNotFoundError(
                f"Credentials file not found: {credentials_path}. "
                "Copy credentials.example.json to credentials.json and configure users."
            )
        try:
            data = json.loads(credentials_path.read_text(encoding="utf-8"))
            users = data["users"]
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            raise ValueError(f"Invalid credentials file: {credentials_path}") from exc
        if not isinstance(users, list):
            raise ValueError("Credentials file 'users' must be a list.")
        for user in users:
            if not isinstance(user, dict):
                continue
            stored_username = user.get("username")
            stored_password = user.get("password")
            if not isinstance(stored_username, str) or not isinstance(stored_password, str):
                continue
            if secrets.compare_digest(stored_username, username) and secrets.compare_digest(
                stored_password, password
            ):
                return True
        return False

    def issue_token(self, username: str) -> tuple[str, datetime]:
        """Create a cryptographically random bearer token."""
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(
            hours=self.settings.auth_token_ttl_hours
        )
        self._tokens[token] = (username, expires_at)
        return token, expires_at

    def username_for_token(self, token: str) -> str | None:
        session = self._tokens.get(token)
        if session is None:
            return None
        username, expires_at = session
        if datetime.now(timezone.utc) >= expires_at:
            self._tokens.pop(token, None)
            return None
        return username

    def revoke_token(self, token: str) -> None:
        """Invalidate a bearer token when a user logs out."""
        self._tokens.pop(token, None)
