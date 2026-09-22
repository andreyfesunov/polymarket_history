from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from polymarket_history.domain.models.log import Log
from polymarket_history.domain.value_objects.address import Address
from polymarket_history.domain.value_objects.block import (
    LATEST,
    BlockNumber,
    BlockRef,
    LatestBlock,
)
from polymarket_history.domain.value_objects.topic import Topic
from polymarket_history.infrastructure.helpers.json_rpc import JsonRpcClient
from polymarket_history.infrastructure.settings import RpcSettings

_ERC20_BALANCE_OF = "0x70a08231"
_ERC1155_BALANCE_OF = "0x00fdd58e"
_ERC1155_BALANCE_OF_BATCH = "0x4e1273f4"


class PolygonRpcParseError(ValueError):
    pass


class PolygonRpcRepository:
    def __init__(self, rpc: RpcSettings) -> None:
        self._client = JsonRpcClient(rpc)

    def get_block_number(self) -> BlockNumber:
        raw = self._client.call("eth_blockNumber")
        try:
            return BlockNumber(int(raw, 16))
        except (TypeError, ValueError) as exc:
            raise PolygonRpcParseError(
                f"invalid eth_blockNumber result: {raw!r}"
            ) from exc

    def get_logs(
        self,
        *,
        address: Address | None = None,
        topics: Sequence[Topic | None] | None = None,
        from_block: BlockNumber,
        to_block: BlockNumber,
    ) -> list[Log]:
        raw_logs = self._client.call(
            "eth_getLogs",
            [_logs_filter(address, topics, from_block, to_block)],
        )
        if not isinstance(raw_logs, list):
            raise PolygonRpcParseError(
                f"eth_getLogs must return a list, got {type(raw_logs).__name__}"
            )
        return [parse_log(item) for item in raw_logs]

    def eth_call(
        self,
        to: Address,
        data: str,
        block: BlockRef = LATEST,
    ) -> str:
        raw = self._client.call(
            "eth_call",
            [{"to": to.value, "data": data}, block_param(block)],
        )
        if not isinstance(raw, str):
            raise PolygonRpcParseError(
                f"eth_call must return a hex string, got {type(raw).__name__}"
            )
        return raw

    def erc20_balance(
        self,
        token: Address,
        owner: Address,
        block: BlockRef = LATEST,
    ) -> int:
        raw = self.eth_call(token, encode_erc20_balance_of(owner), block=block)
        try:
            return int(raw, 16)
        except ValueError as exc:
            raise PolygonRpcParseError(f"invalid erc20 balance hex: {raw!r}") from exc

    def erc1155_balance(
        self,
        token: Address,
        owner: Address,
        token_id: int,
        block: BlockRef = LATEST,
    ) -> int:
        raw = self.eth_call(
            token,
            encode_erc1155_balance_of(owner, token_id),
            block=block,
        )
        try:
            return int(raw, 16)
        except ValueError as exc:
            raise PolygonRpcParseError(f"invalid erc1155 balance hex: {raw!r}") from exc

    def erc1155_balance_of_batch(
        self,
        token: Address,
        owner: Address,
        token_ids: Sequence[int],
        block: BlockRef = LATEST,
    ) -> list[int]:
        if not token_ids:
            return []
        raw = self.eth_call(
            token,
            encode_erc1155_balance_of_batch(owner, token_ids),
            block=block,
        )
        return decode_uint256_array(raw)


def block_param(block: BlockRef) -> str:
    if isinstance(block, LatestBlock):
        return "latest"
    return hex(block.value)


def encode_erc20_balance_of(owner: Address) -> str:
    return _ERC20_BALANCE_OF + owner.value[2:].zfill(64)


def encode_erc1155_balance_of(owner: Address, token_id: int) -> str:
    return _ERC1155_BALANCE_OF + owner.value[2:].zfill(64) + format(token_id, "064x")


def encode_erc1155_balance_of_batch(owner: Address, token_ids: Sequence[int]) -> str:
    n = len(token_ids)
    accounts_offset = 64
    ids_offset = 64 + 32 + 32 * n
    owner_word = owner.value[2:].zfill(64)
    body = (
        format(accounts_offset, "064x")
        + format(ids_offset, "064x")
        + format(n, "064x")
        + owner_word * n
        + format(n, "064x")
        + "".join(format(token_id, "064x") for token_id in token_ids)
    )
    return _ERC1155_BALANCE_OF_BATCH + body


def decode_uint256_array(raw: str) -> list[int]:
    if not raw.startswith("0x"):
        raise PolygonRpcParseError(f"expected 0x-prefixed hex, got {raw!r}")
    payload = raw[2:]
    if len(payload) < 128:
        raise PolygonRpcParseError(f"uint256[] result too short: {raw!r}")
    try:
        offset = int(payload[0:64], 16) * 2
        length = int(payload[offset : offset + 64], 16)
        start = offset + 64
        end = start + length * 64
        if end > len(payload):
            raise PolygonRpcParseError(f"uint256[] extends past data: {raw!r}")
        return [int(payload[i : i + 64], 16) for i in range(start, end, 64)]
    except ValueError as exc:
        raise PolygonRpcParseError(f"invalid uint256[] hex: {raw!r}") from exc


def _logs_filter(
    address: Address | None,
    topics: Sequence[Topic | None] | None,
    from_block: BlockNumber,
    to_block: BlockNumber,
) -> dict[str, Any]:
    filter_params: dict[str, Any] = {
        "fromBlock": hex(from_block.value),
        "toBlock": hex(to_block.value),
    }
    if address is not None:
        filter_params["address"] = address.value
    if topics is not None:
        filter_params["topics"] = [
            None if topic is None else topic.value for topic in topics
        ]
    return filter_params


def parse_log(item: object) -> Log:
    if not isinstance(item, dict):
        raise PolygonRpcParseError(f"log must be an object, got {type(item).__name__}")
    try:
        raw_topics = item["topics"]
        if not isinstance(raw_topics, list):
            raise PolygonRpcParseError(
                f"log.topics must be a list, got {type(raw_topics).__name__}"
            )
        return Log(
            address=Address(str(item["address"])),
            topics=tuple(Topic(str(topic)) for topic in raw_topics),
            data=str(item["data"]),
            block_number=BlockNumber(int(item["blockNumber"], 16)),
            transaction_hash=str(item["transactionHash"]),
            log_index=int(item["logIndex"], 16),
        )
    except KeyError as exc:
        raise PolygonRpcParseError(f"log missing field: {exc.args[0]}") from exc
    except (TypeError, ValueError) as exc:
        raise PolygonRpcParseError(f"invalid log payload: {exc}") from exc
