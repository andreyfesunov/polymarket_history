from __future__ import annotations

from functools import lru_cache

from Crypto.Hash import keccak
from polymarket_history.domain.models.erc1155_transfer import Erc1155Transfer
from polymarket_history.domain.models.log import Log
from polymarket_history.domain.value_objects.token import Token
from polymarket_history.domain.value_objects.topic import Topic
from polymarket_history.infrastructure.helpers.topic_codec import topic_to_address

_TRANSFER_SINGLE_SIGNATURE = "TransferSingle(address,address,address,uint256,uint256)"
_TRANSFER_BATCH_SIGNATURE = "TransferBatch(address,address,address,uint256[],uint256[])"


class Erc1155TransferDecodeError(ValueError):
    pass


@lru_cache(maxsize=1)
def erc1155_transfer_single_topic() -> Topic:
    digest = keccak.new(digest_bits=256)
    digest.update(_TRANSFER_SINGLE_SIGNATURE.encode("ascii"))
    return Topic("0x" + digest.hexdigest())


@lru_cache(maxsize=1)
def erc1155_transfer_batch_topic() -> Topic:
    digest = keccak.new(digest_bits=256)
    digest.update(_TRANSFER_BATCH_SIGNATURE.encode("ascii"))
    return Topic("0x" + digest.hexdigest())


def decode_erc1155_transfer(token: Token, log: Log) -> list[Erc1155Transfer]:
    if len(log.topics) < 4:
        raise Erc1155TransferDecodeError(
            f"ERC-1155 transfer log needs 4 topics, got {len(log.topics)}"
        )
    topic0 = log.topics[0]
    operator = topic_to_address(log.topics[1])
    sender = topic_to_address(log.topics[2])
    recipient = topic_to_address(log.topics[3])

    if topic0 == erc1155_transfer_single_topic():
        token_id, amount = _decode_single_data(log.data)
        return [
            Erc1155Transfer(
                token=token,
                token_id=token_id,
                block=log.block_number,
                transaction_hash=log.transaction_hash,
                log_index=log.log_index,
                operator=operator,
                sender=sender,
                recipient=recipient,
                amount=amount,
            )
        ]

    if topic0 == erc1155_transfer_batch_topic():
        pairs = _decode_batch_data(log.data)
        return [
            Erc1155Transfer(
                token=token,
                token_id=token_id,
                block=log.block_number,
                transaction_hash=log.transaction_hash,
                log_index=log.log_index,
                operator=operator,
                sender=sender,
                recipient=recipient,
                amount=amount,
            )
            for token_id, amount in pairs
        ]

    raise Erc1155TransferDecodeError(f"unexpected topic0: {topic0.value}")


def _decode_single_data(data: str) -> tuple[int, int]:
    payload = _hex_payload(data)
    if len(payload) != 128:
        raise Erc1155TransferDecodeError(
            f"TransferSingle data must be 128 hex chars, got {len(payload)}"
        )
    try:
        token_id = int(payload[0:64], 16)
        amount = int(payload[64:128], 16)
    except ValueError as exc:
        raise Erc1155TransferDecodeError(
            f"invalid TransferSingle data: {data!r}"
        ) from exc
    return token_id, amount


def _decode_batch_data(data: str) -> list[tuple[int, int]]:
    payload = _hex_payload(data)
    if len(payload) < 128:
        raise Erc1155TransferDecodeError(
            f"TransferBatch data too short: {len(payload)} hex chars"
        )
    try:
        ids_offset = int(payload[0:64], 16) * 2
        values_offset = int(payload[64:128], 16) * 2
        ids = _decode_uint256_array(payload, ids_offset)
        values = _decode_uint256_array(payload, values_offset)
    except (ValueError, IndexError) as exc:
        raise Erc1155TransferDecodeError(
            f"invalid TransferBatch data: {data!r}"
        ) from exc
    if len(ids) != len(values):
        raise Erc1155TransferDecodeError(
            f"TransferBatch ids/values length mismatch: {len(ids)} vs {len(values)}"
        )
    return list(zip(ids, values, strict=True))


def _decode_uint256_array(payload: str, offset: int) -> list[int]:
    if offset < 0 or offset + 64 > len(payload):
        raise IndexError(f"array offset out of range: {offset}")
    length = int(payload[offset : offset + 64], 16)
    start = offset + 64
    end = start + length * 64
    if end > len(payload):
        raise IndexError(f"array extends past data: need {end}, have {len(payload)}")
    return [int(payload[i : i + 64], 16) for i in range(start, end, 64)]


def _hex_payload(data: str) -> str:
    if not data.startswith("0x"):
        raise Erc1155TransferDecodeError(f"expected 0x-prefixed hex, got {data!r}")
    payload = data[2:]
    if len(payload) % 2 != 0:
        raise Erc1155TransferDecodeError(f"odd-length hex data: {data!r}")
    return payload
