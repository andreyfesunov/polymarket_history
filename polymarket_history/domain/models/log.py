from __future__ import annotations

from dataclasses import dataclass

from polymarket_history.domain.value_objects.address import Address
from polymarket_history.domain.value_objects.block import BlockNumber
from polymarket_history.domain.value_objects.topic import Topic


@dataclass(frozen=True, slots=True)
class Log:
    address: Address
    topics: tuple[Topic, ...]
    data: str
    block_number: BlockNumber
    transaction_hash: str
    log_index: int
