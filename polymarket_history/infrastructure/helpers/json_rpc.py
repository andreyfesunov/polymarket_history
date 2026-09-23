from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from threading import Lock
from typing import Any

from polymarket_history.infrastructure.settings import RpcSettings

_TENDERLY_RATE_LIMIT_CODE = -32005
_TENDERLY_RATE_LIMIT_MESSAGE = "rate limit exceeded"
_MAX_RETRY_AFTER = 60.0


class JsonRpcError(RuntimeError):
    pass


class RateLimitError(JsonRpcError):
    def __init__(self, message: str, *, retry_after: float | None = None) -> None:
        super().__init__(message)
        self.retry_after = retry_after


class JsonRpcClient:
    def __init__(self, rpc: RpcSettings) -> None:
        self._rpc = rpc
        self._limiter = _RateLimiter(rpc.rate_limit, rpc.rate_limit_period)

    def call(self, method: str, params: list[Any] | None = None) -> Any:
        body = _encode_request(method, params or [])
        last_error: Exception | None = None
        for attempt in range(self._rpc.max_retries):
            self._limiter.acquire()
            try:
                raw = _post(self._rpc.url, body, self._rpc.timeout)
            except RateLimitError as exc:
                last_error = exc
                if attempt + 1 >= self._rpc.max_retries:
                    raise
                time.sleep(_retry_delay(exc, attempt, self._rpc.retry_backoff))
                continue
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
                last_error = exc
                time.sleep(self._rpc.retry_backoff * (2**attempt))
                continue
            if "error" in raw and _is_tenderly_rate_limit(raw["error"]):
                last_error = RateLimitError(
                    f"{method} failed: {_error_message(raw['error'])}"
                )
                if attempt + 1 >= self._rpc.max_retries:
                    raise last_error
                time.sleep(_retry_delay(last_error, attempt, self._rpc.retry_backoff))
                continue
            return _unwrap_result(raw, method)
        raise JsonRpcError(f"{method} failed after retries: {last_error}")


class _RateLimiter:
    def __init__(self, limit: int, period: float) -> None:
        if limit < 1:
            raise ValueError(f"rate_limit must be >= 1, got {limit}")
        if period <= 0:
            raise ValueError(f"rate_limit_period must be > 0, got {period}")
        self._min_interval = period / limit
        self._lock = Lock()
        self._next_at = 0.0

    def acquire(self) -> None:
        with self._lock:
            now = time.monotonic()
            scheduled = max(now, self._next_at)
            self._next_at = scheduled + self._min_interval
            delay = scheduled - now
        if delay > 0:
            time.sleep(delay)


def _encode_request(method: str, params: list[Any]) -> bytes:
    return json.dumps(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params,
        }
    ).encode("utf-8")


def _post(url: str, body: bytes, timeout: float) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raw_body = exc.read().decode("utf-8", errors="replace")
        if exc.code == 429:
            raise _rate_limit_from_http(raw_body, dict(exc.headers)) from exc
        raise
    if not isinstance(payload, dict):
        raise JsonRpcError(f"unexpected JSON-RPC payload: {payload!r}")
    return payload


def _rate_limit_from_http(raw_body: str, headers: dict[str, str]) -> RateLimitError:
    message = _TENDERLY_RATE_LIMIT_MESSAGE
    try:
        payload = json.loads(raw_body)
    except json.JSONDecodeError:
        payload = None
    if isinstance(payload, dict) and "error" in payload:
        message = str(_error_message(payload["error"]))
    return RateLimitError(
        f"rate limited: {message}",
        retry_after=_retry_after_from_headers(headers),
    )


def _retry_after_from_headers(headers: dict[str, str]) -> float | None:
    raw = headers.get("x-tdly-reset-timestamp") or headers.get("X-Tdly-Reset-Timestamp")
    if raw is None:
        return None
    try:
        reset = int(raw)
    except ValueError:
        return None
    reset_s = reset / 1000.0 if reset > 10_000_000_000 else float(reset)
    wait = reset_s - time.time()
    if wait < 0:
        return 0.0
    return min(wait, _MAX_RETRY_AFTER)


def _retry_delay(exc: RateLimitError, attempt: int, backoff: float) -> float:
    if exc.retry_after is not None:
        return max(exc.retry_after, backoff)
    return backoff * (2**attempt)


def _unwrap_result(raw: dict[str, Any], method: str) -> Any:
    if "error" in raw:
        raise JsonRpcError(f"{method} failed: {_error_message(raw['error'])}")
    if "result" not in raw:
        raise JsonRpcError(f"{method} returned no result: {raw!r}")
    return raw["result"]


def _error_message(error: Any) -> Any:
    if isinstance(error, dict):
        return error.get("message", error)
    return error


def _is_tenderly_rate_limit(error: Any) -> bool:
    if not isinstance(error, dict):
        return False
    if error.get("code") == _TENDERLY_RATE_LIMIT_CODE:
        return True
    message = str(error.get("message", "")).lower()
    return _TENDERLY_RATE_LIMIT_MESSAGE in message
