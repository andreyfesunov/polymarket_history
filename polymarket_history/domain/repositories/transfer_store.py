from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from polymarket_history.domain.models.erc20_transfer import Erc20Transfer
from polymarket_history.domain.models.erc1155_transfer import Erc1155Transfer


class TransferStore(Protocol):
    def save_erc20(self, transfers: Sequence[Erc20Transfer]) -> None: ...

    def save_erc1155(self, transfers: Sequence[Erc1155Transfer]) -> None: ...
