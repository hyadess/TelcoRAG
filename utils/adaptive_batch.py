"""Shared adaptive batching for quota- and payload-limited provider calls."""

import logging
import time
from dataclasses import dataclass
from typing import Callable, List, Optional, Sequence, TypeVar


ItemT = TypeVar("ItemT")
ResultT = TypeVar("ResultT")


_CAPACITY_STATUS_CODES = {413, 429}
_CAPACITY_MARKERS = (
    "resource exhausted",
    "resourceexhausted",
    "resource_exhausted",
    "too many requests",
    "rate limit",
    "rate_limit",
    "quota exceeded",
    "quota_exceeded",
    "tokens per minute",
    "token per minute",
    "request too large",
    "payload too large",
    "message too large",
    "max upsert size",
    "request size limit",
)


@dataclass(frozen=True)
class AdaptiveBatchPolicy:
    """Controls how a failed capacity-limited batch is reduced and retried."""

    initial_batch_size: int
    min_batch_size: int = 1
    reduction_factor: float = 0.5
    initial_backoff_seconds: float = 5.0
    max_backoff_seconds: float = 30.0

    def __post_init__(self) -> None:
        if self.initial_batch_size < 1:
            raise ValueError("initial_batch_size must be at least 1")
        if not 1 <= self.min_batch_size <= self.initial_batch_size:
            raise ValueError("min_batch_size must be between 1 and initial_batch_size")
        if not 0 < self.reduction_factor < 1:
            raise ValueError("reduction_factor must be between 0 and 1")
        if self.initial_backoff_seconds < 0 or self.max_backoff_seconds < 0:
            raise ValueError("backoff values must not be negative")


def _exception_chain(exc: BaseException):
    """Yield an exception and its explicit/direct causes without looping."""
    seen = set()
    current = exc
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        yield current
        current = current.__cause__ or current.__context__


def is_capacity_error(exc: BaseException) -> bool:
    """Return whether an error indicates quota pressure or an oversized batch."""
    for current in _exception_chain(exc):
        status_codes = [
            getattr(current, "status_code", None),
            getattr(current, "status", None),
            getattr(getattr(current, "response", None), "status_code", None),
        ]
        code = getattr(current, "code", None)
        if callable(code):
            try:
                code = code()
            except Exception:
                code = None
        status_codes.append(code)
        if any(
            value == limit
            for value in status_codes
            for limit in _CAPACITY_STATUS_CODES
        ):
            return True

        code_text = str(code or "").lower()
        message = f"{type(current).__name__}: {current}".lower()
        if "resource_exhausted" in code_text or "resource exhausted" in code_text:
            return True
        if any(marker in message for marker in _CAPACITY_MARKERS):
            return True
    return False


def run_adaptive_batches(
    items: Sequence[ItemT],
    process_batch: Callable[[Sequence[ItemT]], ResultT],
    *,
    policy: AdaptiveBatchPolicy,
    operation: str,
    logger: logging.Logger,
    sleep: Optional[Callable[[float], None]] = None,
) -> List[ResultT]:
    """Process items in order, shrinking capacity-failed batches for the run.

    Successful results correspond one-for-one with the batches actually sent.
    Non-capacity errors, and capacity errors at the minimum size, are raised.
    """
    if not items:
        return []
    sleep = sleep or time.sleep

    results: List[ResultT] = []
    offset = 0
    batch_size = min(policy.initial_batch_size, len(items))
    consecutive_reductions = 0

    while offset < len(items):
        batch = items[offset : offset + batch_size]
        try:
            results.append(process_batch(batch))
        except Exception as exc:
            if not is_capacity_error(exc) or len(batch) <= policy.min_batch_size:
                raise

            reduced_size = max(
                policy.min_batch_size,
                int(len(batch) * policy.reduction_factor),
            )
            if reduced_size >= len(batch):
                reduced_size = len(batch) - 1
            batch_size = min(batch_size, reduced_size)
            delay = min(
                policy.max_backoff_seconds,
                policy.initial_backoff_seconds * (2 ** consecutive_reductions),
            )
            consecutive_reductions += 1
            logger.warning(
                "%s batch of %d hit a capacity limit (%s). "
                "Reducing the batch size to %d and retrying after %.1f seconds.",
                operation,
                len(batch),
                exc,
                batch_size,
                delay,
            )
            if delay:
                sleep(delay)
            continue

        offset += len(batch)
        consecutive_reductions = 0

    return results
