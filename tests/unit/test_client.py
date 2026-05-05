"""Unit tests for ``eleven_demo.client._with_retry`` and ``_RetryingHttpxClient``."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import httpx
import pytest

from eleven_demo.client import _RetryingHttpxClient, _with_retry


def _http_status_error(status_code: int) -> httpx.HTTPStatusError:
    request = httpx.Request("GET", "https://api.elevenlabs.io/v1/test")
    response = httpx.Response(status_code, request=request)
    return httpx.HTTPStatusError("error", request=request, response=response)


def test_with_retry_returns_immediately_on_success() -> None:
    mock_fn = MagicMock(return_value="ok")

    assert _with_retry(mock_fn) == "ok"

    mock_fn.assert_called_once()


def test_with_retry_retries_on_429_then_succeeds() -> None:
    mock_fn = MagicMock(side_effect=[_http_status_error(429), "success"])

    with patch("eleven_demo.client.time.sleep") as sleep_mock:
        assert _with_retry(mock_fn) == "success"

    assert mock_fn.call_count == 2
    sleep_mock.assert_called_once()
    assert sleep_mock.call_args is not None
    assert sleep_mock.call_args[0][0] == pytest.approx(1.0)


def test_with_retry_raises_after_three_failed_attempts() -> None:
    mock_fn = MagicMock(
        side_effect=[
            _http_status_error(503),
            _http_status_error(503),
            _http_status_error(503),
        ],
    )

    with (
        patch("eleven_demo.client.time.sleep") as sleep_mock,
        pytest.raises(httpx.HTTPStatusError),
    ):
        _with_retry(mock_fn)

    assert mock_fn.call_count == 3
    assert sleep_mock.call_count == 2
    delays = [call[0][0] for call in sleep_mock.call_args_list]
    assert delays[0] == pytest.approx(1.0)
    assert delays[1] == pytest.approx(2.0)


def test_with_retry_does_not_retry_on_client_error_400() -> None:
    mock_fn = MagicMock(side_effect=_http_status_error(400))

    with (
        patch("eleven_demo.client.time.sleep") as sleep_mock,
        pytest.raises(httpx.HTTPStatusError),
    ):
        _with_retry(mock_fn)

    mock_fn.assert_called_once()
    sleep_mock.assert_not_called()


def _req() -> httpx.Request:
    return httpx.Request("GET", "https://api.elevenlabs.io/v1/ping")


def test_retrying_client_stream_skips_retry_wrapper() -> None:
    client = _RetryingHttpxClient()
    ok = httpx.Response(500, request=_req())

    with patch.object(httpx.Client, "send", return_value=ok) as parent:
        out = client.send(_req(), stream=True)

    assert out is ok
    parent.assert_called_once()


def test_retrying_client_retries_retryable_status_then_ok() -> None:
    client = _RetryingHttpxClient()
    req = _req()
    first = httpx.Response(503, request=req)
    second = httpx.Response(200, request=req)
    bodies: list[httpx.Response] = [first, second]

    def fake_send(self: httpx.Client, request: httpx.Request, **kwargs: object) -> httpx.Response:
        r = bodies.pop(0)
        r.request = request
        return r

    with (
        patch.object(httpx.Client, "send", fake_send),
        patch("eleven_demo.client.time.sleep"),
    ):
        out = client.send(req)

    assert out.status_code == 200


def test_retrying_client_returns_non_retryable_error_without_retry() -> None:
    client = _RetryingHttpxClient()
    req = _req()
    resp = httpx.Response(400, request=req)

    with patch.object(httpx.Client, "send", return_value=resp):
        out = client.send(req)

    assert out.status_code == 400
