"""
Per-repository star-count badges.

Renders one tiny flat-square SVG per owned public repo to assets/stars/<repo>.svg,
showing just the stargazer count on a blue field. These replace the dynamic
img.shields.io/github/stars badges in the profile README, which intermittently
render as "invalid" because shields queries GitHub's *anonymous* API (shared,
~60 req/h) and trips its rate limit when many star badges load at once.

Generating the badges in CI with an authenticated token (5000 req/h) and serving
them as static assets removes the rate-limit dependency entirely.

Requires: SNAKE_TOKEN env var with public_repo / read:user scope.
Usage: SNAKE_TOKEN=<TOKEN> python repo_stars.py
       python repo_stars.py --demo
"""

import argparse
import logging
import os
import re
from pathlib import Path

from common.config import ASSETS_DIR
from common.github_api import fetch_repos
from common.svg import escape_svg

logger = logging.getLogger(__name__)

# Flat-square badge geometry: blue field, white count, square corners — matches
# the look of the previous shields github/stars badges (style=flat-square&label=).
BADGE_HEIGHT = 20
MESSAGE_BG = "#007ec6"  # shields default blue, the colour the old badges used
TEXT_FILL = "#fff"
FONT_SIZE = 11
CHAR_WIDTH = 7  # approx Verdana 11px digit advance (integer: counts are small)
SIDE_PADDING = 6

# Repo names are written straight into a filesystem path, so constrain them to a
# conservative slug to avoid path traversal or odd characters in asset filenames.
_SAFE_NAME_RE = re.compile(r"^[A-Za-z0-9._-]+$")


def build_star_map(repos: list[dict]) -> dict[str, int]:
    """Map repository name to its stargazer count.

    Parameters
    ----------
    repos
        Repository objects from the GitHub REST API.

    Returns
    -------
    dict[str, int]
        Repository name to stargazer count, for every repo with a usable name.
    """
    star_map: dict[str, int] = {}
    for repo in repos:
        name = repo.get("name")
        if isinstance(name, str) and _SAFE_NAME_RE.match(name):
            star_map[name] = repo.get("stargazers_count", 0)
    return star_map


def make_stars_badge(count: int) -> str:
    """Render a flat-square badge showing a single star count on a blue field."""
    message = str(count)
    width = len(message) * CHAR_WIDTH + SIDE_PADDING * 2
    text_x = width / 2
    message_safe = escape_svg(message)

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{BADGE_HEIGHT}" role="img" aria-label="stars: {message_safe}">
  <title>stars: {message_safe}</title>
  <g shape-rendering="crispEdges">
    <rect width="{width}" height="{BADGE_HEIGHT}" fill="{MESSAGE_BG}"/>
  </g>
  <g fill="{TEXT_FILL}" text-anchor="middle" font-family="Verdana,Geneva,DejaVu Sans,sans-serif" font-size="{FONT_SIZE}">
    <text x="{text_x:.0f}" y="14">{message_safe}</text>
  </g>
</svg>'''


def write_badges(star_map: dict[str, int], out_dir: Path) -> int:
    """Write one badge SVG per repository into out_dir.

    Returns
    -------
    int
        Number of badge files written.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    written = 0
    for name, stars in star_map.items():
        target = out_dir / f"{name}.svg"
        try:
            target.write_text(make_stars_badge(stars), encoding="utf-8")
        except OSError as exc:
            logger.error("Failed to write %s: %s", target, exc)
            raise SystemExit(1) from exc
        written += 1
    return written


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser()
    parser.add_argument("--demo", action="store_true")
    args = parser.parse_args()

    if args.demo:
        star_map = {"DemoRepo": 7, "AnotherRepo": 0}
        logger.info("Demo mode — %d repos", len(star_map))
    else:
        token = os.environ.get("SNAKE_TOKEN", "")
        if not token:
            logger.error("No GitHub token provided. Set SNAKE_TOKEN env var. Use --demo for test data.")
            raise SystemExit(1)
        logger.info("Fetching repositories...")
        repos = fetch_repos(token)
        if not repos:
            logger.error("No repositories returned — aborting to avoid wiping star badges")
            raise SystemExit(1)
        star_map = build_star_map(repos)

    out_dir = ASSETS_DIR / "stars"
    written = write_badges(star_map, out_dir)
    logger.info("Generated %d star badges in %s", written, out_dir)


if __name__ == "__main__":
    main()
