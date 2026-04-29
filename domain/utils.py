"""Domain utilities.

Contains generic utilities and decorators used across layers.
"""

import logging
import random
import re
import time
from collections.abc import Callable
from typing import ParamSpec
from typing import TypeVar

from .exceptions import QueryError

logger = logging.getLogger(__name__)

P = ParamSpec("P")
R = TypeVar("R")


def with_retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    exceptions: tuple[type[Exception], ...] = (QueryError,),
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Decorator that adds retry logic with exponential backoff."""

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            last_exc = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    last_exc = exc
                    if attempt < max_attempts - 1:
                        delay = base_delay * (2**attempt) * (0.5 + random.random())  # nosec B311
                        logger.warning(
                            "Attempt %d failed: %s, retrying in %.2fs...",
                            attempt + 1,
                            exc,
                            delay,
                        )
                        time.sleep(delay)
                    else:
                        logger.error(
                            "%s failed after %d attempts: %s",
                            func.__name__,
                            max_attempts,
                            exc,
                        )
            if last_exc:
                raise last_exc
            raise RuntimeError("Should not be reached")

        return wrapper

    return decorator


_MAX_DAX_LENGTH = 10_000
_VALID_DAX_START = re.compile(r"^\s*(DEFINE|EVALUATE)\b", re.IGNORECASE)
_BLOCKED_DMV = re.compile(r"\bINFO\.", re.IGNORECASE)


def validate_dax_query(dax: str) -> str | None:
    """Validate a user-supplied DAX query string.

    Checks length, required opening keyword, and blocks INFO.* DMV functions
    that expose internal model metadata.

    Args:
        dax: Raw DAX string from user input.

    Returns:
        Error message string if invalid, None if the query passes all checks.
    """
    stripped = dax.strip()
    if not stripped:
        return "Query is empty."
    if len(stripped) > _MAX_DAX_LENGTH:
        return f"Query exceeds maximum length of {_MAX_DAX_LENGTH:,} characters."
    if not _VALID_DAX_START.match(stripped):
        return "Query must begin with EVALUATE or DEFINE."
    if _BLOCKED_DMV.search(stripped):
        return "INFO.* DMV functions are not permitted."
    return None
