"""Gemini LLM client — structured JSON and plain text responses."""

import logging
import os
from typing import Optional

from dotenv import load_dotenv
from google import genai
from pydantic import BaseModel, ValidationError

from config.settings import GEMINI_MODEL

load_dotenv()

logger = logging.getLogger("GeminiClient")

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    logger.warning("GEMINI_API_KEY is not set — Gemini calls will fail.")

# Client is constructed lazily so importing this module without an API key works
_client: Optional[genai.Client] = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=API_KEY)
    return _client


def structured_response(prompt: str, schema_class: type[BaseModel]) -> Optional[BaseModel]:
    """
    Ask Gemini for JSON conforming to a Pydantic schema.
    Returns None if the API errors or the response fails validation.
    """
    try:
        response = _get_client().models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": schema_class.model_json_schema(),
            },
        )
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
        response = _get_client().models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
        )
        return response.text.strip()
    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        return ""
