from unittest.mock import MagicMock, patch

import pytest
from snake_basket import fetch_github_data, generate_demo_data
from snake_rendering import (
    CELL_GAP,
    CELL_SIZE,
    COLS,
    PAD_LEFT,
    PAD_TOP,
    ROWS,
    build_snake_path,
    cell_center,
    cell_xy,
)


def test_cell_xy_first_cell():
    x, y = cell_xy(col=0, row=0)
    assert x == PAD_LEFT
    assert y == PAD_TOP


def test_cell_xy_second_col():
    x, _ = cell_xy(col=1, row=0)
    assert x == PAD_LEFT + (CELL_SIZE + CELL_GAP)


def test_cell_center_offset():
    cx, cy = cell_center(col=0, row=0)
    x, y = cell_xy(col=0, row=0)
    assert cx == x + CELL_SIZE // 2
    assert cy == y + CELL_SIZE // 2


def test_build_snake_path_only_empty_cells():
    contributions = [[0, 1, 0, 0, 1, 0, 0] for _ in range(COLS)]
    path = build_snake_path(contributions)
    for col, row in path:
        assert contributions[col][row] == 0


def test_build_snake_path_full_grid_empty():
    contributions = [[4, 4, 4, 4, 4, 4, 4] for _ in range(COLS)]
    path = build_snake_path(contributions)
    assert path == []


def test_build_snake_path_all_empty():
    contributions = [[0] * ROWS for _ in range(COLS)]
    path = build_snake_path(contributions)
    assert len(path) == COLS * ROWS


def test_generate_demo_data_shape():
    contributions, month_labels = generate_demo_data()
    assert len(contributions) == COLS
    for week in contributions:
        assert len(week) == ROWS


def test_generate_demo_data_levels_in_range():
    contributions, _ = generate_demo_data()
    for week in contributions:
        for level in week:
            assert 0 <= level <= 4


def test_generate_demo_data_deterministic():
    c1, m1 = generate_demo_data()
    c2, m2 = generate_demo_data()
    assert c1 == c2
    assert m1 == m2


def test_generate_demo_data_has_month_labels():
    _, month_labels = generate_demo_data()
    assert len(month_labels) >= 10


# ---------------------------------------------------------------------------
# fetch_github_data — mock requests.post
# ---------------------------------------------------------------------------


def _make_graphql_response(weeks):
    """Helper: costruisce la response GraphQL completa."""
    return {"data": {"user": {"contributionsCollection": {"contributionCalendar": {"weeks": weeks}}}}}


def _make_week(days):
    """Helper: costruisce una settimana con N giorni."""
    return {
        "contributionDays": [
            {"contributionCount": count, "date": f"2025-01-{i + 1:02d}"} for i, count in enumerate(days)
        ]
    }


@patch("snake_basket.requests.post")
def test_fetch_github_data_happy_path(mock_post):
    weeks = [_make_week([0, 5, 10, 0, 3, 0, 0]) for _ in range(52)]
    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = _make_graphql_response(weeks)
    mock_post.return_value = mock_resp

    contributions, month_labels = fetch_github_data(token="tok")
    assert len(contributions) == 52
    for week in contributions:
        assert len(week) == ROWS
    # Verifica mapping livelli: 0→0, 5→2, 10→4, 3→1
    assert contributions[0][0] == 0
    assert contributions[0][1] == 2
    assert contributions[0][2] == 4
    assert contributions[0][4] == 1


@patch("snake_basket.requests.post")
def test_fetch_github_data_graphql_error_raises(mock_post):
    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = {"errors": [{"message": "bad query"}]}
    mock_post.return_value = mock_resp

    from snake_basket import fetch_github_data as fgd

    with pytest.raises(RuntimeError, match="GraphQL API error"):
        fgd(token="tok")


@patch("snake_basket.requests.post")
def test_fetch_github_data_user_not_found_raises(mock_post):
    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = {"data": {"user": None}}
    mock_post.return_value = mock_resp

    with pytest.raises(RuntimeError, match="not found"):
        fetch_github_data(token="tok")


@patch("snake_basket.requests.post")
def test_fetch_github_data_missing_field_raises(mock_post):
    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = {"data": {"user": {"contributionsCollection": {}}}}
    mock_post.return_value = mock_resp

    with pytest.raises(RuntimeError, match="missing expected field"):
        fetch_github_data(token="tok")


@patch("snake_basket.requests.post")
def test_fetch_github_data_empty_week_skipped(mock_post):
    weeks = [{"contributionDays": []} for _ in range(52)]
    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = _make_graphql_response(weeks)
    mock_post.return_value = mock_resp

    contributions, month_labels = fetch_github_data(token="tok")
    assert len(contributions) == 52
    # Tutte le settimane vuote → tutti zeri
    for week in contributions:
        assert week == [0] * ROWS


@patch("snake_basket.requests.post")
def test_fetch_github_data_bad_date_skipped(mock_post):
    bad_week = {"contributionDays": [{"contributionCount": 1, "date": "invalid-date"}]}
    good_weeks = [_make_week([1, 2, 3, 4, 5, 6, 7]) for _ in range(51)]
    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = _make_graphql_response([bad_week] + good_weeks)
    mock_post.return_value = mock_resp

    contributions, _ = fetch_github_data(token="tok")
    assert len(contributions) == 52
    # La prima settimana con data invalida → zeri
    assert contributions[0] == [0] * ROWS


@patch("snake_basket.requests.post")
def test_fetch_github_data_short_week_padded(mock_post):
    """Settimana con meno di 7 giorni → paddata con zeri."""
    short_week = {
        "contributionDays": [
            {"contributionCount": 5, "date": "2025-01-01"},
            {"contributionCount": 3, "date": "2025-01-02"},
        ]
    }
    weeks = [short_week] + [_make_week([0] * 7) for _ in range(51)]
    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = _make_graphql_response(weeks)
    mock_post.return_value = mock_resp

    contributions, _ = fetch_github_data(token="tok")
    assert len(contributions[0]) == 7
    assert contributions[0][0] == 2  # count 5 → level 2
    assert contributions[0][1] == 1  # count 3 → level 1
    assert contributions[0][2] == 0  # padded


@patch("snake_basket.requests.post")
def test_fetch_github_data_level_boundaries(mock_post):
    """Verifica i confini esatti dei livelli: 0, 1-3, 4-6, 7-9, 10+."""
    week = _make_week([0, 1, 3, 4, 6, 7, 9])
    weeks = [week] + [_make_week([10, 0, 0, 0, 0, 0, 0]) for _ in range(51)]
    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = _make_graphql_response(weeks)
    mock_post.return_value = mock_resp

    contributions, _ = fetch_github_data(token="tok")
    assert contributions[0] == [0, 1, 1, 2, 2, 3, 3]
    assert contributions[1][0] == 4  # count 10 → level 4
