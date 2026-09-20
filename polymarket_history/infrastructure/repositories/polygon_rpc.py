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


def block_param(block: BlockRef) -> str:
    if isinstance(block, LatestBlock):
        return "latest"
    return hex(block.value)


def encode_erc20_balance_of(owner: Address) -> str:
    return _ERC20_BALANCE_OF + owner.value[2:].zfill(64)


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
