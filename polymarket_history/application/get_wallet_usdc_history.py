from __future__ import annotations

from polymarket_history.domain.models.erc20_transfer import Erc20Transfer
from polymarket_history.domain.repositories.erc20_transfer import (
    Erc20TransferRepository,
)
from polymarket_history.domain.value_objects.address import Address
from polymarket_history.domain.value_objects.block import BlockNumber


class GetWalletUsdcHistory:
    def __init__(self, repository: Erc20TransferRepository) -> None:
        self._repository = repository

    def __call__(
        self,
        wallet: Address,
        token: Address,
        from_block: BlockNumber,
        to_block: BlockNumber,
        batch_size: int,
    ) -> list[Erc20Transfer]:
        return self._repository.list_for_wallet(
            wallet,
            token,
            from_block,
            to_block,
            batch_size,
        )
