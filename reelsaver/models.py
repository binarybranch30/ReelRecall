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