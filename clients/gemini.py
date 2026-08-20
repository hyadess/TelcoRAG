"""Vertex AI Gemini client — structured JSON and plain text responses."""

import json
import logging
import os
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path
from typing import Iterator, Optional

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
_request_oidc_token: ContextVar[str] = ContextVar("vercel_oidc_token", default="")

_CLOUD_PLATFORM_SCOPE = "https://www.googleapis.com/auth/cloud-platform"
_OIDC_SUBJECT_TOKEN_TYPE = "urn:ietf:params:oauth:token-type:jwt"


@contextmanager
def vercel_oidc_token(token: Optional[str]) -> Iterator[None]:
    """Make a request's Vercel OIDC token available during Google auth refresh."""
    value = (token or "").strip()
    if not value:
        yield
        return
    reset_token = _request_oidc_token.set(value)
    try:
        yield
    finally:
        _request_oidc_token.reset(reset_token)


def _create_vercel_federated_credentials(
    *,
    project_number: str,
    pool_id: str,
    provider_id: str,
    service_account_email: str,
    project_id: str,
):
    from google.auth import exceptions, identity_pool

    class VercelSubjectTokenSupplier(identity_pool.SubjectTokenSupplier):
        def get_subject_token(self, context, request):
            del context, request
            token = _request_oidc_token.get() or os.getenv(
                "VERCEL_OIDC_TOKEN", ""
            ).strip()
            if not token:
                raise exceptions.RefreshError(
                    "Vercel OIDC token is unavailable. The backend must receive "
                    "the x-vercel-oidc-token request header."
                )
            return token

    audience = (
        f"//iam.googleapis.com/projects/{project_number}/locations/global/"
        f"workloadIdentityPools/{pool_id}/providers/{provider_id}"
    )
    impersonation_url = (
        "https://iamcredentials.googleapis.com/v1/projects/-/serviceAccounts/"
        f"{service_account_email}:generateAccessToken"
    )
    return identity_pool.Credentials(
        audience=audience,
        subject_token_type=_OIDC_SUBJECT_TOKEN_TYPE,
        subject_token_supplier=VercelSubjectTokenSupplier(),
        service_account_impersonation_url=impersonation_url,
        scopes=[_CLOUD_PLATFORM_SCOPE],
        quota_project_id=project_id,
    )


def create_vertex_client(*, request_timeout_seconds: Optional[int] = None) -> genai.Client:
    """Build a Vertex AI client from the project's environment configuration.

    ``request_timeout_seconds`` is optional because embedding clients use this
    factory too. Generative calls pass the shared LLM deadline explicitly.
    """
    project = os.getenv("GOOGLE_CLOUD_PROJECT", "").strip()
    location = os.getenv("GOOGLE_CLOUD_LOCATION", "").strip()
    credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "").strip()
    credentials_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "").strip()
    federation = {
        "GCP_PROJECT_NUMBER": os.getenv("GCP_PROJECT_NUMBER", "").strip(),
        "GCP_WORKLOAD_IDENTITY_POOL_ID": os.getenv(
            "GCP_WORKLOAD_IDENTITY_POOL_ID", ""
        ).strip(),
        "GCP_WORKLOAD_IDENTITY_POOL_PROVIDER_ID": os.getenv(
            "GCP_WORKLOAD_IDENTITY_POOL_PROVIDER_ID", ""
        ).strip(),
        "GCP_SERVICE_ACCOUNT_EMAIL": os.getenv(
            "GCP_SERVICE_ACCOUNT_EMAIL", ""
        ).strip(),
    }
    federation_configured = all(federation.values())
    partial_federation = any(federation.values()) and not federation_configured

    if partial_federation and not (credentials_path or credentials_json):
        missing_federation = [name for name, value in federation.items() if not value]
        raise RuntimeError(
            "Incomplete Vercel Workload Identity configuration; missing: "
            + ", ".join(missing_federation)
        )

    missing = [
        name
        for name, value in (
            ("GOOGLE_CLOUD_PROJECT", project),
            ("GOOGLE_CLOUD_LOCATION", location),
            (
                "Google credentials",
                credentials_path or credentials_json or federation_configured,
            ),
        )
        if not value
    ]
    if missing:
        raise RuntimeError(
            "Missing Vertex AI configuration: " + ", ".join(missing) + ". "
            "Set them in .env before using Gemini."
        )

    if credentials_json:
        try:
            credentials_info = json.loads(credentials_json)
        except json.JSONDecodeError as exc:
            raise RuntimeError("GOOGLE_SERVICE_ACCOUNT_JSON is not valid JSON") from exc
        from google.oauth2.service_account import Credentials

        credentials = Credentials.from_service_account_info(
            credentials_info,
            scopes=[_CLOUD_PLATFORM_SCOPE],
            quota_project_id=project,
        )
    elif federation_configured:
        credentials = _create_vercel_federated_credentials(
            project_number=federation["GCP_PROJECT_NUMBER"],
            pool_id=federation["GCP_WORKLOAD_IDENTITY_POOL_ID"],
            provider_id=federation["GCP_WORKLOAD_IDENTITY_POOL_PROVIDER_ID"],
            service_account_email=federation["GCP_SERVICE_ACCOUNT_EMAIL"],
            project_id=project,
        )
    else:
        credential_file = Path(credentials_path).expanduser()
        if not credential_file.is_file():
            raise RuntimeError(
                "GOOGLE_APPLICATION_CREDENTIALS does not point to a file: "
                f"{credential_file}"
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
