import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from reelsaver.models import Share

SCHEMA = """
CREATE TABLE IF NOT EXISTS reels (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    shortcode   TEXT NOT NULL UNIQUE,   -- Instagram's reel id: one row per reel
    url         TEXT NOT NULL,
    sender_id   TEXT NOT NULL,          -- ids are TEXT: they are bigger than 64 bits
    message_id  TEXT NOT NULL,
    thread_id   TEXT NOT NULL,
    posted_at   TEXT NOT NULL,          -- UTC, like 2026-10-18T09:09:24+00:00
    my_caption  TEXT,                   -- NULL until a caption is paired
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_reels_posted_at ON reels (posted_at);
"""


def _now_text() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _to_utc_text(local_time: datetime) -> str:
    return local_time.astimezone(timezone.utc).isoformat(timespec="seconds")


def _from_utc_text(text: str) -> datetime:
    return datetime.fromisoformat(text).astimezone().replace(tzinfo=None)


def connect(path: Path | str | None = None) -> sqlite3.Connection:
    if path is None:
        import config   
        path = config.DB_PATH
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row  
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)


def upsert_share(conn: sqlite3.Connection, share: Share) -> None:
    now = _now_text()
    with conn:   # commits if everything works, rolls back if anything fails
        conn.execute(
            """
            INSERT INTO reels
                (shortcode, url, sender_id, message_id, thread_id, posted_at,
                 my_caption, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(shortcode) DO UPDATE SET
                my_caption = COALESCE(excluded.my_caption, reels.my_caption),
                updated_at = excluded.updated_at
            """,
            (
                share.shortcode, share.url, share.sender_id, share.message_id,
                share.thread_id, _to_utc_text(share.timestamp),
                share.my_caption, now, now,
            ),
        )


def get_reel(conn: sqlite3.Connection, shortcode: str) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT * FROM reels WHERE shortcode = ?", (shortcode,)
    ).fetchone()


def get_resume_point(conn: sqlite3.Connection) -> datetime | None:
    row = conn.execute("SELECT MAX(posted_at) AS latest FROM reels").fetchone()
    if row is None or row["latest"] is None:
        return None
    return _from_utc_text(row["latest"])