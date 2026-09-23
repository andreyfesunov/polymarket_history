from __future__ import annotations

import sys
from collections.abc import Sequence

from polymarket_history.application.get_wallet_usdc_history import GetWalletUsdcHistory
from polymarket_history.domain.models.erc20_transfer import Erc20Transfer
from polymarket_history.domain.repositories.transfer_store import TransferStore
from polymarket_history.domain.value_objects.address import Address
from polymarket_history.domain.value_objects.block import BlockNumber


class PersistingGetWalletUsdcHistory:
    def __init__(
        self,
        inner: GetWalletUsdcHistory,
        store: TransferStore,
    ) -> None:
        self._inner = inner
        self._store = store

    def __call__(
        self,
        wallet: Address,
        token: Address,
        from_block: BlockNumber,
        to_block: BlockNumber,
        batch_size: int,
    ) -> list[Erc20Transfer]:
        transfers = self._inner(wallet, token, from_block, to_block, batch_size)
        self._persist(transfers)
        return transfers

    def _persist(self, transfers: Sequence[Erc20Transfer]) -> None:
        try:
            self._store.save_erc20(transfers)
        except Exception as exc:
            print(f"failed to persist erc20 transfers: {exc}", file=sys.stderr)
            raise
