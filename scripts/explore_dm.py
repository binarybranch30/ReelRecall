import json
import random
import sys
import time
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config
from instagrapi import Client

SHARE_FIELDS = ("clip", "media_share", "reel_share", "felix_share", "xma_media_share", "link")


def get_client() -> Client:
    cl = Client()
    session_loaded = False

    if config.SESSION_PATH.exists():
        try:
            settings = cl.load_settings(config.SESSION_PATH)
            cl.set_settings(settings)
            session_loaded = True
        except (ValueError, OSError) as e:
            print(f"Session file unusable ({type(e).__name__}), ignoring it")

    print("Reusing saved session" if session_loaded else "Doing a fresh login")
    cl.login(config.IG_USERNAME, config.IG_PASSWORD)
    cl.dump_settings(config.SESSION_PATH)
    return cl


def get_allowed_sender(cl: Client) -> str:
    settings = config.load_app_settings()
    if settings.get("allowed_sender_id"):
        return str(settings["allowed_sender_id"])

    username = input("Instagram username whose DMs should be read: ").strip().lstrip("@").lower()
    if not username:
        raise ValueError("No username entered")

    user_id = str(cl.user_id_from_username(username))
    settings["allowed_sender_username"] = username
    settings["allowed_sender_id"] = user_id
    config.save_app_settings(settings)
    print(f"Saved. Only DMs from @{username} will be read from now on.")
    return user_id


def find_share(msg):
    for name in SHARE_FIELDS:
        value = getattr(msg, name, None)
        if value is not None:
            code = getattr(value, "code", None)
            if code is None and isinstance(value, dict):
                code = value.get("code")
            return name, code
    return None, None


def collect_messages(label: str, fetch_fn, allowed_id: str) -> list:
    try:
        threads = fetch_fn(amount=20)
    except Exception as e:
        text = str(e)
        first_line = text.splitlines()[0] if text else ""
        print(f"[{label}] fetch failed: {type(e).__name__}: {first_line}")
        return []

    messages = [m for t in threads for m in t.messages if str(m.user_id) == allowed_id]
    print(f"[{label}] {len(threads)} threads, {len(messages)} messages from the allowed sender")
    return messages


def print_message(msg) -> None:
    field, code = find_share(msg)
    print(f"  type={msg.item_type} time={msg.timestamp} sender={msg.user_id} "
          f"text={msg.text!r} share_field={field} shortcode={code}")


def main() -> None:
    try:
        client = get_client()
        allowed_id = get_allowed_sender(client)

        messages = collect_messages("main", client.direct_threads, allowed_id)
        time.sleep(random.uniform(2, 5))
        messages += collect_messages("pending", client.direct_pending_inbox, allowed_id)
    except Exception as e:
        print(f"Failed: {type(e).__name__}: {e}")
        traceback.print_exc()
        sys.exit(1)

    messages.sort(key=lambda m: m.timestamp)
    for m in messages:
        print_message(m)

    sample = next((m for m in messages if find_share(m)[0]), None)
    if sample is None:
        print("No share-like message found")
        return

    raw = sample.model_dump() if hasattr(sample, "model_dump") else sample.dict()
    print("--- raw share message ---")
    print(json.dumps(raw, indent=2, default=str))


if __name__ == "__main__":
    main()