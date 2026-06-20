from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
import requests
import tamagotchi
from scoreboard import make_last_commit_svg
from tamagotchi import fetch_days_since_last_commit, get_state, make_tamagotchi_svg, wrap_msg


@patch("tamagotchi.requests.get")
def test_fetch_days_http_error_returns_none(mock_get):
    mock_get.side_effect = requests.ConnectionError("timeout")
    assert fetch_days_since_last_commit(token="tok") is None


@patch("tamagotchi.requests.get")
def test_fetch_days_non_json_response_returns_none(mock_get):
    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.side_effect = requests.exceptions.JSONDecodeError("err", "doc", 0)
    mock_get.return_value = mock_resp
    assert fetch_days_since_last_commit(token="tok") is None


@patch("tamagotchi.requests.get")
def test_fetch_days_missing_commit_field_returns_none(mock_get):
    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = {"items": [{"no_commit_key": {}}]}
    mock_get.return_value = mock_resp
    assert fetch_days_since_last_commit(token="tok") is None


@patch("tamagotchi.requests.get")
def test_fetch_days_non_dict_payload_returns_none(mock_get):
    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = ["not", "a", "dict"]
    mock_get.return_value = mock_resp
    assert fetch_days_since_last_commit(token="tok") is None


@patch("tamagotchi.requests.get")
def test_fetch_days_valid_response_returns_elapsed_days(mock_get):
    commit_date = (datetime.now(UTC) - timedelta(days=4)).isoformat().replace("+00:00", "Z")
    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = {"items": [{"commit": {"author": {"date": commit_date}}}]}
    mock_get.return_value = mock_resp
    assert fetch_days_since_last_commit(token="tok") == 4


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


def test_get_state_out_of_range_falls_back_to_dead():
    # Days beyond every defined range hit the explicit dead fallback.
    state = get_state(days=100000)
    assert state["status"] == "RIP"


def test_wrap_msg_delegates_to_wrap_text():
    result = wrap_msg("short msg")
    assert result == ["short msg"]


def test_wrap_msg_custom_max_chars():
    result = wrap_msg("one two three", max_chars=8)
    assert result == ["one two", "three"]


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


def test_make_last_commit_svg_q3_two_days():
    svg = make_last_commit_svg(days=2, visitors=10, total_visitors=100)
    assert "Q3" in svg
    assert "#3fb950" in svg


def test_make_last_commit_svg_q2_five_days():
    svg = make_last_commit_svg(days=5, visitors=10, total_visitors=100)
    assert "Q2" in svg
    assert "#e6861a" in svg


def test_make_last_commit_svg_q1_fourteen_days():
    svg = make_last_commit_svg(days=14, visitors=10, total_visitors=100)
    assert "Q1" in svg
    assert "#f85149" in svg


def test_make_tamagotchi_svg_good_state():
    svg = make_tamagotchi_svg(days=4)
    assert "ON BREAK" in svg


def test_make_tamagotchi_svg_tired_state():
    svg = make_tamagotchi_svg(days=10)
    assert "TIRED" in svg


# ---------------------------------------------------------------------------
# main() — integration tests
# ---------------------------------------------------------------------------


def test_main_demo_writes_svgs(tmp_path, monkeypatch):

    monkeypatch.setattr("tamagotchi.ASSETS_DIR", tmp_path)
    monkeypatch.setattr("sys.argv", ["tamagotchi", "--demo", "--days", "3", "--visitors", "42"])
    from tamagotchi import main

    main()
    assert (tmp_path / "tamagotchi.svg").exists()
    assert (tmp_path / "last_commit.svg").exists()
    content = (tmp_path / "tamagotchi.svg").read_text(encoding="utf-8")
    assert "GITHUB TAMAGOTCHI" in content
    assert "ON BREAK" in content


def test_main_no_token_exits(monkeypatch):

    monkeypatch.setattr("sys.argv", ["tamagotchi"])
    monkeypatch.delenv("SNAKE_TOKEN", raising=False)
    from tamagotchi import main

    with pytest.raises(SystemExit):
        main()


def test_main_token_success_writes_svgs(tmp_path, monkeypatch):
    monkeypatch.setattr(tamagotchi, "ASSETS_DIR", tmp_path)
    monkeypatch.setattr("sys.argv", ["tamagotchi"])
    monkeypatch.setenv("SNAKE_TOKEN", "tok")
    monkeypatch.setattr(tamagotchi, "fetch_days_since_last_commit", lambda _t: 1)
    monkeypatch.setattr(tamagotchi, "fetch_visitor_count", lambda: (42, 420))
    from tamagotchi import main

    main()
    assert (tmp_path / "tamagotchi.svg").exists()
    assert (tmp_path / "last_commit.svg").exists()


def test_main_token_unavailable_commit_exits(tmp_path, monkeypatch):
    monkeypatch.setattr(tamagotchi, "ASSETS_DIR", tmp_path)
    monkeypatch.setattr("sys.argv", ["tamagotchi"])
    monkeypatch.setenv("SNAKE_TOKEN", "tok")
    monkeypatch.setattr(tamagotchi, "fetch_days_since_last_commit", lambda _t: None)
    from tamagotchi import main

    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 1


def test_main_write_failure_exits(tmp_path, monkeypatch):
    monkeypatch.setattr(tamagotchi, "ASSETS_DIR", tmp_path)
    monkeypatch.setattr("sys.argv", ["tamagotchi", "--demo", "--days", "1"])

    def _boom(*_a, **_k):
        raise OSError("disk full")

    monkeypatch.setattr("pathlib.Path.write_text", _boom)
    from tamagotchi import main

    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 1
