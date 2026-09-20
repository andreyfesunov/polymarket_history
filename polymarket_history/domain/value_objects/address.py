from __future__ import annotations

import re
from dataclasses import dataclass

_ADDRESS_RE = re.compile(r"^0x[0-9a-f]{40}$")


@dataclass(frozen=True, slots=True)
class Address:
    value: str

    def __post_init__(self) -> None:
        normalized = self.value.lower()
        if not _ADDRESS_RE.fullmatch(normalized):
            raise ValueError(f"invalid address: {self.value}")
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value
