from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from polymarket_history.domain.models.log import Log
from polymarket_history.domain.value_objects.address import Address
from polymarket_history.domain.value_objects.block import (
    LATEST,
    BlockNumber,
    BlockRef,
)
from polymarket_history.domain.value_objects.topic import Topic


class PolygonRepository(Protocol):
    def get_block_number(self) -> BlockNumber: ...

    def get_logs(
        self,
        *,
        address: Address | None = None,
        topics: Sequence[Topic | None] | None = None,
        from_block: BlockNumber,
        to_block: BlockNumber,
    ) -> list[Log]: ...

    def erc20_balance(
        self,
        token: Address,
        owner: Address,
        block: BlockRef = LATEST,
    ) -> int: ...

    def erc1155_balance(
        self,
        token: Address,
        owner: Address,
        token_id: int,
        block: BlockRef = LATEST,
    ) -> int: ...

    def erc1155_balance_of_batch(
        self,
        token: Address,
        owner: Address,
        token_ids: Sequence[int],
        block: BlockRef = LATEST,
    ) -> list[int]: ...
