"""Test helpers shared across the integration suite."""

import functools
import warnings

import pytest


def _is_forbidden(exc: BaseException) -> bool:
    """Return True if ``exc`` (or anything in its cause/context chain) represents
    an HTTP 403 Forbidden response.

    The fetchers wrap remote errors in different ways (``httpx.HTTPStatusError``,
    ``requests`` errors, ``ChEBIError``, ``ConnectionError``, ``ValueError`` …),
    so we walk the whole exception chain and check both the response status code
    and the string representation.
    """
    seen: set[int] = set()
    while exc is not None and id(exc) not in seen:
        seen.add(id(exc))

        response = getattr(exc, "response", None)
        if getattr(response, "status_code", None) == 403:
            return True

        message = str(exc)
        if "403" in message or "Forbidden" in message:
            return True

        exc = exc.__cause__ or exc.__context__

    return False


def skip_on_forbidden(func):
    """Skip a remote test (with a warning) when the remote API returns HTTP 403.

    Some databases block outbound requests from CI, which surfaces as a 403
    Forbidden. That is an environment restriction, not a genuine test failure,
    so we emit a warning and skip the test rather than fail it.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as exc:
            if _is_forbidden(exc):
                warnings.warn(
                    f"'{func.__name__}' received HTTP 403 Forbidden from a remote "
                    f"API (likely blocked in this environment); skipping.",
                    stacklevel=2,
                )
                pytest.skip(f"Remote API returned 403 Forbidden for {func.__name__}")
            raise

    return wrapper
