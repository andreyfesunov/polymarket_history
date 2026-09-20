from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BlockNumber:
    value: int

    def __post_init__(self) -> None:
        if self.value < 0:
            raise ValueError(f"invalid block number: {self.value}")

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True, slots=True)
class LatestBlock:
    pass


LATEST = LatestBlock()

BlockRef = BlockNumber | LatestBlock
