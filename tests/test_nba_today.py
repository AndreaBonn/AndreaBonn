from datetime import UTC, datetime

from nba_today import NBA_HISTORY, generate_svg, get_today_event


def test_get_today_event_known_date():
    today = datetime(2025, 3, 2, tzinfo=UTC)
    event = get_today_event(today)
    assert "Wilt Chamberlain" in event["text"]
    assert event["icon"] == "\U0001f4af"


def test_get_today_event_unknown_date_returns_event():
    today = datetime(2025, 7, 15, tzinfo=UTC)
    event = get_today_event(today)
    assert "text" in event
    assert "icon" in event


def test_get_today_event_deterministic_for_same_day():
    today = datetime(2025, 7, 15, tzinfo=UTC)
    e1 = get_today_event(today)
    e2 = get_today_event(today)
    assert e1 == e2


def test_generate_svg_returns_valid_svg():
    event = {"text": "Test event.", "icon": "🏀"}
    today = datetime(2025, 1, 1, tzinfo=UTC)
    svg = generate_svg(event, today)
    assert svg.startswith("<svg")
    assert svg.strip().endswith("</svg>")
    assert "TODAY IN NBA HISTORY" in svg


def test_generate_svg_escapes_text():
    event = {"text": "Score < 100 & special", "icon": "🏀"}
    today = datetime(2025, 1, 1, tzinfo=UTC)
    svg = generate_svg(event, today)
    assert "&lt;" in svg
    assert "&amp;" in svg


def test_nba_history_has_entries():
    assert len(NBA_HISTORY) > 20
