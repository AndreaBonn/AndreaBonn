"""Rendering engine for Snake Basket — Pillow-based contribution graph and GIF generation."""

import logging

from PIL import Image, ImageDraw

logger = logging.getLogger(__name__)

CELL_SIZE = 13
CELL_GAP = 3
COLS = 52
ROWS = 7
PAD_LEFT = 36
PAD_TOP = 28
PAD_RIGHT = 16
PAD_BOTTOM = 16

CANVAS_W = PAD_LEFT + COLS * (CELL_SIZE + CELL_GAP) - CELL_GAP + PAD_RIGHT
CANVAS_H = PAD_TOP + ROWS * (CELL_SIZE + CELL_GAP) - CELL_GAP + PAD_BOTTOM

BG_COLOR = (22, 27, 34)
EMPTY_COLOR = (30, 40, 50)
CONTRIB_COLORS = [
    (14, 68, 41),
    (0, 109, 50),
    (38, 166, 78),
    (57, 211, 83),
]
TEXT_COLOR = (139, 148, 158)
SNAKE_HEAD_COLOR = (255, 140, 0)
SNAKE_BODY_COLOR = (200, 100, 0)


def draw_basketball(draw: ImageDraw.ImageDraw, cx: int, cy: int, r: int) -> None:
    """Draw a stylized basketball in the cell."""
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(230, 90, 20))
    lc = (180, 50, 0)
    lw = max(1, r // 5)
    draw.arc([cx - r, cy - r, cx + r, cy + r], start=0, end=360, fill=lc, width=lw)
    draw.line([cx, cy - r, cx, cy + r], fill=lc, width=lw)
    draw.line([cx - r, cy, cx + r, cy], fill=lc, width=lw)
    offset = int(r * 0.55)
    draw.arc([cx - r - offset, cy - r, cx + r - offset, cy + r], start=320, end=40, fill=lc, width=lw)
    draw.arc([cx - r + offset, cy - r, cx + r + offset, cy + r], start=140, end=220, fill=lc, width=lw)


def draw_snake_head(draw: ImageDraw.ImageDraw, cx: int, cy: int, r: int) -> None:
    """Snake head — pivot with number 5."""
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=SNAKE_HEAD_COLOR)
    try:
        draw.text((cx, cy), "5", fill=(255, 255, 255), anchor="mm")
    except (ValueError, OSError) as exc:
        logger.warning("Font anchor 'mm' not supported — falling back to default positioning: %s", exc)
        draw.text((cx - 3, cy - 5), "5", fill=(255, 255, 255))


def cell_xy(col: int, row: int) -> tuple[int, int]:
    x = PAD_LEFT + col * (CELL_SIZE + CELL_GAP)
    y = PAD_TOP + row * (CELL_SIZE + CELL_GAP)
    return x, y


def cell_center(col: int, row: int) -> tuple[int, int]:
    x, y = cell_xy(col, row)
    return x + CELL_SIZE // 2, y + CELL_SIZE // 2


def render_base(contributions: list[list[int]], month_labels: list[tuple]) -> Image.Image:
    """Render the base contribution graph without animation."""
    img = Image.new("RGB", (CANVAS_W, CANVAS_H), BG_COLOR)
    draw = ImageDraw.Draw(img)

    day_names = ["", "Mon", "", "Wed", "", "Fri", ""]
    for r, name in enumerate(day_names):
        if name:
            cx, cy = cell_center(0, r)
            draw.text((PAD_LEFT - 6, cy), name, fill=TEXT_COLOR, anchor="rm", font_size=9)

    for label, col in month_labels:
        x, _ = cell_xy(col, 0)
        draw.text((x, PAD_TOP - 14), label, fill=TEXT_COLOR, font_size=9)

    for c in range(COLS):
        for r in range(ROWS):
            level = contributions[c][r]
            color = EMPTY_COLOR if level == 0 else CONTRIB_COLORS[level - 1]
            x, y = cell_xy(c, r)
            draw.rounded_rectangle([x, y, x + CELL_SIZE, y + CELL_SIZE], radius=2, fill=color)
    return img


def build_snake_path(contributions: list[list[int]]) -> list[tuple]:
    """Snake path: column by column, alternating top-down and bottom-up."""
    path = []
    for c in range(COLS):
        rows = range(ROWS) if c % 2 == 0 else range(ROWS - 1, -1, -1)
        for r in rows:
            if contributions[c][r] == 0:
                path.append((c, r))
    return path


def generate_gif(
    contributions: list[list[int]], month_labels: list[tuple], output_path: str = "snake_basket.gif"
) -> None:
    path = build_snake_path(contributions)
    if not path:
        logger.warning("No empty cells found — your GitHub is already full of contributions!")
        return

    logger.info("Empty cells to eat: %d", len(path))
    logger.info("Generating frames...")

    base_img = render_base(contributions, month_labels)
    frames = []
    eaten = set()
    snake_length = 5
    r_ball = CELL_SIZE // 2 - 1
    step_per_frame = max(1, len(path) // 120)

    for i, (col, row) in enumerate(path):
        if i % step_per_frame != 0 and i != len(path) - 1:
            eaten.add((col, row))
            continue

        eaten.add((col, row))
        frame = base_img.copy()
        draw = ImageDraw.Draw(frame)

        for ec, er in eaten:
            cx, cy = cell_center(ec, er)
            draw_basketball(draw, cx, cy, r_ball)

        snake_positions = path[max(0, i - snake_length + 1) : i + 1]
        for sc, sr in snake_positions[:-1]:
            cx, cy = cell_center(sc, sr)
            body_r = max(2, r_ball - 1)
            draw.ellipse([cx - body_r, cy - body_r, cx + body_r, cy + body_r], fill=SNAKE_BODY_COLOR)

        hcx, hcy = cell_center(col, row)
        draw_snake_head(draw, hcx, hcy, r_ball)
        frames.append(frame)

    # Frame finale
    final = base_img.copy()
    draw = ImageDraw.Draw(final)
    for ec, er in [(p[0], p[1]) for p in path]:
        cx, cy = cell_center(ec, er)
        draw_basketball(draw, cx, cy, r_ball)

    for _ in range(3):
        frames.append(final)

    if not frames:
        logger.warning("No frames generated.")
        return

    try:
        frames[0].save(
            output_path,
            save_all=True,
            append_images=frames[1:],
            loop=0,
            duration=80,
            optimize=True,
        )
    except OSError as exc:
        logger.error(
            "generate_gif: failed to write GIF to '%s': %s — check disk space and permissions", output_path, exc
        )
        raise
    logger.info("GIF saved: %s (%d frames)", output_path, len(frames))
