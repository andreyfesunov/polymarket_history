from __future__ import annotations

from dataclasses import dataclass

from polymarket_history.domain.repositories.polygon import PolygonRepository
from polymarket_history.domain.value_objects.address import Address
from polymarket_history.domain.value_objects.block import (
    LATEST,
    BlockNumber,
    BlockRef,
    LatestBlock,
)
from polymarket_history.domain.value_objects.token import Token


@dataclass(frozen=True, slots=True)
class Erc1155BalanceResult:
    token: Token
    token_id: int
    block: BlockNumber
    balance: int


class GetErc1155Balance:
    def __init__(self, repository: PolygonRepository) -> None:
        self._repository = repository

    def __call__(
        self,
        token: Address,
        owner: Address,
        token_id: int,
        block: BlockRef = LATEST,
    ) -> Erc1155BalanceResult:
        tip = self._repository.get_block_number()
        resolved = tip if isinstance(block, LatestBlock) else block
        balance = self._repository.erc1155_balance(
            token,
            owner,
            token_id,
            block=resolved,
        )
        return Erc1155BalanceResult(
            token=Token(token),
            token_id=token_id,
            block=resolved,
            balance=balance,
        )
