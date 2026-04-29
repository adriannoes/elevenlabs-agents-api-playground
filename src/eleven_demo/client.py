"""ElevenLabs SDK client factory.

Strategy **(b)**: a thin ``httpx.Client`` subclass overrides synchronous ``send()`` so
every REST round-trip passes through :func:`_with_retry`. Responses with retryable status
codes are turned into :class:`httpx.HTTPStatusError`, triggering up to three attempts with
exponential backoff (``1s``, ``2s``) between failures. Streaming HTTP bodies skip this wrapper
(the SDK rarely enables ``stream=True`` for typical REST JSON calls). WebSockets use separate
APIs and never pass through here.

REST timeouts use ``timeout=30.0`` seconds on the underlying HTTP client.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from functools import lru_cache
from typing import Any

import httpx
from elevenlabs import ElevenLabs

from eleven_demo.config import get_settings

RETRYABLE_STATUS_CODES = frozenset({429, 500, 502, 503, 504})


def _with_retry[T](callable_: Callable[[], T], *, attempts: int = 3, base_delay: float = 1.0) -> T:
    """Run ``callable_``, retrying retryable HTTP responses."""
    for attempt in range(attempts):
        try:
            return callable_()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code not in RETRYABLE_STATUS_CODES:
                raise
            if attempt == attempts - 1:
                raise
            delay = base_delay * (2**attempt)
            time.sleep(delay)
    raise AssertionError("unreachable")  # pragma: no cover


class _RetryingHttpxClient(httpx.Client):
    """HTTP client that retries transient ElevenLabs REST failures."""

    def send(self, request: httpx.Request, **kwargs: Any) -> httpx.Response:
        stream = kwargs.get("stream", False)
        if stream:
            return super().send(request, **kwargs)

        parent_send = super().send

        def call() -> httpx.Response:
            response = parent_send(request, **kwargs)
            if response.status_code not in RETRYABLE_STATUS_CODES:
                return response
            response.read()
            raise httpx.HTTPStatusError(
                f"Retryable HTTP {response.status_code}",
                request=request,
                response=response,
            )

        response = _with_retry(call)
        return response


@lru_cache
def get_client() -> ElevenLabs:
    """Return a cached ElevenLabs HTTP client with retries on transient REST failures."""
    settings = get_settings()
    api_key = settings.elevenlabs_api_key.get_secret_value()
    http_client = _RetryingHttpxClient(timeout=30.0)
    return ElevenLabs(api_key=api_key, httpx_client=http_client, timeout=30.0)
