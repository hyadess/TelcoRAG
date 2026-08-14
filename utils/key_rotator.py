"""
API key rotator — rotates through a pool of keys stored in env vars
(LLAMAPARSE_API_KEYPOOL, VOYAGE_API_KEYPOOL) so a single rate-limited call
doesn't kill a long ingestion run.

The current index is persisted in a JSON file in the same directory so
multiple processes share the rotation state.
"""

import ast
import json
import logging
import os
from pathlib import Path
from typing import Dict

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("KeyRotator")

CONFIG_PATH = Path(__file__).resolve().parent / "keyconfig.json"


def _load_config() -> Dict[str, int]:
    if not CONFIG_PATH.exists():
        CONFIG_PATH.write_text("{}")
    return json.loads(CONFIG_PATH.read_text() or "{}")


def _save_config(cfg: Dict[str, int]):
    CONFIG_PATH.write_text(json.dumps(cfg, indent=4))


def _rotate(env_var: str, state_key: str) -> str:
    raw = os.getenv(env_var)
    if not raw:
        raise ValueError(f"{env_var} missing in .env")

    keys = ast.literal_eval(raw)
    if not isinstance(keys, list) or not keys:
        raise ValueError(f"{env_var} must be a non-empty list literal")

    cfg = _load_config()
    # -1 makes the first call select key 0; the old default skipped the first
    # key until the pool wrapped around.
    current = cfg.get(state_key, -1)
    next_idx = (current + 1) % len(keys)
    cfg[state_key] = next_idx
    _save_config(cfg)

    key = keys[next_idx]
    if not isinstance(key, str) or not key.strip():
        raise ValueError(f"{env_var} entries must be non-empty strings")
    return key.strip()


def rotate_llamaparse_key() -> str:
    return _rotate("LLAMAPARSE_API_KEYPOOL", "CURRENT_LLAMAPARSE_KEY_INDEX")


def rotate_voyage_key() -> str:
    return _rotate("VOYAGE_API_KEYPOOL", "CURRENT_VOYAGE_KEY_INDEX")
