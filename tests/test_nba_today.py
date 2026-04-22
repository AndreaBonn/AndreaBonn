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


def test_get_today_event_all_history_dates_return_matching_event():
    """Verifica che ogni data in NBA_HISTORY restituisca un evento dalla lista corrispondente."""
    for (month, day), events in NBA_HISTORY.items():
        today = datetime(2025, month, day, tzinfo=UTC)
        result = get_today_event(today)
        assert result in events, f"Event for ({month}, {day}) not found in expected list"


def test_get_today_event_different_days_can_differ():
    """Due date diverse senza match in NBA_HISTORY possono produrre eventi diversi."""
    d1 = datetime(2025, 7, 15, tzinfo=UTC)
    d2 = datetime(2025, 7, 16, tzinfo=UTC)
    e1 = get_today_event(d1)
    e2 = get_today_event(d2)
    # Non richiediamo che siano diversi (seed potrebbe coincidere),
    # ma verifichiamo che entrambi siano eventi validi
    assert "text" in e1 and "icon" in e1
    assert "text" in e2 and "icon" in e2


def test_generate_svg_contains_date_label():
    event = {"text": "Test event.", "icon": "🏀"}
    today = datetime(2025, 3, 15, tzinfo=UTC)
    svg = generate_svg(event, today)
    assert "MARCH 15" in svg


def test_generate_svg_contains_icon():
    event = {"text": "Test event.", "icon": "🔥"}
    today = datetime(2025, 1, 1, tzinfo=UTC)
    svg = generate_svg(event, today)
    assert "🔥" in svg


def test_generate_svg_contains_footer():
    event = {"text": "Test event.", "icon": "🏀"}
    today = datetime(2025, 1, 1, tzinfo=UTC)
    svg = generate_svg(event, today)
    assert "@AndreaBonn" in svg


def test_generate_svg_min_height():
    event = {"text": "Short.", "icon": "🏀"}
    today = datetime(2025, 1, 1, tzinfo=UTC)
    svg = generate_svg(event, today)
    import re

    h = int(re.search(r'height="(\d+)"', svg).group(1))
    assert h >= 140


def test_main_writes_svg(tmp_path, monkeypatch):
    from nba_today import main

    monkeypatch.setattr("nba_today.ASSETS_DIR", tmp_path)
    main()
    out = tmp_path / "nba_today.svg"
    assert out.exists()
    content = out.read_text(encoding="utf-8")
    assert content.startswith("<svg")
    assert "TODAY IN NBA HISTORY" in content
