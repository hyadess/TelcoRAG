"""Cohere client — used for embeddings and reranking."""

import logging
import os
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("CohereClient")

API_KEY = os.getenv("COHERE_API_KEY")

# Lazy import to avoid hard dependency if Cohere isn't selected
_client = None


def get_client():
    global _client
    if _client is None:
        import cohere
        _client = cohere.ClientV2(API_KEY)
    return _client
