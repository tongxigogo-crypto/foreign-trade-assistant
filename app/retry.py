"""Retry decorator for unstable external calls."""

from __future__ import annotations

import time
from collections.abc import Callable
from functools import wraps
from typing import ParamSpec, TypeVar

P = ParamSpec("P")
T = TypeVar("T")


def with_retry(
    max_attempts: int,
    base_delay_seconds: float,
    retry_exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            attempt = 1
            while True:
                try:
                    return func(*args, **kwargs)
                except retry_exceptions:
                    if attempt >= max_attempts:
                        raise
                    time.sleep(base_delay_seconds * (2 ** (attempt - 1)))
                    attempt += 1

        return wrapper

    return decorator
