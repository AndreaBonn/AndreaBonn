from unittest.mock import patch

import update_visitors


@patch("update_visitors.fetch_visitor_count", return_value=(12, 340))
def test_main_triggers_visitor_count_update(mock_fetch):
    update_visitors.main()

    mock_fetch.assert_called_once_with()


@patch("update_visitors.fetch_visitor_count", return_value=(12, 340))
def test_main_reports_recent_and_total_views(mock_fetch, caplog):
    with caplog.at_level("INFO"):
        update_visitors.main()

    assert "12" in caplog.text
    assert "340" in caplog.text


@patch("update_visitors.fetch_visitor_count", return_value=(0, 0))
def test_main_reports_zero_views_without_failing(mock_fetch, caplog):
    with caplog.at_level("INFO"):
        update_visitors.main()

    assert "0" in caplog.text
