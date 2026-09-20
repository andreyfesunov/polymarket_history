from __future__ import annotations

from typing import Protocol

from polymarket_history.domain.models.erc20_transfer import Erc20Transfer
from polymarket_history.domain.value_objects.address import Address
from polymarket_history.domain.value_objects.block import BlockNumber


class Erc20TransferRepository(Protocol):
    def list_for_wallet(
        self,
        wallet: Address,
        token: Address,
        from_block: BlockNumber,
        to_block: BlockNumber,
        batch_size: int,
    ) -> list[Erc20Transfer]: ...
