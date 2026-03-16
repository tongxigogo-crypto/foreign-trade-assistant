from typing import Callable, TypeVar

T = TypeVar("T")


def run_with_retry(fn: Callable[[], T], retries: int = 2) -> T:
    last_error = None
    for _ in range(retries + 1):
        try:
            return fn()
        except Exception as e:  # pragma: no cover
            last_error = e
    raise last_error  # pragma: no cover
