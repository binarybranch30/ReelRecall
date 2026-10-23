import sqlite3

from reelsaver import db
from reelsaver.pairing import pair
from reelsaver.sources.base import ShareSource


def run_ingest(source: ShareSource, conn: sqlite3.Connection) -> int:
    """Run once and return how many NEW reels were saved. Errors propagate."""
    before = db.count_reels(conn)

    since = db.get_resume_point(conn)
    shares, texts = source.get_new_messages(since)
    paired = pair(shares, texts)
    db.save_shares(conn, paired)

    new = db.count_reels(conn) - before
    print(f"Fetched {len(shares)} reels and {len(texts)} texts: {new} new reels saved.")
    return new