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


def test_read_visitors_data_corrupted_json(tmp_path, monkeypatch):
    corrupted = tmp_path / "visitors.json"
    corrupted.write_text("{invalid json")
    monkeypatch.setattr("common.visitors.VISITORS_JSON", corrupted)
    data = _read_visitors_data()
    assert "history" in data
    assert data["last_komarev"] == 0
