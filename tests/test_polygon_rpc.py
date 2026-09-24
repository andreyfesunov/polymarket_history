from __future__ import annotations

import pytest
from polymarket_history.domain.value_objects.address import Address
from polymarket_history.domain.value_objects.block import BlockNumber
from polymarket_history.infrastructure.repositories.polygon_rpc import (
    PolygonRpcParseError,
    PolygonRpcRepository,
    parse_uint256_hex,
)
from polymarket_history.infrastructure.settings import RpcSettings

TOKEN = Address("0x1111111111111111111111111111111111111111")
OWNER = Address("0x2222222222222222222222222222222222222222")


def _repo() -> PolygonRpcRepository:
    return PolygonRpcRepository(RpcSettings(url="http://example.invalid/rpc"))


def test_parse_uint256_hex_empty_return_is_zero() -> None:
    assert parse_uint256_hex("0x", label="erc20 balance") == 0
    assert parse_uint256_hex("0X", label="erc20 balance") == 0


def test_parse_uint256_hex_normal_value() -> None:
    assert parse_uint256_hex("0x0a", label="erc20 balance") == 10
    assert parse_uint256_hex("0x" + "00" * 31 + "2a", label="erc20 balance") == 42


def test_parse_uint256_hex_invalid_raises() -> None:
    with pytest.raises(PolygonRpcParseError, match="invalid erc20 balance hex"):
        parse_uint256_hex("0xzz", label="erc20 balance")


def test_erc20_balance_empty_call_result_is_zero(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = _repo()
    monkeypatch.setattr(repo, "eth_call", lambda *args, **kwargs: "0x")

    assert repo.erc20_balance(TOKEN, OWNER, block=BlockNumber(1)) == 0


def test_erc1155_balance_empty_call_result_is_zero(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = _repo()
    monkeypatch.setattr(repo, "eth_call", lambda *args, **kwargs: "0x")

    assert repo.erc1155_balance(TOKEN, OWNER, token_id=7, block=BlockNumber(1)) == 0
