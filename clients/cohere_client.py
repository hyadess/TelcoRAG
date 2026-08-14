"""Lazy, process-wide Cohere client used by rerankers."""

import os
from dotenv import load_dotenv

load_dotenv()

# Lazy import to avoid hard dependency if Cohere isn't selected
_client = None


def get_client():
    """Return the shared Cohere client, creating it on first use."""
    global _client
    if _client is None:
        import cohere

        api_key = os.getenv("COHERE_API_KEY")
        if not api_key:
            raise RuntimeError(
                "COHERE_API_KEY is not set. Add it to .env before using Cohere."
            )
        _client = cohere.ClientV2(api_key=api_key)
    return _client
