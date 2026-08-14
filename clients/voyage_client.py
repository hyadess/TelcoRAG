"""Lazy, process-wide Voyage AI client used by rerankers."""

import os
from dotenv import load_dotenv

load_dotenv()

_client = None


def get_client():
    """Return the shared Voyage client, creating it on first use."""
    global _client
    if _client is None:
        import voyageai

        api_key = os.getenv("VOYAGE_API_KEY")
        if not api_key:
            raise RuntimeError(
                "VOYAGE_API_KEY is not set. Add it to .env before using Voyage."
            )
        _client = voyageai.Client(api_key=api_key)
    return _client
