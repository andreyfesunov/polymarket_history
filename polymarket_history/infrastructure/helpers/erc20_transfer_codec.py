from __future__ import annotations

from functools import lru_cache

from Crypto.Hash import keccak
from polymarket_history.domain.models.erc20_transfer import Erc20Transfer
from polymarket_history.domain.models.log import Log
from polymarket_history.domain.value_objects.token import Token
from polymarket_history.domain.value_objects.topic import Topic
from polymarket_history.infrastructure.helpers.topic_codec import topic_to_address

_ERC20_TRANSFER_SIGNATURE = "Transfer(address,address,uint256)"


class Erc20TransferDecodeError(ValueError):
    pass


@lru_cache(maxsize=1)
def erc20_transfer_topic() -> Topic:
    digest = keccak.new(digest_bits=256)
    digest.update(_ERC20_TRANSFER_SIGNATURE.encode("ascii"))
    return Topic("0x" + digest.hexdigest())


def decode_erc20_transfer(token: Token, log: Log) -> Erc20Transfer:
    if len(log.topics) < 3:
        raise Erc20TransferDecodeError(
            f"Transfer log needs 3 topics, got {len(log.topics)}"
        )
    if log.topics[0] != erc20_transfer_topic():
        raise Erc20TransferDecodeError(f"unexpected topic0: {log.topics[0].value}")
    try:
        amount = int(log.data, 16)
    except ValueError as exc:
        raise Erc20TransferDecodeError(f"invalid Transfer data: {log.data!r}") from exc
    return Erc20Transfer(
        token=token,
        block=log.block_number,
        transaction_hash=log.transaction_hash,
        log_index=log.log_index,
        sender=topic_to_address(log.topics[1]),
        recipient=topic_to_address(log.topics[2]),
        amount=amount,
    )
