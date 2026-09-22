from __future__ import annotations

import sys

import psycopg
from polymarket_history.domain.repositories.transfer_store import TransferStore
from polymarket_history.infrastructure.repositories.null_transfer_store import (
    NullTransferStore,
)
from polymarket_history.infrastructure.repositories.postgres_transfer_store import (
    PostgresTransferStore,
)


def build_transfer_store(dsn: str) -> TransferStore:
    cleaned = dsn.strip()
    if not cleaned:
        print(
            "database.dsn is empty; transfers will not be saved to the database",
            file=sys.stderr,
        )
        return NullTransferStore()

    try:
        with (
            psycopg.connect(cleaned, connect_timeout=3) as conn,
            conn.cursor() as cur,
        ):
            cur.execute("SELECT 1")
    except psycopg.Error as exc:
        print(
            f"database unavailable ({exc}); "
            "transfers will not be saved to the database",
            file=sys.stderr,
        )
        return NullTransferStore()

    return PostgresTransferStore(cleaned)
