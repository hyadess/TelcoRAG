"""Shared retry policy for synchronous LLM calls."""

import logging
from dataclasses import dataclass
from typing import Callable, TypeVar


T = TypeVar("T")


@dataclass(frozen=True)
class LLMRetryPolicy:
    """Limits applied to one logical LLM request."""

    timeout_seconds: int = 180
    max_attempts: int = 2

    def __post_init__(self):
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")


DEFAULT_LLM_RETRY_POLICY = LLMRetryPolicy()


def call_with_retry(
    call: Callable[[], T],
    *,
    operation: str,
    logger: logging.Logger,
    policy: LLMRetryPolicy = DEFAULT_LLM_RETRY_POLICY,
) -> T:
    """Run ``call`` and retry failures up to the policy's attempt limit.

    The provider client enforces the per-attempt timeout. Keeping the retry
    loop here makes timeout and transport failures behave consistently across
    structured and free-form LLM requests.
    """
    for attempt in range(1, policy.max_attempts + 1):
        try:
            return call()
        except Exception as exc:
            if attempt == policy.max_attempts:
                raise
            logger.warning(
                "%s failed on attempt %d/%d (%s). Retrying.",
                operation,
                attempt,
                policy.max_attempts,
                exc,
            )

    raise RuntimeError("unreachable")
