from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from typing import Any

from polymarket_history.infrastructure.settings import RpcSettings


class JsonRpcError(RuntimeError):
    pass


class JsonRpcClient:
    def __init__(self, rpc: RpcSettings) -> None:
        self._rpc = rpc

    def call(self, method: str, params: list[Any] | None = None) -> Any:
        body = _encode_request(method, params or [])
        last_error: Exception | None = None
        for attempt in range(self._rpc.max_retries):
            try:
                raw = _post(self._rpc.url, body, self._rpc.timeout)
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
                last_error = exc
                time.sleep(self._rpc.retry_backoff * (2**attempt))
                continue
            return _unwrap_result(raw, method)
        raise JsonRpcError(f"{method} failed after retries: {last_error}")


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
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, dict):
        raise JsonRpcError(f"unexpected JSON-RPC payload: {payload!r}")
    return payload


def _unwrap_result(raw: dict[str, Any], method: str) -> Any:
    if "error" in raw:
        message = raw["error"]
        if isinstance(message, dict):
            message = message.get("message", message)
        raise JsonRpcError(f"{method} failed: {message}")
    if "result" not in raw:
        raise JsonRpcError(f"{method} returned no result: {raw!r}")
    return raw["result"]
