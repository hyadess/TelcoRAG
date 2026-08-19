"""Small HTTP client used by the Streamlit UI."""

from typing import Any

import requests

from tool.settings import SETTINGS


class BackendError(RuntimeError):
    pass


def _message(response: requests.Response) -> str:
    try:
        detail = response.json().get("detail")
        if detail:
            return str(detail)
    except (ValueError, AttributeError):
        pass
    return response.text or f"HTTP {response.status_code}"


def ask(question: str, session_id: str) -> dict[str, Any]:
    try:
        response = requests.post(
            f"{SETTINGS.backend_url}/api/chat",
            json={"question": question, "session_id": session_id},
            timeout=SETTINGS.request_timeout_seconds,
        )
    except requests.RequestException as exc:
        raise BackendError(f"Cannot reach the backend: {exc}") from exc
    if not response.ok:
        raise BackendError(_message(response))
    return response.json()


def submit_rating(response_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    try:
        response = requests.put(
            f"{SETTINGS.backend_url}/api/responses/{response_id}/rating",
            json=payload,
            timeout=30,
        )
    except requests.RequestException as exc:
        raise BackendError(f"Could not save the rating: {exc}") from exc
    if not response.ok:
        raise BackendError(_message(response))
    return response.json()


def fetch_stats(admin_password: str) -> dict[str, Any]:
    try:
        response = requests.get(
            f"{SETTINGS.backend_url}/api/admin/stats",
            headers={"X-Admin-Password": admin_password},
            timeout=30,
        )
    except requests.RequestException as exc:
        raise BackendError(f"Cannot load analytics: {exc}") from exc
    if not response.ok:
        raise BackendError(_message(response))
    return response.json()
