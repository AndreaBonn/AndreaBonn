from tamagotchi import get_state, make_last_commit_svg, make_tamagotchi_svg, wrap_msg


def test_get_state_happy_at_zero_days():
    state = get_state(days=0)
    assert state["status"] == "ON FIRE"
    assert state["color"] == "#3fb950"


def test_get_state_happy_at_two_days():
    state = get_state(days=2)
    assert state["status"] == "ON FIRE"


def test_get_state_good_at_three_days():
    state = get_state(days=3)
    assert state["status"] == "ON BREAK"


def test_get_state_tired_at_ten_days():
    state = get_state(days=10)
    assert state["status"] == "TIRED"


def test_get_state_dead_at_fifteen_days():
    state = get_state(days=15)
    assert state["status"] == "RIP"


def test_get_state_dead_at_extreme():
    state = get_state(days=9999)
    assert state["status"] == "RIP"


def test_wrap_msg_delegates_to_wrap_text():
    result = wrap_msg("short msg")
    assert result == ["short msg"]


def test_wrap_msg_custom_max_chars():
    result = wrap_msg("one two three", max_chars=8)
    assert len(result) >= 2


def test_make_tamagotchi_svg_returns_valid_svg():
    svg = make_tamagotchi_svg(days=0)
    assert svg.startswith("<svg")
    assert svg.strip().endswith("</svg>")
    assert "GITHUB TAMAGOTCHI" in svg


def test_make_tamagotchi_svg_contains_status():
    svg = make_tamagotchi_svg(days=0)
    assert "ON FIRE" in svg


def test_make_tamagotchi_svg_dead_state():
    svg = make_tamagotchi_svg(days=20)
    assert "RIP" in svg


def test_make_last_commit_svg_returns_valid_svg():
    svg = make_last_commit_svg(days=1, visitors=42, total_visitors=420)
    assert svg.startswith("<svg")
    assert svg.strip().endswith("</svg>")
    assert "SCOREBOARD" in svg


def test_make_last_commit_svg_zero_days():
    svg = make_last_commit_svg(days=0, visitors=10, total_visitors=100)
    assert "Q4" in svg
    assert "#3fb950" in svg


def test_make_last_commit_svg_high_days():
    svg = make_last_commit_svg(days=30, visitors=5, total_visitors=50)
    assert "OT" in svg
    assert "#8b949e" in svg


def test_make_last_commit_svg_visitor_formatting():
    svg = make_last_commit_svg(days=1, visitors=1234, total_visitors=56789)
    assert "1.234" in svg
    assert "56.789" in svg
