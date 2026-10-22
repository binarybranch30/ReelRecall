from datetime import datetime, timedelta

from reelsaver.models import Share, TextMessage
from reelsaver.pairing import pair

T0 = datetime(2026, 10, 18, 14, 0, 0)


def make_share(code, seconds, msg_id, thread="t1"):
    return Share(
        shortcode=code, url=f"https://www.instagram.com/reel/{code}/",
        sender_id="u1", timestamp=T0 + timedelta(seconds=seconds),
        message_id=str(msg_id), thread_id=thread, raw_type="xma_clip",
    )


def make_text(text, seconds, msg_id, thread="t1"):
    return TextMessage(
        message_id=str(msg_id), thread_id=thread, sender_id="u1",
        timestamp=T0 + timedelta(seconds=seconds), text=text,
    )


def test_caption_attaches_to_preceding_reel():
    result = pair([make_share("A", 0, 1)], [make_text("hello", 10, 2)])
    assert result[0].my_caption == "hello"


def test_two_reels_then_caption_goes_to_the_second():
    result = pair([make_share("A", 0, 1), make_share("B", 5, 2)], [make_text("cap", 10, 3)])
    assert result[0].my_caption is None
    assert result[1].my_caption == "cap"


def test_text_before_any_reel_is_ignored():
    result = pair([make_share("A", 10, 2)], [make_text("early", 0, 1)])
    assert result[0].my_caption is None


def test_text_outside_window_is_ignored():
    result = pair([make_share("A", 0, 1)], [make_text("late", 120, 2)])
    assert result[0].my_caption is None


def test_texts_are_appended_up_to_the_limit():
    texts = [make_text(f"t{i}", 5 + i, 10 + i) for i in range(8)]
    result = pair([make_share("A", 0, 1)], texts, max_texts=5)
    assert result[0].my_caption == "t0\nt1\nt2\nt3\nt4"


def test_same_second_uses_message_id():
    after = pair([make_share("A", 0, 5)], [make_text("same second", 0, 6)])
    assert after[0].my_caption == "same second"
    before = pair([make_share("A", 0, 5)], [make_text("same second", 0, 4)])
    assert before[0].my_caption is None


def test_text_in_another_thread_is_ignored():
    result = pair([make_share("A", 0, 1, thread="t1")], [make_text("x", 5, 2, thread="t2")])
    assert result[0].my_caption is None