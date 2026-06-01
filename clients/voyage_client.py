"""Voyage AI client — embeddings and reranking."""

import logging
import os
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("VoyageClient")

API_KEY = os.getenv("VOYAGE_API_KEY")

_client = None


def get_client():
    global _client
    if _client is None:
        import voyageai
        _client = voyageai.Client(api_key=API_KEY)
    return _client
