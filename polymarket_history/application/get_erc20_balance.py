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
class Erc20BalanceResult:
    token: Token
    block: BlockNumber
    balance: int


class GetErc20Balance:
    def __init__(self, repository: PolygonRepository) -> None:
        self._repository = repository

    def __call__(
        self,
        token: Address,
        owner: Address,
        block: BlockRef = LATEST,
    ) -> Erc20BalanceResult:
        tip = self._repository.get_block_number()
        resolved = tip if isinstance(block, LatestBlock) else block
        balance = self._repository.erc20_balance(token, owner, block=resolved)
        return Erc20BalanceResult(
            token=Token(token),
            block=resolved,
            balance=balance,
        )
