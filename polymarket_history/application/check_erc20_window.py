from __future__ import annotations

from dataclasses import dataclass

from polymarket_history.application.get_erc20_balance import GetErc20Balance
from polymarket_history.application.get_wallet_usdc_history import GetWalletUsdcHistory
from polymarket_history.domain.value_objects.address import Address
from polymarket_history.domain.value_objects.block import BlockNumber


@dataclass(frozen=True, slots=True)
class CheckWindowResult:
    wallet: Address
    token: Address
    from_block: BlockNumber
    to_block: BlockNumber
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


class CheckErc20Window:
    def __init__(
        self,
        get_erc20_balance: GetErc20Balance,
        get_wallet_usdc_history: GetWalletUsdcHistory,
    ) -> None:
        self._get_erc20_balance = get_erc20_balance
        self._get_wallet_usdc_history = get_wallet_usdc_history

    def __call__(
        self,
        wallet: Address,
        token: Address,
        from_block: BlockNumber,
        to_block: BlockNumber,
        batch_size: int,
    ) -> CheckWindowResult:
        if from_block.value == 0:
            opening_balance = 0
        else:
            opening_balance = self._get_erc20_balance(
                token,
                wallet,
                block=BlockNumber(from_block.value - 1),
            ).balance

        transfers = self._get_wallet_usdc_history(
            wallet,
            token,
            from_block,
            to_block,
            batch_size,
        )
        reconstructed = opening_balance
        for transfer in transfers:
            if transfer.recipient == wallet:
                reconstructed += transfer.amount
            if transfer.sender == wallet:
                reconstructed -= transfer.amount

        closing_balance = self._get_erc20_balance(
            token,
            wallet,
            block=to_block,
        ).balance

        return CheckWindowResult(
            wallet=wallet,
            token=token,
            from_block=from_block,
            to_block=to_block,
            opening_balance=opening_balance,
            closing_balance=closing_balance,
            reconstructed_balance=reconstructed,
            transfer_count=len(transfers),
        )
