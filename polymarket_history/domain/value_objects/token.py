from __future__ import annotations

from dataclasses import dataclass

from polymarket_history.domain.value_objects.address import Address


@dataclass(frozen=True, slots=True)
class Token:
    address: Address

    def __str__(self) -> str:
        return self.address.value
