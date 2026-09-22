from __future__ import annotations

from polymarket_history.domain.value_objects.address import Address
from polymarket_history.domain.value_objects.topic import Topic


def address_to_topic(address: Address) -> Topic:
    return Topic("0x" + address.value[2:].zfill(64))


def topic_to_address(topic: Topic) -> Address:
    return Address("0x" + topic.value[-40:])
