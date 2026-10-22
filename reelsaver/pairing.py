from dataclasses import replace
from datetime import timedelta

from reelsaver.models import Share, TextMessage, order_key

PAIRING_WINDOW = timedelta(seconds=60)
MAX_TEXTS_PER_REEL = 5
CAPTION_SEPARATOR = "\n"


def pair(shares: list[Share], texts: list[TextMessage],
         window: timedelta = PAIRING_WINDOW,
         max_texts: int = MAX_TEXTS_PER_REEL) -> list[Share]:
    events = sorted([*shares, *texts], key=order_key)

    latest_reel: dict[str, Share] = {}
    collected: dict[str, list[str]] = {}

    for item in events:
        if isinstance(item, Share):
            latest_reel[item.thread_id] = item
            collected[item.message_id] = []
            continue

        reel = latest_reel.get(item.thread_id)
        if reel is None:
            continue
        if item.timestamp - reel.timestamp > window:
            continue
        parts = collected[reel.message_id]
        if len(parts) >= max_texts:
            continue
        parts.append(item.text)

    result = []
    for share in sorted(shares, key=order_key):
        parts = collected[share.message_id]
        caption = CAPTION_SEPARATOR.join(parts) if parts else None
        result.append(replace(share, my_caption=caption))
    return result