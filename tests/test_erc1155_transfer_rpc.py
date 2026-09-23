from __future__ import annotations

from collections.abc import Sequence

from polymarket_history.domain.models.log import Log
from polymarket_history.domain.value_objects.address import Address
from polymarket_history.domain.value_objects.block import BlockNumber
from polymarket_history.domain.value_objects.topic import Topic
from polymarket_history.infrastructure.helpers.erc1155_transfer_codec import (
    erc1155_transfer_batch_topic,
    erc1155_transfer_single_topic,
)
from polymarket_history.infrastructure.helpers.topic_codec import address_to_topic
from polymarket_history.infrastructure.repositories.erc1155_transfer_rpc import (
    Erc1155TransferRpcRepository,
)

WALLET = Address("0x46b353667fd7d846af3bbeda6584b0e5b883d3de")
OTHER = Address("0x1111111111111111111111111111111111111111")
OPERATOR = Address("0x2222222222222222222222222222222222222222")
CTF = Address("0x4d97dcd97ec945f40cf65f87097ace5ea0476045")
TX = "0x" + "ab" * 32


def _uint(value: int) -> str:
    return f"{value:064x}"


def _encode_single(token_id: int, amount: int) -> str:
    return "0x" + _uint(token_id) + _uint(amount)


def _encode_batch(pairs: Sequence[tuple[int, int]]) -> str:
    n = len(pairs)
    ids_offset = 64
    values_offset = 64 + 32 + n * 32
    parts = [_uint(ids_offset), _uint(values_offset), _uint(n)]
    parts.extend(_uint(token_id) for token_id, _ in pairs)
    parts.append(_uint(n))
    parts.extend(_uint(amount) for _, amount in pairs)
    return "0x" + "".join(parts)


def _make_log(
    *,
    topic0: Topic,
    sender: Address,
    recipient: Address,
    data: str,
    log_index: int = 7,
    block: int = 100,
) -> Log:
    return Log(
        address=CTF,
        topics=(
            topic0,
            address_to_topic(OPERATOR),
            address_to_topic(sender),
            address_to_topic(recipient),
        ),
        data=data,
        block_number=BlockNumber(block),
        transaction_hash=TX,
        log_index=log_index,
    )


def _topics_match(
    log_topics: Sequence[Topic],
    filter_topics: Sequence[Topic | None],
) -> bool:
    for index, expected in enumerate(filter_topics):
        if expected is None:
            continue
        if index >= len(log_topics) or log_topics[index] != expected:
            return False
    return True


class _FakePolygon:
    def __init__(self, logs: list[Log]) -> None:
        self._logs = logs

    def get_logs(
        self,
        *,
        address: Address | None = None,
        topics: Sequence[Topic | None] | None = None,
        from_block: BlockNumber,
        to_block: BlockNumber,
    ) -> list[Log]:
        del from_block, to_block
        matched: list[Log] = []
        for log in self._logs:
            if address is not None and log.address != address:
                continue
            if topics is not None and not _topics_match(log.topics, topics):
                continue
            matched.append(log)
        return matched


def test_self_transfer_single_is_not_double_counted() -> None:
    log = _make_log(
        topic0=erc1155_transfer_single_topic(),
        sender=WALLET,
        recipient=WALLET,
        data=_encode_single(token_id=42, amount=1_000),
    )
    repo = Erc1155TransferRpcRepository(_FakePolygon([log]))

    transfers = repo.list_for_wallet(
        WALLET,
        CTF,
        BlockNumber(1),
        BlockNumber(200),
        batch_size=1000,
    )

    assert len(transfers) == 1
    assert transfers[0].token_id == 42
    assert transfers[0].amount == 1_000


def test_transfer_batch_duplicate_token_ids_are_summed() -> None:
    log = _make_log(
        topic0=erc1155_transfer_batch_topic(),
        sender=OTHER,
        recipient=WALLET,
        data=_encode_batch([(7, 100), (7, 250), (9, 50)]),
    )
    repo = Erc1155TransferRpcRepository(_FakePolygon([log]))

    transfers = repo.list_for_wallet(
        WALLET,
        CTF,
        BlockNumber(1),
        BlockNumber(200),
        batch_size=1000,
    )

    by_id = {item.token_id: item.amount for item in transfers}
    assert by_id == {7: 350, 9: 50}


def test_self_transfer_batch_with_dup_token_id_sums_once() -> None:
    log = _make_log(
        topic0=erc1155_transfer_batch_topic(),
        sender=WALLET,
        recipient=WALLET,
        data=_encode_batch([(3, 10), (3, 20)]),
    )
    repo = Erc1155TransferRpcRepository(_FakePolygon([log]))

    transfers = repo.list_for_wallet(
        WALLET,
        CTF,
        BlockNumber(1),
        BlockNumber(200),
        batch_size=1000,
    )

    assert len(transfers) == 1
    assert transfers[0].token_id == 3
    assert transfers[0].amount == 30
