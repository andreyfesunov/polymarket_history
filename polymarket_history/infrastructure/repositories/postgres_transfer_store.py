from __future__ import annotations

from collections.abc import Sequence

import psycopg
from polymarket_history.domain.models.erc20_transfer import Erc20Transfer
from polymarket_history.domain.models.erc1155_transfer import Erc1155Transfer

_INSERT_ERC20 = """
INSERT INTO erc20_transfers (
    token, block_number, transaction_hash, log_index,
    sender, recipient, amount
) VALUES (%s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (token, transaction_hash, log_index) DO NOTHING
"""

_INSERT_ERC1155 = """
INSERT INTO erc1155_transfers (
    contract, token_id, block_number, transaction_hash, log_index,
    operator, sender, recipient, amount
) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (contract, transaction_hash, log_index, token_id) DO NOTHING
"""


class PostgresTransferStore:
    def __init__(self, dsn: str) -> None:
        self._dsn = dsn

    def save_erc20(self, transfers: Sequence[Erc20Transfer]) -> None:
        if not transfers:
            return
        rows = [
            (
                str(transfer.token),
                transfer.block.value,
                transfer.transaction_hash,
                transfer.log_index,
                str(transfer.sender),
                str(transfer.recipient),
                transfer.amount,
            )
            for transfer in transfers
        ]
        with psycopg.connect(self._dsn) as conn, conn.cursor() as cur:
            cur.executemany(_INSERT_ERC20, rows)
            conn.commit()

    def save_erc1155(self, transfers: Sequence[Erc1155Transfer]) -> None:
        if not transfers:
            return
        rows = [
            (
                str(transfer.token),
                transfer.token_id,
                transfer.block.value,
                transfer.transaction_hash,
                transfer.log_index,
                str(transfer.operator),
                str(transfer.sender),
                str(transfer.recipient),
                transfer.amount,
            )
            for transfer in transfers
        ]
        with psycopg.connect(self._dsn) as conn, conn.cursor() as cur:
            cur.executemany(_INSERT_ERC1155, rows)
            conn.commit()
