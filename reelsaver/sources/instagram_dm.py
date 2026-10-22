import random
import re
import sys
import time
from datetime import datetime
from pathlib import Path

from instagrapi import Client

import config
from reelsaver.models import Share, TextMessage, order_key
from reelsaver.sources.base import ShareSource

SHORTCODE_RE = re.compile(r"/(?:reel|reels)/([A-Za-z0-9_-]+)")


def _field(obj, name):
    if obj is None:
        return None
    if isinstance(obj, dict):
        return obj.get(name)
    return getattr(obj, name, None)


class InstagramDMSource(ShareSource):
    def __init__(self, username: str | None = None, password: str | None = None,
                 session_path: Path | str | None = None):
        self.username = username or config.IG_USERNAME
        self.password = password or config.IG_PASSWORD
        self.session_path = Path(session_path or config.SESSION_PATH)
        self._client: Client | None = None

    def _login(self) -> Client:
        if self._client is not None:
            return self._client

        cl = Client()
        session_loaded = False

        if self.session_path.exists():
            try:
                cl.set_settings(cl.load_settings(self.session_path))
                session_loaded = True
            except (ValueError, OSError) as e:
                print(f"Session file unusable ({type(e).__name__}), ignoring it")

        print("Reusing saved session" if session_loaded else "Doing a fresh login")
        cl.login(self.username, self.password)
        cl.dump_settings(self.session_path)

        self._client = cl
        return cl

    def _get_sender_id(self, client: Client) -> str:
        settings = config.load_app_settings()
        if settings.get("allowed_sender_id"):
            return str(settings["allowed_sender_id"])

        if not sys.stdin.isatty():
            raise RuntimeError(
                "No sender saved and no terminal to ask. "
                "Run this once from a terminal to choose a sender."
            )

        username = input("Instagram username whose DMs should be read: ").strip().lstrip("@").lower()
        if not username:
            raise ValueError("No username entered")

        user_id = str(client.user_id_from_username(username))
        settings["allowed_sender_username"] = username
        settings["allowed_sender_id"] = user_id
        config.save_app_settings(settings)
        print(f"Saved. Only DMs from @{username} will be read from now on.")
        return user_id

    def _fetch(self, label: str, fetch_fn) -> list:
        try:
            threads = fetch_fn(amount=20)
        except Exception as e:
            text = str(e)
            first_line = text.splitlines()[0] if text else ""
            print(f"[{label}] fetch failed: {type(e).__name__}: {first_line}")
            return []
        return [m for t in threads for m in t.messages]

    def _to_share(self, msg) -> Share | None:
        url = _field(_field(msg, "xma_share"), "video_url")

        if not url:
            clips = (_field(msg, "raw_xma") or {}).get("xma_clip") or []
            if clips:
                url = clips[0].get("target_url")

        match = SHORTCODE_RE.search(url or "")
        if not match:
            print(f"Skipping message {msg.id}: no reel link found")
            return None

        code = match.group(1)
        return Share(
            shortcode=code,
            url=f"https://www.instagram.com/reel/{code}/",
            sender_id=str(msg.user_id),
            timestamp=msg.timestamp,
            message_id=str(msg.id),
            thread_id=str(msg.thread_id),
            raw_type=str(msg.item_type),
        )

    def _to_text(self, msg) -> TextMessage | None:
        text = (msg.text or "").strip()
        if not text:
            return None
        return TextMessage(
            message_id=str(msg.id),
            thread_id=str(msg.thread_id),
            sender_id=str(msg.user_id),
            timestamp=msg.timestamp,
            text=text,
        )

    def get_new_messages(self, since: datetime | None = None) -> tuple[list[Share], list[TextMessage]]:
        client = self._login()
        sender_id = self._get_sender_id(client)

        messages = self._fetch("main", client.direct_threads)
        time.sleep(random.uniform(2, 5))
        messages += self._fetch("pending", client.direct_pending_inbox)

        shares: dict[str, Share] = {}
        texts: dict[str, TextMessage] = {}
        for msg in messages:
            if str(msg.user_id) != sender_id:
                continue
            if since is not None and msg.timestamp < since:
                continue

            kind = str(msg.item_type)
            if kind == "xma_clip":
                share = self._to_share(msg)
                if share is not None:
                    shares[share.message_id] = share
            elif kind == "text":
                text = self._to_text(msg)
                if text is not None:
                    texts[text.message_id] = text

        return (sorted(shares.values(), key=order_key),
                sorted(texts.values(), key=order_key))