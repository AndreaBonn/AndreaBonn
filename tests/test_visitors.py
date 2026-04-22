import json
from datetime import UTC, datetime, timedelta
from unittest.mock import patch

from common.visitors import _migrate_legacy, _read_visitors_data, fetch_visitor_count


def test_migrate_legacy_empty():
    result = _migrate_legacy({})
    assert result == {"last_komarev": 0, "total": 0, "history": []}


def test_migrate_legacy_with_old_data():
    result = _migrate_legacy({"total": 100, "last_komarev": 50})
    assert result["last_komarev"] == 50
    assert result["history"] == []


def test_read_visitors_data_missing_file(tmp_path, monkeypatch):
    monkeypatch.setattr("common.visitors.VISITORS_JSON", tmp_path / "missing.json")
    data = _read_visitors_data()
    assert "history" in data
    assert data["last_komarev"] == 0


def test_read_visitors_data_migrates_old_format(tmp_path, monkeypatch):
    old_file = tmp_path / "visitors.json"
    old_file.write_text(json.dumps({"total": 13, "last_komarev": 13}))
    monkeypatch.setattr("common.visitors.VISITORS_JSON", old_file)
    data = _read_visitors_data()
    assert "history" in data
    assert data["last_komarev"] == 13


def test_fetch_visitor_count_first_run(tmp_path, monkeypatch):
    visitors_file = tmp_path / "visitors.json"
    monkeypatch.setattr("common.visitors.VISITORS_JSON", visitors_file)
    with patch("common.visitors._fetch_komarev_count", return_value=50):
        views_14d, total = fetch_visitor_count()
    assert total == 0  # primo run, nessun delta calcolabile
    assert views_14d == 0


def test_fetch_visitor_count_accumulates_delta(tmp_path, monkeypatch):
    visitors_file = tmp_path / "visitors.json"
    visitors_file.write_text(
        json.dumps(
            {
                "last_komarev": 40,
                "total": 200,
                "history": [],
            }
        )
    )
    monkeypatch.setattr("common.visitors.VISITORS_JSON", visitors_file)
    with patch("common.visitors._fetch_komarev_count", return_value=50):
        views_14d, total = fetch_visitor_count()
    assert views_14d == 10
    assert total == 210  # 200 + delta 10


def test_fetch_visitor_count_prunes_old_entries(tmp_path, monkeypatch):
    visitors_file = tmp_path / "visitors.json"
    old_date = (datetime.now(UTC) - timedelta(days=20)).strftime("%Y-%m-%d")
    recent_date = (datetime.now(UTC) - timedelta(days=5)).strftime("%Y-%m-%d")
    visitors_file.write_text(
        json.dumps(
            {
                "last_komarev": 100,
                "total": 500,
                "history": [
                    {"date": old_date, "views": 50},
                    {"date": recent_date, "views": 30},
                ],
            }
        )
    )
    monkeypatch.setattr("common.visitors.VISITORS_JSON", visitors_file)
    with patch("common.visitors._fetch_komarev_count", return_value=110):
        views_14d, total = fetch_visitor_count()
    assert views_14d == 30 + 10  # recent + new delta
    assert total == 510  # 500 + delta 10


def test_fetch_visitor_count_same_day_accumulates(tmp_path, monkeypatch):
    visitors_file = tmp_path / "visitors.json"
    today = datetime.now(UTC).strftime("%Y-%m-%d")
    visitors_file.write_text(
        json.dumps(
            {
                "last_komarev": 90,
                "total": 300,
                "history": [{"date": today, "views": 5}],
            }
        )
    )
    monkeypatch.setattr("common.visitors.VISITORS_JSON", visitors_file)
    with patch("common.visitors._fetch_komarev_count", return_value=100):
        views_14d, total = fetch_visitor_count()
    assert views_14d == 15  # 5 existing + 10 new delta
    assert total == 310  # 300 + delta 10


def test_fetch_visitor_count_komarev_failure_uses_last_known(tmp_path, monkeypatch):
    visitors_file = tmp_path / "visitors.json"
    visitors_file.write_text(
        json.dumps(
            {
                "last_komarev": 50,
                "total": 200,
                "history": [],
            }
        )
    )
    monkeypatch.setattr("common.visitors.VISITORS_JSON", visitors_file)
    with patch("common.visitors._fetch_komarev_count", return_value=None):
        views_14d, total = fetch_visitor_count()
    assert total == 200  # no delta when komarev fails
    assert views_14d == 0


def test_read_visitors_data_corrupted_json_creates_backup(tmp_path, monkeypatch):
    corrupted = tmp_path / "visitors.json"
    corrupted.write_text("{invalid json")
    monkeypatch.setattr("common.visitors.VISITORS_JSON", corrupted)
    data = _read_visitors_data()
    assert "history" in data
    assert data["last_komarev"] == 0
    backup = tmp_path / "visitors.bak"
    assert backup.exists()
    assert backup.read_text() == "{invalid json"


def test_read_visitors_data_corrupted_json_backup_fails(tmp_path, monkeypatch):
    corrupted = tmp_path / "visitors.json"
    corrupted.write_text("{bad}")
    monkeypatch.setattr("common.visitors.VISITORS_JSON", corrupted)
    # Make rename fail by patching Path.rename
    monkeypatch.setattr("pathlib.Path.rename", lambda *a, **kw: (_ for _ in ()).throw(OSError("no perms")))
    data = _read_visitors_data()
    assert "history" in data
    assert data["last_komarev"] == 0


# ---------------------------------------------------------------------------
# _fetch_komarev_count — comportamento con mock
# ---------------------------------------------------------------------------


@patch("common.visitors.requests.get")
def test_fetch_komarev_count_happy_path(mock_get):
    from unittest.mock import MagicMock

    from common.visitors import _fetch_komarev_count

    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.text = "<svg><text>views</text><text>1,234</text></svg>"
    mock_get.return_value = mock_resp

    result = _fetch_komarev_count()
    assert result == 1234


@patch("common.visitors.requests.get")
def test_fetch_komarev_count_network_error_returns_none(mock_get):
    import requests
    from common.visitors import _fetch_komarev_count

    mock_get.side_effect = requests.ConnectionError("timeout")
    assert _fetch_komarev_count() is None


@patch("common.visitors.requests.get")
def test_fetch_komarev_count_no_numbers_returns_none(mock_get):
    from unittest.mock import MagicMock

    from common.visitors import _fetch_komarev_count

    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.text = "<svg><text>no numbers here</text></svg>"
    mock_get.return_value = mock_resp

    assert _fetch_komarev_count() is None


@patch("common.visitors.requests.get")
def test_fetch_komarev_count_capped_at_10_million(mock_get):
    from unittest.mock import MagicMock

    from common.visitors import _fetch_komarev_count

    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.text = "<svg><text>99999999</text></svg>"
    mock_get.return_value = mock_resp

    result = _fetch_komarev_count()
    assert result == 10_000_000


@patch("common.visitors.requests.get")
def test_fetch_komarev_count_http_error_returns_none(mock_get):
    from unittest.mock import MagicMock

    import requests
    from common.visitors import _fetch_komarev_count

    mock_resp = MagicMock()
    mock_resp.raise_for_status.side_effect = requests.HTTPError("500 Server Error")
    mock_get.return_value = mock_resp

    assert _fetch_komarev_count() is None


@patch("common.visitors.requests.get")
def test_fetch_komarev_count_plain_number(mock_get):
    from unittest.mock import MagicMock

    from common.visitors import _fetch_komarev_count

    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.text = "<svg><text>views</text><text>42</text></svg>"
    mock_get.return_value = mock_resp

    assert _fetch_komarev_count() == 42
