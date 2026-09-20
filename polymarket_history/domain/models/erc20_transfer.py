from __future__ import annotations

from dataclasses import dataclass

from polymarket_history.domain.value_objects.address import Address
from polymarket_history.domain.value_objects.block import BlockNumber
from polymarket_history.domain.value_objects.token import Token


@dataclass(frozen=True, slots=True)
class Erc20Transfer:
    token: Token
    block: BlockNumber
    transaction_hash: str
    log_index: int
    sender: Address
    recipient: Address
    amount: int
