from __future__ import annotations

from dataclasses import replace

from polymarket_history.domain.models.erc1155_transfer import Erc1155Transfer
from polymarket_history.domain.repositories.polygon import PolygonRepository
from polymarket_history.domain.value_objects.address import Address
from polymarket_history.domain.value_objects.block import BlockNumber
from polymarket_history.domain.value_objects.token import Token
from polymarket_history.infrastructure.helpers.erc1155_transfer_codec import (
    decode_erc1155_transfer,
    erc1155_transfer_batch_topic,
    erc1155_transfer_single_topic,
)
from polymarket_history.infrastructure.helpers.topic_codec import address_to_topic


class Erc1155TransferRpcRepository:
    def __init__(self, polygon: PolygonRepository) -> None:
        self._polygon = polygon

    def list_for_wallet(
        self,
        wallet: Address,
        token: Address,
        from_block: BlockNumber,
        to_block: BlockNumber,
        batch_size: int,
    ) -> list[Erc1155Transfer]:
        if batch_size < 1:
            raise ValueError(f"batch_size must be >= 1, got {batch_size}")
        if from_block.value > to_block.value:
            raise ValueError(
                f"from_block {from_block.value} > to_block {to_block.value}"
            )

        token_id = Token(token)
        wallet_topic = address_to_topic(wallet)
        transfers: dict[tuple[str, int, int], Erc1155Transfer] = {}

        single_topic = erc1155_transfer_single_topic()
        batch_topic = erc1155_transfer_batch_topic()

        start = from_block.value
        while start <= to_block.value:
            end = min(start + batch_size - 1, to_block.value)
            chunk_from = BlockNumber(start)
            chunk_to = BlockNumber(end)

            queries = (
                [single_topic, None, wallet_topic, None],
                [single_topic, None, None, wallet_topic],
                [batch_topic, None, wallet_topic, None],
                [batch_topic, None, None, wallet_topic],
            )
            logs = []
            for topics in queries:
                logs.extend(
                    self._polygon.get_logs(
                        address=token,
                        topics=topics,
                        from_block=chunk_from,
                        to_block=chunk_to,
                    )
                )

            for log in logs:
                for transfer in decode_erc1155_transfer(token_id, log):
                    key = (
                        transfer.transaction_hash,
                        transfer.log_index,
                        transfer.token_id,
                    )
                    existing = transfers.get(key)
                    if existing is None:
                        transfers[key] = transfer
                    else:
                        transfers[key] = replace(
                            existing,
                            amount=existing.amount + transfer.amount,
                        )

            start = end + 1

        return sorted(
            transfers.values(),
            key=lambda item: (item.block.value, item.log_index, item.token_id),
        )
