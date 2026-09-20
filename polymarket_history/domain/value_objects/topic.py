from __future__ import annotations

import re
from dataclasses import dataclass

_TOPIC_RE = re.compile(r"^0x[0-9a-f]{64}$")


@dataclass(frozen=True, slots=True)
class Topic:
    value: str

    def __post_init__(self) -> None:
        normalized = self.value.lower()
        if not _TOPIC_RE.fullmatch(normalized):
            raise ValueError(f"invalid topic: {self.value}")
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value
