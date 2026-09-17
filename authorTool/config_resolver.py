"""
Configuration layering — config/pipeline.yaml plus the author's UI overrides.

    config/pipeline.yaml      base, read from disk, NEVER written
          | deep merge
    UI overrides              only the keys the author actually touched
          =
    EFFECTIVE CONFIG          what the run uses; hashed; written into the trace

Every axis in pipeline.yaml is settable, in any combination — that is the whole
contract. There are no named conditions and no shipped presets: a configuration
is whatever the YAML keys are currently set to.

Two rules this module exists to enforce (DESIGN.md §4.3):

  * Only touched keys enter the override layer. Pinning every widget value would
    silently mask a later edit to pipeline.yaml.
  * The layers stay inspectable. ``diff_paths`` gives the UI exactly which keys
    differ from the file on disk, so a surprising result can be traced to the
    change that caused it.

``applied()`` installs the effective config into the in-memory ``SETTINGS``
singleton for the duration of a run. It patches the loaded dict, not the file.
"""

from __future__ import annotations

import copy
import hashlib
import json
from contextlib import contextmanager
from typing import Any, Dict, Iterator, List, Optional, Tuple

from config.settings import SETTINGS


# =============================================================================
# Merging
# =============================================================================

def deep_merge(base: Dict[str, Any], overlay: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively merge ``overlay`` onto a copy of ``base``. Lists replace."""
    out = copy.deepcopy(base)
    for key, value in (overlay or {}).items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = deep_merge(out[key], value)
        else:
            out[key] = copy.deepcopy(value)
    return out


def get_path(cfg: Dict[str, Any], path: str) -> Any:
    """Read a dotted path, e.g. ``retrieval.top_k``. Missing -> None."""
    node: Any = cfg
    for part in path.split("."):
        if not isinstance(node, dict) or part not in node:
            return None
        node = node[part]
    return node


def set_path(cfg: Dict[str, Any], path: str, value: Any) -> None:
    """Write a dotted path, creating intermediate dicts as needed."""
    parts = path.split(".")
    node = cfg
    for part in parts[:-1]:
        node = node.setdefault(part, {})
    node[parts[-1]] = value


def overrides_to_nested(overrides: Dict[str, Any]) -> Dict[str, Any]:
    """Turn ``{"retrieval.top_k": 40}`` into ``{"retrieval": {"top_k": 40}}``."""
    nested: Dict[str, Any] = {}
    for path, value in overrides.items():
        set_path(nested, path, value)
    return nested


# =============================================================================
# The layers
# =============================================================================

def base_config() -> Dict[str, Any]:
    """A deep copy of config/pipeline.yaml as currently on disk."""
    SETTINGS.reload()
    return copy.deepcopy(SETTINGS.pipeline)


def resolve(base: Dict[str, Any], overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """pipeline.yaml -> UI overrides (dotted keys) -> effective config."""
    return deep_merge(base, overrides_to_nested(overrides or {}))


def canonical_json(cfg: Dict[str, Any]) -> str:
    return json.dumps(cfg, sort_keys=True, separators=(",", ":"), default=str)


def config_hash(cfg: Dict[str, Any]) -> str:
    """sha256 of the canonical-JSON effective config. Shown in the UI and
    written into the trace — this is what makes a finding reproducible."""
    return hashlib.sha256(canonical_json(cfg).encode("utf-8")).hexdigest()


def _walk(cfg: Any, prefix: str = "") -> Iterator[Tuple[str, Any]]:
    if isinstance(cfg, dict):
        for key, value in cfg.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            if isinstance(value, dict):
                yield from _walk(value, path)
            else:
                yield path, value
    else:
        yield prefix, cfg


def diff_paths(base: Dict[str, Any], effective: Dict[str, Any]) -> List[Tuple[str, Any, Any]]:
    """Every dotted path where the effective config differs from pipeline.yaml."""
    diffs: List[Tuple[str, Any, Any]] = []
    seen = set()
    for path, value in _walk(effective):
        seen.add(path)
        before = get_path(base, path)
        if before != value:
            diffs.append((path, before, value))
    for path, value in _walk(base):
        if path not in seen:
            diffs.append((path, value, None))
    return sorted(diffs)


def summarise(cfg: Dict[str, Any]) -> str:
    """One-line description of the axes that identify a configuration."""
    two_call = (cfg.get("two_call", {}) or {}).get("enabled", False)
    return " · ".join(
        [
            str(cfg.get("embedder")),
            str(cfg.get("query_strategy")),
            str(cfg.get("retriever")),
            f"rerank:{cfg.get('reranker')}",
            f"two_call:{'on' if two_call else 'off'}",
        ]
    )


# =============================================================================
# Installing a config for one run
# =============================================================================

@contextmanager
def applied(effective: Dict[str, Any]):
    """Install ``effective`` into the in-memory SETTINGS for the duration.

    The pipeline reads ``SETTINGS.pipeline`` both when constructed (component
    names, post-processing, thresholds) and during a search (hierarchical and
    hybrid parameters), so both the build and the run must happen inside this
    block. config/pipeline.yaml on disk is never touched.
    """
    SETTINGS._ensure_loaded()
    previous = SETTINGS._pipeline
    SETTINGS._pipeline = copy.deepcopy(effective)
    try:
        yield SETTINGS._pipeline
    finally:
        SETTINGS._pipeline = previous
