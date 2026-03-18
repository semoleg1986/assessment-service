from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from typing import TypeVar

from fastapi import HTTPException

F = TypeVar("F", bound=Callable[..., object])


def with_error_mapping(
    *mappings: tuple[type[Exception], int],
) -> Callable[[F], F]:
    """
    Apply reusable exception-to-HTTP mapping for route handlers.

    Example:
        @with_error_mapping((NotFoundError, 404), (InvariantViolationError, 409))
        def route(...): ...
    """

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapped(*args: object, **kwargs: object) -> object:
            try:
                return func(*args, **kwargs)
            except HTTPException:
                raise
            except Exception as exc:
                for exc_type, status_code in mappings:
                    if isinstance(exc, exc_type):
                        raise HTTPException(
                            status_code=status_code,
                            detail=str(exc),
                        ) from exc
                raise

        return wrapped  # type: ignore[return-value]

    return decorator
