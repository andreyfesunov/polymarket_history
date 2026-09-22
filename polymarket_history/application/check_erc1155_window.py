from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from polymarket_history.domain.models.erc1155_transfer import Erc1155Transfer
from polymarket_history.domain.repositories.polygon import PolygonRepository
from polymarket_history.domain.value_objects.address import Address
from polymarket_history.domain.value_objects.block import BlockNumber

WalletCtfHistoryFn = Callable[
    [Address, Address, BlockNumber, BlockNumber, int],
    list[Erc1155Transfer],
]


@dataclass(frozen=True, slots=True)
class TokenIdCheckResult:
    token_id: int
    opening_balance: int
    closing_balance: int
    reconstructed_balance: int
    transfer_count: int

    @property
    def matched(self) -> bool:
        return self.reconstructed_balance == self.closing_balance

    @property
    def delta(self) -> int:
        return self.reconstructed_balance - self.closing_balance


@dataclass(frozen=True, slots=True)
class CheckErc1155WindowResult:
    wallet: Address
    token: Address
    from_block: BlockNumber
    to_block: BlockNumber
    transfer_count: int
    positions: tuple[TokenIdCheckResult, ...]

    @property
    def matched(self) -> bool:
        return all(position.matched for position in self.positions)


class CheckErc1155Window:
    def __init__(
        self,
        polygon: PolygonRepository,
        get_wallet_ctf_history: WalletCtfHistoryFn,
    ) -> None:
        self._polygon = polygon
        self._get_wallet_ctf_history = get_wallet_ctf_history

    def __call__(
        self,
        wallet: Address,
        token: Address,
        from_block: BlockNumber,
        to_block: BlockNumber,
        batch_size: int,
    ) -> CheckErc1155WindowResult:
        transfers = self._get_wallet_ctf_history(
            wallet,
            token,
            from_block,
            to_block,
            batch_size,
        )
        token_ids = sorted({transfer.token_id for transfer in transfers})

        opening_by_id: dict[int, int] = {}
        closing_by_id: dict[int, int] = {}
        if token_ids:
            if from_block.value == 0:
                opening_by_id = dict.fromkeys(token_ids, 0)
            else:
                opening_balances = self._polygon.erc1155_balance_of_batch(
                    token,
                    wallet,
                    token_ids,
                    block=BlockNumber(from_block.value - 1),
                )
                opening_by_id = dict(zip(token_ids, opening_balances, strict=True))

            closing_balances = self._polygon.erc1155_balance_of_batch(
                token,
                wallet,
                token_ids,
                block=to_block,
            )
            closing_by_id = dict(zip(token_ids, closing_balances, strict=True))

        reconstructed: dict[int, int] = {
            token_id: opening_by_id[token_id] for token_id in token_ids
        }
        counts: dict[int, int] = dict.fromkeys(token_ids, 0)
        for transfer in transfers:
            counts[transfer.token_id] += 1
            if transfer.recipient == wallet:
                reconstructed[transfer.token_id] += transfer.amount
            if transfer.sender == wallet:
                reconstructed[transfer.token_id] -= transfer.amount

        positions = tuple(
            TokenIdCheckResult(
                token_id=token_id,
                opening_balance=opening_by_id[token_id],
                closing_balance=closing_by_id[token_id],
                reconstructed_balance=reconstructed[token_id],
                transfer_count=counts[token_id],
            )
            for token_id in token_ids
        )

        return CheckErc1155WindowResult(
            wallet=wallet,
            token=token,
            from_block=from_block,
            to_block=to_block,
            transfer_count=len(transfers),
            positions=positions,
        )
