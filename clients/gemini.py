"""Vertex AI Gemini client — structured JSON and plain text responses."""

import logging
import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, ValidationError

from clients.llm_retry import DEFAULT_LLM_RETRY_POLICY, call_with_retry
from config.settings import GEMINI_MODEL

load_dotenv()

logger = logging.getLogger("GeminiClient")

# Client is constructed lazily so importing this module does not load credentials.
_client: Optional[genai.Client] = None

_CLOUD_PLATFORM_SCOPE = "https://www.googleapis.com/auth/cloud-platform"


def create_vertex_client(*, request_timeout_seconds: Optional[int] = None) -> genai.Client:
    """Build a Vertex AI client from the project's environment configuration.

    ``request_timeout_seconds`` is optional because embedding clients use this
    factory too. Generative calls pass the shared LLM deadline explicitly.
    """
    project = os.getenv("GOOGLE_CLOUD_PROJECT", "").strip()
    location = os.getenv("GOOGLE_CLOUD_LOCATION", "").strip()
    credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "").strip()

    missing = [
        name
        for name, value in (
            ("GOOGLE_CLOUD_PROJECT", project),
            ("GOOGLE_CLOUD_LOCATION", location),
            ("GOOGLE_APPLICATION_CREDENTIALS", credentials_path),
        )
        if not value
    ]
    if missing:
        raise RuntimeError(
            "Missing Vertex AI configuration: " + ", ".join(missing) + ". "
            "Set them in .env before using Gemini."
        )

    credential_file = Path(credentials_path).expanduser()
    if not credential_file.is_file():
        raise RuntimeError(
            f"GOOGLE_APPLICATION_CREDENTIALS does not point to a file: {credential_file}"
        )

    # Local import keeps non-Gemini code importable when Google auth is absent.
    from google.auth import load_credentials_from_file

    credentials, _ = load_credentials_from_file(
        str(credential_file),
        scopes=[_CLOUD_PLATFORM_SCOPE],
        quota_project_id=project,
    )
    http_options = {"api_version": "v1"}
    if request_timeout_seconds is not None:
        # google-genai's HttpOptions timeout is expressed in milliseconds.
        http_options["timeout"] = request_timeout_seconds * 1000

    return genai.Client(
        vertexai=True,
        project=project,
        location=location,
        credentials=credentials,
        http_options=types.HttpOptions(**http_options),
    )


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = create_vertex_client(
            request_timeout_seconds=DEFAULT_LLM_RETRY_POLICY.timeout_seconds,
        )
    return _client


def structured_response(prompt: str, schema_class: type[BaseModel]) -> Optional[BaseModel]:
    """
    Ask Gemini for JSON conforming to a Pydantic schema.
    Returns None if the API errors or the response fails validation.
    """
    try:
        response = call_with_retry(
            lambda: _get_client().models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": schema_class.model_json_schema(),
                },
            ),
            operation=f"Gemini structured response ({schema_class.__name__})",
            logger=logger,
        )
        if not response.text:
            raise ValueError("Gemini returned an empty structured response")
        return schema_class.model_validate_json(response.text)
    except ValidationError as e:
        logger.error(f"Schema validation failed for {schema_class.__name__}: {e}")
        return None
    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        return None


def general_response(prompt: str) -> str:
    """Free-form text completion. Returns empty string on failure."""
    try:
        response = call_with_retry(
            lambda: _get_client().models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
            ),
            operation="Gemini text response",
            logger=logger,
        )
        return (response.text or "").strip()
    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        return ""
