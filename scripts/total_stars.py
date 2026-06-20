"""
Total GitHub stars badge.

Sums the stargazers of every non-fork public repo owned by the user and renders
a flat shields-style badge to assets/total_stars.svg, meant to sit next to the
CI badge at the top of the profile README.

Requires: SNAKE_TOKEN env var with public_repo / read:user scope.
Usage: SNAKE_TOKEN=<TOKEN> python total_stars.py
       python total_stars.py --demo --stars <N>
"""

import argparse
import logging
import os

from common.config import ASSETS_DIR
from common.github_api import fetch_repos
from common.svg import escape_svg

logger = logging.getLogger(__name__)

# Flat badge geometry (shields "flat" style, 20px tall)
BADGE_HEIGHT = 20
LABEL_BG = "#555"
MESSAGE_BG = "#dfb317"  # shields gold, conventional for stars
TEXT_FILL = "#fff"
LABEL_TEXT = "stars"
FONT_SIZE = 11
CHAR_WIDTH = 6.6  # approx Verdana 11px advance, used to size the badge
SIDE_PADDING = 8
ICON_SLOT = 19  # horizontal space reserved for the star glyph


def compute_total_stars(repos: list[dict]) -> int:
    """Sum stargazers across owned (non-fork) repositories.

    Parameters
    ----------
    repos
        Repository objects from the GitHub REST API.

    Returns
    -------
    int
        Total stargazers, forks excluded so the count reflects stars earned.
    """
    return sum(repo.get("stargazers_count", 0) for repo in repos if not repo.get("fork", False))


def _text_width(text: str) -> int:
    """Approximate rendered width in px for the badge font."""
    return round(len(text) * CHAR_WIDTH)


def make_total_stars_svg(total: int) -> str:
    """Render a flat shields-style badge showing the total star count."""
    message = str(total)
    label_w = ICON_SLOT + _text_width(LABEL_TEXT) + SIDE_PADDING
    message_w = _text_width(message) + SIDE_PADDING * 2
    total_w = label_w + message_w
    label_text_x = ICON_SLOT + (label_w - ICON_SLOT) / 2
    message_text_x = label_w + message_w / 2
    label = escape_svg(LABEL_TEXT)
    message_safe = escape_svg(message)

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{total_w}" height="{BADGE_HEIGHT}" role="img" aria-label="stars: {message_safe}">
  <title>stars: {message_safe}</title>
  <linearGradient id="s" x2="0" y2="100%">
    <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
    <stop offset="1" stop-opacity=".1"/>
  </linearGradient>
  <clipPath id="r"><rect width="{total_w}" height="{BADGE_HEIGHT}" rx="3" fill="#fff"/></clipPath>
  <g clip-path="url(#r)">
    <rect width="{label_w}" height="{BADGE_HEIGHT}" fill="{LABEL_BG}"/>
    <rect x="{label_w}" width="{message_w}" height="{BADGE_HEIGHT}" fill="{MESSAGE_BG}"/>
    <rect width="{total_w}" height="{BADGE_HEIGHT}" fill="url(#s)"/>
  </g>
  <path d="M11 4.5l1.7 3.4 3.8.6-2.7 2.7.6 3.8L11 13.4 7.6 15.5l.6-3.8L5.5 9l3.8-.6z" fill="{TEXT_FILL}"/>
  <g fill="{TEXT_FILL}" text-anchor="middle" font-family="Verdana,Geneva,DejaVu Sans,sans-serif" font-size="{FONT_SIZE}">
    <text x="{label_text_x:.0f}" y="15" fill="#010101" fill-opacity=".3">{label}</text>
    <text x="{label_text_x:.0f}" y="14">{label}</text>
    <text x="{message_text_x:.0f}" y="15" fill="#010101" fill-opacity=".3">{message_safe}</text>
    <text x="{message_text_x:.0f}" y="14">{message_safe}</text>
  </g>
</svg>'''


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser()
    parser.add_argument("--demo", action="store_true")
    parser.add_argument("--stars", type=int, default=128, help="Stars to simulate in demo mode")
    args = parser.parse_args()

    token = os.environ.get("SNAKE_TOKEN", "")
    if args.demo:
        total = args.stars
        logger.info("Demo mode — %d stars", total)
    elif not token:
        logger.error("No GitHub token provided. Set SNAKE_TOKEN env var. Use --demo for test data.")
        raise SystemExit(1)
    else:
        logger.info("Fetching repositories...")
        repos = fetch_repos(token)
        if not repos:
            logger.error("No repositories returned — aborting to avoid publishing a bogus 0")
            raise SystemExit(1)
        total = compute_total_stars(repos)

    logger.info("Total stars: %d", total)
    ASSETS_DIR.mkdir(exist_ok=True)
    out = ASSETS_DIR / "total_stars.svg"
    try:
        out.write_text(make_total_stars_svg(total), encoding="utf-8")
    except OSError as exc:
        logger.error("Failed to write %s: %s", out, exc)
        raise SystemExit(1) from exc
    logger.info("total_stars.svg generated")


if __name__ == "__main__":
    main()
