from __future__ import annotations

import io
import time
import urllib.error
from typing import Any
from unittest.mock import MagicMock

import pytest

from polymarket_history.infrastructure.helpers import json_rpc
from polymarket_history.infrastructure.helpers.json_rpc import (
    JsonRpcClient,
    JsonRpcError,
    RateLimitError,
)
from polymarket_history.infrastructure.settings import RpcSettings


def _client(
    *,
    max_retries: int = 5,
    rate_limit: int = 1000,
    rate_limit_period: float = 1.0,
) -> JsonRpcClient:
    return JsonRpcClient(
        RpcSettings(
            url="http://example.invalid/rpc",
            timeout=1.0,
            max_retries=max_retries,
            retry_backoff=0.01,
            rate_limit=rate_limit,
            rate_limit_period=rate_limit_period,
        )
    )


def _http_429(
    body: str = '{"id":1,"jsonrpc":"2.0","error":{"code":-32005,"message":"rate limit exceeded"}}',
    *,
    reset_ms: int | None = None,
) -> urllib.error.HTTPError:
    headers = {"x-tdly-limit": "20", "x-tdly-remaining": "0"}
    if reset_ms is not None:
        headers["x-tdly-reset-timestamp"] = str(reset_ms)
    return urllib.error.HTTPError(
        url="http://example.invalid/rpc",
        code=429,
        msg="Too Many Requests",
        hdrs=headers,  # type: ignore[arg-type]
        fp=io.BytesIO(body.encode()),
    )


def test_retries_http_429_tenderly_then_succeeds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = {"n": 0}
    sleeps: list[float] = []

    def fake_urlopen(_request: object, timeout: float = 0) -> MagicMock:
        del timeout
        calls["n"] += 1
        if calls["n"] < 3:
            raise _http_429(reset_ms=int((time.time() + 0.5) * 1000))
        response = MagicMock()
        response.read.return_value = b'{"jsonrpc":"2.0","id":1,"result":"0xabc"}'
        response.__enter__.return_value = response
        response.__exit__.return_value = False
        return response

    monkeypatch.setattr(json_rpc.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(json_rpc.time, "sleep", sleeps.append)

    assert _client().call("eth_blockNumber") == "0xabc"
    assert calls["n"] == 3
    retry_sleeps = [delay for delay in sleeps if delay >= 0.01]
    assert len(retry_sleeps) == 2
    assert all(delay >= 0.01 for delay in retry_sleeps)


def test_http_429_uses_tdly_reset_timestamp(monkeypatch: pytest.MonkeyPatch) -> None:
    sleeps: list[float] = []
    reset_ms = int((time.time() + 2.5) * 1000)
    calls = {"n": 0}

    def fake_urlopen(_request: object, timeout: float = 0) -> MagicMock:
        del timeout
        calls["n"] += 1
        if calls["n"] == 1:
            raise _http_429(reset_ms=reset_ms)
        response = MagicMock()
        response.read.return_value = b'{"jsonrpc":"2.0","id":1,"result":1}'
        response.__enter__.return_value = response
        response.__exit__.return_value = False
        return response

    monkeypatch.setattr(json_rpc.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(json_rpc.time, "sleep", sleeps.append)

    assert _client().call("eth_chainId") == 1
    retry_sleeps = [delay for delay in sleeps if delay >= 0.01]
    assert len(retry_sleeps) == 1
    assert 2.0 <= retry_sleeps[0] <= 3.0


def test_rate_limit_exhausted_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {"n": 0}

    def fake_urlopen(_request: object, timeout: float = 0) -> MagicMock:
        del timeout
        calls["n"] += 1
        raise _http_429()

    monkeypatch.setattr(json_rpc.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(json_rpc.time, "sleep", lambda _s: None)

    with pytest.raises(RateLimitError, match="rate limit exceeded"):
        _client(max_retries=3).call("eth_getLogs")
    assert calls["n"] == 3


def test_non_rate_limit_jsonrpc_error_raises_immediately(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = {"n": 0}

    def fake_urlopen(_request: object, timeout: float = 0) -> MagicMock:
        del timeout
        calls["n"] += 1
        response = MagicMock()
        response.read.return_value = (
            b'{"jsonrpc":"2.0","id":1,"error":{"code":-32000,"message":"execution reverted"}}'
        )
        response.__enter__.return_value = response
        response.__exit__.return_value = False
        return response

    monkeypatch.setattr(json_rpc.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(json_rpc.time, "sleep", lambda _s: None)

    with pytest.raises(JsonRpcError, match="execution reverted"):
        _client().call("eth_call")
    assert calls["n"] == 1


def test_client_throttles_to_configured_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    stamps: list[float] = []
    mono = {"t": 0.0}

    def fake_mono() -> float:
        return mono["t"]

    def fake_sleep(seconds: float) -> None:
        mono["t"] += seconds

    def fake_urlopen(_request: object, timeout: float = 0) -> MagicMock:
        del timeout
        stamps.append(mono["t"])
        response = MagicMock()
        response.read.return_value = b'{"jsonrpc":"2.0","id":1,"result":"0x1"}'
        response.__enter__.return_value = response
        response.__exit__.return_value = False
        return response

    monkeypatch.setattr(json_rpc.time, "monotonic", fake_mono)
    monkeypatch.setattr(json_rpc.time, "sleep", fake_sleep)
    monkeypatch.setattr(json_rpc.urllib.request, "urlopen", fake_urlopen)

    client = _client(rate_limit=20, rate_limit_period=1.0)
    for _ in range(21):
        client.call("eth_blockNumber")

    assert stamps[0] == 0.0
    assert stamps[1] == pytest.approx(0.05)
    assert stamps[20] == pytest.approx(1.0)