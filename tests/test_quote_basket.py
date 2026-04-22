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


def test_generate_svg_contains_date():
    quote = {"text": "Test.", "author": "Author"}
    today = datetime(2025, 3, 15, tzinfo=UTC)
    svg = generate_svg(quote, today)
    assert "15 Mar 2025" in svg


def test_generate_svg_contains_header():
    quote = {"text": "Test.", "author": "Author"}
    today = datetime(2025, 1, 1, tzinfo=UTC)
    svg = generate_svg(quote, today)
    assert "QUOTE OF THE DAY" in svg
    assert "@AndreaBonn" in svg


def test_generate_svg_height_scales_with_text_length():
    short = {"text": "Short.", "author": "A"}
    long = {
        "text": "This is a very long quote that should make the SVG taller because it wraps over many lines in the output.",
        "author": "B",
    }
    today = datetime(2025, 1, 1, tzinfo=UTC)
    svg_short = generate_svg(short, today)
    svg_long = generate_svg(long, today)
    # Estrarre altezza dal viewBox/height
    import re

    h_short = int(re.search(r'height="(\d+)"', svg_short).group(1))
    h_long = int(re.search(r'height="(\d+)"', svg_long).group(1))
    assert h_long > h_short


def test_main_writes_svg(tmp_path, monkeypatch):
    from quote_basket import main

    monkeypatch.setattr("quote_basket.ASSETS_DIR", tmp_path)
    main()
    out = tmp_path / "quote.svg"
    assert out.exists()
    content = out.read_text(encoding="utf-8")
    assert content.startswith("<svg")
    assert content.strip().endswith("</svg>")
