from datetime import UTC, datetime

from quote_basket import QUOTES, generate_svg, pick_daily_quote


def test_pick_daily_quote_returns_dict():
    quote = pick_daily_quote()
    assert "text" in quote
    assert "author" in quote


def test_pick_daily_quote_deterministic():
    q1 = pick_daily_quote()
    q2 = pick_daily_quote()
    assert q1 == q2


def test_pick_daily_quote_from_pool():
    quote = pick_daily_quote()
    assert quote in QUOTES


def test_generate_svg_returns_valid_svg():
    quote = {"text": "Test quote.", "author": "Test Author"}
    today = datetime(2025, 1, 1, tzinfo=UTC)
    svg = generate_svg(quote, today)
    assert svg.startswith("<svg")
    assert svg.strip().endswith("</svg>")


def test_generate_svg_contains_author():
    quote = {"text": "Test quote.", "author": "Michael Jordan"}
    today = datetime(2025, 1, 1, tzinfo=UTC)
    svg = generate_svg(quote, today)
    assert "Michael Jordan" in svg


def test_generate_svg_escapes_special_chars():
    quote = {"text": "A & B < C", "author": "Author"}
    today = datetime(2025, 1, 1, tzinfo=UTC)
    svg = generate_svg(quote, today)
    assert "A &amp; B &lt; C" in svg
