"""HTTP client for the separately hosted FastAPI backend."""

from typing import Any

import requests

from frontend.config import API_BASE_URL


class APIError(RuntimeError):
    """An API request failed or the backend returned an error."""


class APIClient:
    """Small authenticated REST client used by Streamlit components."""

    def __init__(self, token: str | None = None, base_url: str = API_BASE_URL) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token

    def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
    ) -> Any:
        headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        try:
            response = requests.request(
                method,
                f"{self.base_url}{path}",
                headers=headers,
                json=json,
                files=files,
                data=data,
                timeout=60,
            )
        except requests.RequestException as exc:
            raise APIError(
                f"Could not connect to the backend at {self.base_url}: {exc}"
            ) from exc
        if not response.ok:
            try:
                body = response.json()
                detail = body.get("detail", response.text)
            except ValueError:
                detail = response.text
            raise APIError(f"Backend returned {response.status_code}: {detail}")
        if response.status_code == 204:
            return None
        try:
            return response.json()
        except ValueError as exc:
            raise APIError("Backend returned an invalid JSON response.") from exc

    def login(self, username: str, password: str) -> dict[str, Any]:
        return self._request(
            "POST", "/api/auth/login", json={"username": username, "password": password}
        )

    def logout(self) -> None:
        self._request("POST", "/api/auth/logout")

    def dashboard(self) -> dict[str, Any]:
        return self._request("GET", "/api/documents/dashboard")

    def documents(self) -> list[dict[str, Any]]:
        return self._request("GET", "/api/documents")["documents"]

    def upload_document(
        self,
        filename: str,
        content: bytes,
        category: str | None,
        department: str | None,
        patient_id: str | None,
    ) -> dict[str, Any]:
        return self._request(
            "POST",
            "/api/documents/upload",
            files={"file": (filename, content)},
            data={
                key: value
                for key, value in {
                    "category": category,
                    "department": department,
                    "patient_id": patient_id,
                }.items()
                if value
            },
        )

    def document_status(self, document_id: str) -> dict[str, Any]:
        return self._request("GET", f"/api/ingestion/status/{document_id}")

    def trigger_ingestion(self, document_id: str) -> dict[str, Any]:
        return self._request("POST", f"/api/ingestion/{document_id}")

    def delete_document(self, document_id: str) -> None:
        self._request("DELETE", f"/api/documents/{document_id}")

    def chat(
        self,
        question: str,
        conversation_id: str | None,
        history: list[dict[str, str]],
    ) -> dict[str, Any]:
        return self._request(
            "POST",
            "/api/chat",
            json={
                "question": question,
                "conversation_id": conversation_id,
                "history": history,
            },
        )

    def upload_image(self, filename: str, content: bytes) -> dict[str, Any]:
        return self._request(
            "POST", "/api/images/upload", files={"file": (filename, content)}
        )

    def analyze_image(self, image_id: str, question: str) -> dict[str, Any]:
        return self._request(
            "POST",
            "/api/images/analyze",
            json={"image_id": image_id, "question": question},
        )
