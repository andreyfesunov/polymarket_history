from __future__ import annotations

from polymarket_history.domain.models.erc1155_transfer import Erc1155Transfer
from polymarket_history.domain.repositories.erc1155_transfer import (
    Erc1155TransferRepository,
)
from polymarket_history.domain.value_objects.address import Address
from polymarket_history.domain.value_objects.block import BlockNumber


class GetWalletCtfHistory:
    def __init__(self, repository: Erc1155TransferRepository) -> None:
        self._repository = repository

    def __call__(
        self,
        wallet: Address,
        token: Address,
        from_block: BlockNumber,
        to_block: BlockNumber,
        batch_size: int,
    ) -> list[Erc1155Transfer]:
        return self._repository.list_for_wallet(
            wallet,
            token,
            from_block,
            to_block,
            batch_size,
        )
