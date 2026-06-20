"""
Total GitHub forks badge.

Sums the forks of every non-fork public repo owned by the user and renders a
flat shields-style badge to assets/total_forks.svg, meant to sit next to the CI
and total-stars badges at the top of the profile README.

Requires: SNAKE_TOKEN env var with public_repo / read:user scope.
Usage: SNAKE_TOKEN=<TOKEN> python total_forks.py
       python total_forks.py --demo --forks <N>
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
MESSAGE_BG = "#007ec6"  # shields blue, conventional for forks/info
TEXT_FILL = "#fff"
LABEL_TEXT = "forks"
FONT_SIZE = 11
CHAR_WIDTH = 6.6  # approx Verdana 11px advance, used to size the badge
SIDE_PADDING = 8
ICON_SLOT = 19  # horizontal space reserved for the fork glyph

# Octicon "repo-forked" (16x16), scaled and offset to sit inside the icon slot
FORK_ICON = (
    '<path transform="translate(5.6,3.5) scale(0.8)" fill="{fill}" '
    'd="M5 5.372v.878c0 .414.336.75.75.75h4.5a.75.75 0 0 0 .75-.75v-.878a2.25 '
    "2.25 0 1 1 1.5 0v.878a2.25 2.25 0 0 1-2.25 2.25h-1.5v2.128a2.251 2.251 0 1 "
    "1-1.5 0V8.5h-1.5A2.25 2.25 0 0 1 3.5 6.25v-.878a2.25 2.25 0 1 1 1.5 0ZM5 "
    "3.25a.75.75 0 1 0-1.5 0 .75.75 0 0 0 1.5 0Zm6.75.75a.75.75 0 1 0 0-1.5.75."
    '75 0 0 0 0 1.5Zm-3 8.75a.75.75 0 1 0-1.5 0 .75.75 0 0 0 1.5 0Z"/>'
)


def compute_total_forks(repos: list[dict]) -> int:
    """Sum forks across owned (non-fork) repositories.

    Parameters
    ----------
    repos
        Repository objects from the GitHub REST API.

    Returns
    -------
    int
        Total forks, forked repos excluded so the count reflects forks earned.
    """
    return sum(repo.get("forks_count", 0) for repo in repos if not repo.get("fork", False))


def _text_width(text: str) -> int:
    """Approximate rendered width in px for the badge font."""
    return round(len(text) * CHAR_WIDTH)


def make_total_forks_svg(total: int) -> str:
    """Render a flat shields-style badge showing the total fork count."""
    message = str(total)
    label_w = ICON_SLOT + _text_width(LABEL_TEXT) + SIDE_PADDING
    message_w = _text_width(message) + SIDE_PADDING * 2
    total_w = label_w + message_w
    label_text_x = ICON_SLOT + (label_w - ICON_SLOT) / 2
    message_text_x = label_w + message_w / 2
    label = escape_svg(LABEL_TEXT)
    message_safe = escape_svg(message)
    icon = FORK_ICON.format(fill=TEXT_FILL)

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{total_w}" height="{BADGE_HEIGHT}" role="img" aria-label="forks: {message_safe}">
  <title>forks: {message_safe}</title>
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
  {icon}
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
    parser.add_argument("--forks", type=int, default=24, help="Forks to simulate in demo mode")
    args = parser.parse_args()

    token = os.environ.get("SNAKE_TOKEN", "")
    if args.demo:
        total = args.forks
        logger.info("Demo mode — %d forks", total)
    elif not token:
        logger.error("No GitHub token provided. Set SNAKE_TOKEN env var. Use --demo for test data.")
        raise SystemExit(1)
    else:
        logger.info("Fetching repositories...")
        repos = fetch_repos(token)
        if not repos:
            logger.error("No repositories returned — aborting to avoid publishing a bogus 0")
            raise SystemExit(1)
        total = compute_total_forks(repos)

    logger.info("Total forks: %d", total)
    ASSETS_DIR.mkdir(exist_ok=True)
    out = ASSETS_DIR / "total_forks.svg"
    try:
        out.write_text(make_total_forks_svg(total), encoding="utf-8")
    except OSError as exc:
        logger.error("Failed to write %s: %s", out, exc)
        raise SystemExit(1) from exc
    logger.info("total_forks.svg generated")


if __name__ == "__main__":
    main()
