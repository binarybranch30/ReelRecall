from dataclasses import dataclass
from datetime import datetime


@dataclass
class Share:
    shortcode: str
    url: str
    sender_id: str
    timestamp: datetime
    message_id: str
    thread_id: str
    raw_type: str
    my_caption: str | None = None

@dataclass
class TextMessage:
    message_id: str
    thread_id: str
    sender_id: str
    timestamp: datetime
    text: str


def order_key(item) -> tuple[datetime, int]:
    return (item.timestamp, int(item.message_id))