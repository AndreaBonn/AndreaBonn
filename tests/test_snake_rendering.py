import os
import tempfile

from PIL import Image, ImageDraw
from snake_rendering import (
    BG_COLOR,
    CANVAS_H,
    CANVAS_W,
    COLS,
    CONTRIB_COLORS,
    EMPTY_COLOR,
    ROWS,
    SNAKE_HEAD_COLOR,
    build_snake_path,
    cell_center,
    draw_basketball,
    draw_snake_head,
    generate_gif,
    render_base,
)

# ---------------------------------------------------------------------------
# draw_basketball
# ---------------------------------------------------------------------------


def test_draw_basketball_paints_ball_area():
    img = Image.new("RGB", (50, 50), (0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw_basketball(draw, cx=25, cy=25, r=10)
    # Il centro ha le linee (180, 50, 0), i quadranti hanno il fill (230, 90, 20)
    # Verifichiamo un pixel nel quadrante (non sulle linee)
    pixel = img.getpixel((20, 20))
    assert pixel == (230, 90, 20)


def test_draw_basketball_does_not_affect_far_corners():
    img = Image.new("RGB", (100, 100), (0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw_basketball(draw, cx=50, cy=50, r=10)
    assert img.getpixel((0, 0)) == (0, 0, 0)
    assert img.getpixel((99, 99)) == (0, 0, 0)


# ---------------------------------------------------------------------------
# draw_snake_head
# ---------------------------------------------------------------------------


def test_draw_snake_head_paints_head_color():
    img = Image.new("RGB", (50, 50), (0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw_snake_head(draw, cx=25, cy=25, r=10)
    # Un pixel vicino al centro (non esattamente il centro perché c'è il testo "5")
    pixel = img.getpixel((17, 25))
    assert pixel == SNAKE_HEAD_COLOR


# ---------------------------------------------------------------------------
# render_base
# ---------------------------------------------------------------------------


def test_render_base_returns_correct_size():
    contributions = [[0] * ROWS for _ in range(COLS)]
    img = render_base(contributions, month_labels=[])
    assert img.size == (CANVAS_W, CANVAS_H)


def test_render_base_background_is_correct():
    contributions = [[0] * ROWS for _ in range(COLS)]
    img = render_base(contributions, month_labels=[])
    assert img.getpixel((0, 0)) == BG_COLOR


def test_render_base_empty_cells_use_empty_color():
    contributions = [[0] * ROWS for _ in range(COLS)]
    img = render_base(contributions, month_labels=[])
    cx, cy = cell_center(0, 0)
    assert img.getpixel((cx, cy)) == EMPTY_COLOR


def test_render_base_filled_cells_use_contrib_color():
    contributions = [[0] * ROWS for _ in range(COLS)]
    contributions[0][0] = 4  # livello massimo
    img = render_base(contributions, month_labels=[])
    cx, cy = cell_center(0, 0)
    assert img.getpixel((cx, cy)) == CONTRIB_COLORS[3]


def test_render_base_all_levels_rendered():
    contributions = [[0] * ROWS for _ in range(COLS)]
    for level in range(1, 5):
        contributions[level][0] = level
    img = render_base(contributions, month_labels=[])
    for level in range(1, 5):
        cx, cy = cell_center(level, 0)
        assert img.getpixel((cx, cy)) == CONTRIB_COLORS[level - 1]


def test_render_base_with_month_labels_does_not_crash():
    contributions = [[0] * ROWS for _ in range(COLS)]
    labels = [("Jan", 0), ("Feb", 4), ("Mar", 8)]
    img = render_base(contributions, month_labels=labels)
    assert img.size == (CANVAS_W, CANVAS_H)


# ---------------------------------------------------------------------------
# generate_gif
# ---------------------------------------------------------------------------


def test_generate_gif_creates_file():
    contributions = [[0] * ROWS for _ in range(COLS)]
    contributions[0] = [1, 1, 1, 1, 1, 1, 1]  # prima colonna piena
    # Ci sono celle vuote nelle altre 51 colonne
    with tempfile.NamedTemporaryFile(suffix=".gif", delete=False) as f:
        path = f.name
    try:
        generate_gif(contributions, month_labels=[], output_path=path)
        assert os.path.exists(path)
        img = Image.open(path)
        assert img.format == "GIF"
        assert img.n_frames > 1
    finally:
        os.unlink(path)


def test_generate_gif_no_empty_cells_returns_early():
    contributions = [[4] * ROWS for _ in range(COLS)]  # tutto pieno
    with tempfile.NamedTemporaryFile(suffix=".gif", delete=False) as f:
        path = f.name
    try:
        generate_gif(contributions, month_labels=[], output_path=path)
        # Il file non viene scritto (o è vuoto dal NamedTemporaryFile)
        assert os.path.getsize(path) == 0
    finally:
        os.unlink(path)


def test_generate_gif_small_grid_produces_valid_gif():
    """Griglia con poche celle vuote — verifica che la GIF sia valida."""
    contributions = [[4] * ROWS for _ in range(COLS)]
    # Solo 3 celle vuote
    contributions[0][0] = 0
    contributions[0][1] = 0
    contributions[0][2] = 0
    with tempfile.NamedTemporaryFile(suffix=".gif", delete=False) as f:
        path = f.name
    try:
        generate_gif(contributions, month_labels=[], output_path=path)
        img = Image.open(path)
        assert img.format == "GIF"
    finally:
        os.unlink(path)


# ---------------------------------------------------------------------------
# build_snake_path (copre pattern serpentina)
# ---------------------------------------------------------------------------


def test_build_snake_path_alternates_direction():
    """Colonne pari: top-down, colonne dispari: bottom-up."""
    contributions = [[0] * ROWS for _ in range(COLS)]
    path = build_snake_path(contributions)
    # Prima colonna (pari): righe 0,1,2,3,4,5,6
    col0_rows = [r for c, r in path if c == 0]
    assert col0_rows == list(range(ROWS))
    # Seconda colonna (dispari): righe 6,5,4,3,2,1,0
    col1_rows = [r for c, r in path if c == 1]
    assert col1_rows == list(range(ROWS - 1, -1, -1))
