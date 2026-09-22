from __future__ import annotations

from polymarket_history.domain.models.erc20_transfer import Erc20Transfer
from polymarket_history.domain.repositories.polygon import PolygonRepository
from polymarket_history.domain.value_objects.address import Address
from polymarket_history.domain.value_objects.block import BlockNumber
from polymarket_history.domain.value_objects.token import Token
from polymarket_history.infrastructure.helpers.erc20_transfer_codec import (
    decode_erc20_transfer,
    erc20_transfer_topic,
)
from polymarket_history.infrastructure.helpers.topic_codec import address_to_topic


class Erc20TransferRpcRepository:
    def __init__(self, polygon: PolygonRepository) -> None:
        self._polygon = polygon

    def list_for_wallet(
        self,
        wallet: Address,
        token: Address,
        from_block: BlockNumber,
        to_block: BlockNumber,
        batch_size: int,
    ) -> list[Erc20Transfer]:
        if batch_size < 1:
            raise ValueError(f"batch_size must be >= 1, got {batch_size}")
        if from_block.value > to_block.value:
            raise ValueError(
                f"from_block {from_block.value} > to_block {to_block.value}"
            )

        token_id = Token(token)
        wallet_topic = address_to_topic(wallet)
        transfers: dict[tuple[str, int], Erc20Transfer] = {}

        start = from_block.value
        while start <= to_block.value:
            end = min(start + batch_size - 1, to_block.value)
            chunk_from = BlockNumber(start)
            chunk_to = BlockNumber(end)

            outgoing = self._polygon.get_logs(
                address=token,
                topics=[erc20_transfer_topic(), wallet_topic, None],
                from_block=chunk_from,
                to_block=chunk_to,
            )
            incoming = self._polygon.get_logs(
                address=token,
                topics=[erc20_transfer_topic(), None, wallet_topic],
                from_block=chunk_from,
                to_block=chunk_to,
            )

            for log in outgoing + incoming:
                transfer = decode_erc20_transfer(token_id, log)
                transfers[(transfer.transaction_hash, transfer.log_index)] = transfer

            start = end + 1

        return sorted(
            transfers.values(),
            key=lambda item: (item.block.value, item.log_index),
        )
