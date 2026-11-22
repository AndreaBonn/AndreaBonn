"""
Per-repository quality badges: test count and coverage in one compact SVG.

Replaces the two shields.io endpoint badges per row in the README. Those were
rendered at different widths (GitHub shrank the long "12123 passed" badge until
it was unreadable) and showed upstream glitches such as "0 passed" or "pending"
verbatim. Here every badge has the same fixed width, and any value that is not
a real result renders as a neutral dash.

Sources live in quality_sources.py. No token needed: the badge JSON files are
public raw files.

Usage: python repo_quality.py
"""

import http.client
import json
import logging
import math
import re
import urllib.error
import urllib.request
from collections.abc import Callable
from pathlib import Path
from typing import TypeVar
from urllib.parse import urlparse

from common.config import ASSETS_DIR
from common.svg import escape_svg
from quality_sources import QUALITY_SOURCES, QualitySource

logger = logging.getLogger(__name__)
T = TypeVar("T")

_ALLOWED_HOST = "raw.githubusercontent.com"
_TESTS_RE = re.compile(r"^(\d+) passed$")
_COVERAGE_RE = re.compile(r"^(\d{1,3}(?:\.\d+)?)%$")

BADGE_HEIGHT = 20
LEFT_WIDTH = 58
RIGHT_WIDTH = 46
CORNER_RADIUS = 3
NEUTRAL_BG = "#555"  # same grey as the label of the header stars badge
COVERAGE_GOOD = "#1a7f37"  # white text contrast 5.1:1
COVERAGE_LOW = "#9a6700"  # white text contrast 4.9:1
COVERAGE_THRESHOLD = 90.0
MISSING = "–"
FONT = 'font-family="Verdana,Geneva,DejaVu Sans,sans-serif" font-size="11"'
CHECK_ICON = '<path d="M6 10.5l2.5 2.5 5-5.5" fill="none" stroke="#fff" stroke-width="1.8" stroke-linecap="round"/>'
TEXT_AREA_START = 18  # left of this sits the check icon
MAX_JSON_BYTES = 65536  # a badge JSON is ~100 bytes


class BadgeFetchError(Exception):
    """A badge JSON could not be downloaded or decoded."""


def parse_test_count(message: str) -> int | None:
    """Return the passed-test count, or None when the message is not a real result."""
    match = _TESTS_RE.match(message.strip())
    if not match or int(match.group(1)) == 0:
        return None
    return int(match.group(1))


def parse_coverage(message: str) -> float | None:
    """Return the coverage percentage, or None when the message is not a valid percentage."""
    match = _COVERAGE_RE.match(message.strip())
    if not match:
        return None
    value = float(match.group(1))
    # 0% is treated like "0 passed": an upstream glitch, never a real result here.
    return value if 0 < value <= 100 else None


def _truncate_one_decimal(value: float) -> str:
    # Truncate, never round up: 99.96% must not be shown as 100%.
    text = f"{math.floor(value * 10) / 10:.1f}"
    return text.removesuffix(".0")


def format_test_count(count: int) -> str:
    """Abbreviate counts from 1000 upwards: 1558 -> '1.5k', 12123 -> '12.1k'."""
    if count < 1000:
        return str(count)
    return f"{_truncate_one_decimal(count / 1000)}k"


def format_coverage(pct: float) -> str:
    """Format a coverage percentage with at most one decimal: 98.0 -> '98%'."""
    return f"{_truncate_one_decimal(pct)}%"


def coverage_color(pct: float) -> str:
    """Green from the threshold upwards, amber below."""
    return COVERAGE_GOOD if pct >= COVERAGE_THRESHOLD else COVERAGE_LOW


def _aria_label(tests: int | None, coverage: float | None) -> str:
    tests_part = f"{tests} tests passed" if tests is not None else "tests not available"
    coverage_part = f"{format_coverage(coverage)} coverage" if coverage is not None else "coverage not available"
    return f"{tests_part}, {coverage_part}"


def make_quality_badge(tests: int | None, coverage: float | None) -> str:
    """Render the fixed-width two-segment badge: grey test count, coloured coverage."""
    width = LEFT_WIDTH + RIGHT_WIDTH
    label = escape_svg(_aria_label(tests, coverage))
    right_bg = coverage_color(coverage) if coverage is not None else NEUTRAL_BG
    right_text = format_coverage(coverage) if coverage is not None else MISSING
    if tests is not None:
        icon, left_text, left_x = CHECK_ICON, format_test_count(tests), (TEXT_AREA_START + LEFT_WIDTH - 2) / 2
    else:
        icon, left_text, left_x = "", MISSING, LEFT_WIDTH / 2
    right_x = LEFT_WIDTH + RIGHT_WIDTH / 2

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{BADGE_HEIGHT}" role="img" aria-label="{label}">
  <title>{label}</title>
  <clipPath id="r"><rect width="{width}" height="{BADGE_HEIGHT}" rx="{CORNER_RADIUS}" fill="#fff"/></clipPath>
  <g clip-path="url(#r)">
    <rect width="{LEFT_WIDTH}" height="{BADGE_HEIGHT}" fill="{NEUTRAL_BG}"/>
    <rect x="{LEFT_WIDTH}" width="{RIGHT_WIDTH}" height="{BADGE_HEIGHT}" fill="{right_bg}"/>
  </g>
  {icon}
  <g fill="#fff" text-anchor="middle" {FONT}>
    <text x="{left_x:.0f}" y="14">{escape_svg(left_text)}</text>
    <text x="{right_x:.0f}" y="14">{escape_svg(right_text)}</text>
  </g>
</svg>'''


def fetch_badge_message(url: str) -> str:
    """Download a shields.io endpoint JSON and return its ``message`` field."""
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname != _ALLOWED_HOST:
        raise ValueError(f"URL host not allowed: {url}")
    request = urllib.request.Request(url, headers={"User-Agent": "profile-quality-badges"})  # noqa: S310  # nosec B310
    try:
        with urllib.request.urlopen(request, timeout=15) as resp:  # noqa: S310  # nosec B310
            payload = json.loads(resp.read(MAX_JSON_BYTES).decode("utf-8"))
    # OSError covers URLError and timeouts, HTTPException a truncated or dropped
    # read, ValueError bad JSON or UTF-8: none of them may stop the daily workflow.
    except (OSError, http.client.HTTPException, ValueError) as exc:
        raise BadgeFetchError(f"{url}: {exc}") from exc
    message = payload.get("message") if isinstance(payload, dict) else None
    if not isinstance(message, str):
        raise BadgeFetchError(f"{url}: no string 'message' field")
    return message


def _fetch_parsed(url: str, parser: Callable[[str], T | None]) -> tuple[T | None, bool]:
    """Return (value, ok): ok is False when the fetch failed or the value is not a real result."""
    try:
        value = parser(fetch_badge_message(url))
    except BadgeFetchError as exc:
        logger.warning("Fetch failed: %s", exc)
        return None, False
    if value is None:
        logger.warning("Upstream value is not a real result: %s", url)
    return value, value is not None


def build_badge(source: QualitySource) -> tuple[str, bool]:
    """Render the badge for ``source``; the flag is False if any endpoint value was missing."""
    tests_ok = coverage_ok = True
    if isinstance(source.tests, str):
        tests, tests_ok = _fetch_parsed(source.tests, parse_test_count)
    else:
        tests = source.tests or None
    if isinstance(source.coverage, str):
        coverage, coverage_ok = _fetch_parsed(source.coverage, parse_coverage)
    else:
        coverage = float(source.coverage)
    return make_quality_badge(tests=tests, coverage=coverage), tests_ok and coverage_ok


def write_quality_badges(sources: dict[str, QualitySource], out_dir: Path) -> int:
    """Write one badge per repo. If a value is missing the previous badge is kept.

    A glitch upstream ("0 passed", "pending", network error) must not replace a
    good badge with a dash; a dash is written only when there is no badge yet.

    Returns
    -------
    int
        Number of badge files written.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    written = 0
    kept: list[str] = []
    for name, source in sources.items():
        target = out_dir / f"{name}.svg"
        svg, complete = build_badge(source)
        if not complete and target.exists():
            kept.append(name)
            continue
        target.write_text(svg, encoding="utf-8")
        written += 1
    if kept:
        logger.warning("Kept previous badge for %d repo(s): %s", len(kept), ", ".join(kept))
    return written


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    out_dir = ASSETS_DIR / "quality"
    written = write_quality_badges(QUALITY_SOURCES, out_dir)
    logger.info("Generated %d quality badges in %s", written, out_dir)


if __name__ == "__main__":
    main()
