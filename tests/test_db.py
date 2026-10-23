from datetime import datetime

import pytest

from reelsaver import db
from reelsaver.models import Share


@pytest.fixture
def conn():
    connection = db.connect(":memory:")
    db.init_db(connection)
    yield connection
    connection.close()


def make_share(code="A", when=datetime(2026, 10, 18, 14, 0, 0), caption=None, msg_id="1"):
    return Share(
        shortcode=code, url=f"https://www.instagram.com/reel/{code}/",
        sender_id="u1", timestamp=when, message_id=msg_id,
        thread_id="t1", raw_type="xma_clip", my_caption=caption,
    )


def count(conn):
    return conn.execute("SELECT COUNT(*) FROM reels").fetchone()[0]


def test_saving_same_reel_twice_gives_one_row(conn):
    db.upsert_share(conn, make_share())
    db.upsert_share(conn, make_share())
    assert count(conn) == 1


def test_caption_is_added_on_a_later_run(conn):
    db.upsert_share(conn, make_share(caption=None))
    db.upsert_share(conn, make_share(caption="nice"))
    assert db.get_reel(conn, "A")["my_caption"] == "nice"


def test_new_caption_replaces_old_one(conn):
    db.upsert_share(conn, make_share(caption="old"))
    db.upsert_share(conn, make_share(caption="new"))
    assert db.get_reel(conn, "A")["my_caption"] == "new"


def test_missing_caption_does_not_erase_existing_one(conn):
    db.upsert_share(conn, make_share(caption="nice"))
    db.upsert_share(conn, make_share(caption=None))
    assert db.get_reel(conn, "A")["my_caption"] == "nice"


def test_resume_point_is_none_when_empty(conn):
    assert db.get_resume_point(conn) is None


def test_resume_point_is_newest_reel_in_local_time(conn):
    early = datetime(2026, 10, 18, 14, 0, 0)
    late = datetime(2026, 10, 18, 15, 30, 0)
    db.upsert_share(conn, make_share("A", early, msg_id="1"))
    db.upsert_share(conn, make_share("B", late, msg_id="2"))
    assert db.get_resume_point(conn) == late


def test_save_shares_is_all_or_nothing(conn):
    with pytest.raises(AttributeError):
        db.save_shares(conn, [make_share("A"), "not a share"])
    assert count(conn) == 0