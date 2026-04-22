from snake_basket import generate_demo_data
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
