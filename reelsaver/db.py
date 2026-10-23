import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from reelsaver.models import Share

SCHEMA = """
CREATE TABLE IF NOT EXISTS reels (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    shortcode   TEXT NOT NULL UNIQUE,
    url         TEXT NOT NULL,
    sender_id   TEXT NOT NULL,
    message_id  TEXT NOT NULL,
    thread_id   TEXT NOT NULL,
    posted_at   TEXT NOT NULL,
    my_caption  TEXT,
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_reels_posted_at ON reels (posted_at);
"""

_UPSERT_SQL = """
    INSERT INTO reels
        (shortcode, url, sender_id, message_id, thread_id, posted_at,
         my_caption, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(shortcode) DO UPDATE SET
        my_caption = COALESCE(excluded.my_caption, reels.my_caption),
        updated_at = excluded.updated_at
"""


def _now_text() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _to_utc_text(local_time: datetime) -> str:
    # A datetime with no timezone is treated as this computer's local time.
    return local_time.astimezone(timezone.utc).isoformat(timespec="seconds")


def _from_utc_text(text: str) -> datetime:
    # Back to the plain local-time datetime the Instagram source uses.
    return datetime.fromisoformat(text).astimezone().replace(tzinfo=None)


def connect(path: Path | str | None = None) -> sqlite3.Connection:
    """Open the database (default: data/reels.db). Use ":memory:" for tests."""
    if path is None:
        import config   # imported here so tests don't need a .env file
        path = config.DB_PATH
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)


def save_shares(conn: sqlite3.Connection, shares: list[Share]) -> int:
    """Save all reels in ONE transaction: either every reel is saved or none is."""
    now = _now_text()
    with conn:
        for share in shares:
            conn.execute(_UPSERT_SQL, (
                share.shortcode, share.url, share.sender_id, share.message_id,
                share.thread_id, _to_utc_text(share.timestamp),
                share.my_caption, now, now,
            ))
    return len(shares)


def upsert_share(conn: sqlite3.Connection, share: Share) -> None:
    save_shares(conn, [share])


def count_reels(conn: sqlite3.Connection) -> int:
    return conn.execute("SELECT COUNT(*) FROM reels").fetchone()[0]


def get_reel(conn: sqlite3.Connection, shortcode: str) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT * FROM reels WHERE shortcode = ?", (shortcode,)
    ).fetchone()


def get_resume_point(conn: sqlite3.Connection) -> datetime | None:
    """Time of the newest saved reel (local, naive), or None if nothing is saved."""
    row = conn.execute("SELECT MAX(posted_at) AS latest FROM reels").fetchone()
    if row is None or row["latest"] is None:
        return None
    return _from_utc_text(row["latest"])