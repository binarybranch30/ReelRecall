from datetime import datetime, timedelta

import pytest

from reelsaver import db
from reelsaver.ingest import run_ingest
from reelsaver.models import Share, TextMessage
from reelsaver.sources.base import ShareSource

T0 = datetime(2026, 10, 18, 14, 0, 0)


class FakeSource(ShareSource):
    def __init__(self, shares, texts):
        self.shares = shares
        self.texts = texts
        self.since_seen = "not called"

    def get_new_messages(self, since=None):
        self.since_seen = since
        return self.shares, self.texts


class BrokenSource(ShareSource):
    def get_new_messages(self, since=None):
        raise RuntimeError("boom")


@pytest.fixture
def conn():
    connection = db.connect(":memory:")
    db.init_db(connection)
    yield connection
    connection.close()


def make_share(code, seconds, msg_id):
    return Share(
        shortcode=code, url=f"https://www.instagram.com/reel/{code}/",
        sender_id="u1", timestamp=T0 + timedelta(seconds=seconds),
        message_id=str(msg_id), thread_id="t1", raw_type="xma_clip",
    )


def make_text(text, seconds, msg_id):
    return TextMessage(
        message_id=str(msg_id), thread_id="t1", sender_id="u1",
        timestamp=T0 + timedelta(seconds=seconds), text=text,
    )


def test_ingest_saves_reel_with_its_caption(conn):
    source = FakeSource([make_share("A", 0, 1)], [make_text("hello", 10, 2)])
    assert run_ingest(source, conn) == 1
    assert db.get_reel(conn, "A")["my_caption"] == "hello"


def test_second_run_uses_resume_point_and_adds_nothing(conn):
    source = FakeSource([make_share("A", 0, 1)], [])
    run_ingest(source, conn)
    assert source.since_seen is None
    assert run_ingest(source, conn) == 0
    assert source.since_seen == T0
    assert db.count_reels(conn) == 1


def test_late_caption_is_added_to_a_reel_saved_earlier(conn):
    run_ingest(FakeSource([make_share("A", 0, 1)], []), conn)
    run_ingest(FakeSource([make_share("A", 0, 1)], [make_text("late", 20, 2)]), conn)
    assert db.get_reel(conn, "A")["my_caption"] == "late"


def test_failed_fetch_saves_nothing(conn):
    with pytest.raises(RuntimeError):
        run_ingest(BrokenSource(), conn)
    assert db.count_reels(conn) == 0