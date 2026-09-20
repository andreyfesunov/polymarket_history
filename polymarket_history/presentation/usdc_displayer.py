from __future__ import annotations

from dataclasses import dataclass

from polymarket_history.domain.value_objects.token import Token

_USDC_DECIMALS = 6


@dataclass(frozen=True, slots=True)
class UsdcDisplayer:
    usdc: Token

    def format(self, token: Token, balance: int) -> str | None:
        if token != self.usdc:
            return None
        return f"{balance / 10**_USDC_DECIMALS:.6f}"
