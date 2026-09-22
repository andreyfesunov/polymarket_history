from __future__ import annotations

import sys
from collections.abc import Sequence

from polymarket_history.application.get_wallet_ctf_history import GetWalletCtfHistory
from polymarket_history.domain.models.erc1155_transfer import Erc1155Transfer
from polymarket_history.domain.repositories.transfer_store import TransferStore
from polymarket_history.domain.value_objects.address import Address
from polymarket_history.domain.value_objects.block import BlockNumber


class PersistingGetWalletCtfHistory:
    def __init__(
        self,
        inner: GetWalletCtfHistory,
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
    ) -> list[Erc1155Transfer]:
        transfers = self._inner(wallet, token, from_block, to_block, batch_size)
        self._persist(transfers)
        return transfers

    def _persist(self, transfers: Sequence[Erc1155Transfer]) -> None:
        try:
            self._store.save_erc1155(transfers)
        except Exception as exc:
            print(f"failed to persist erc1155 transfers: {exc}", file=sys.stderr)
