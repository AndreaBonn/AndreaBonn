"""
GitHub Tamagotchi + Days since last commit
Generates two SVGs:
  - assets/tamagotchi.svg  → character that changes state based on commits
  - assets/last_commit.svg → days since last commit

Requires: GITHUB_TOKEN with read:user and public_repo permissions
Usage: python tamagotchi.py --token <TOKEN>
       python tamagotchi.py --demo --days <N>
"""

import argparse
import logging
import os
from datetime import UTC, datetime
from typing import TypedDict

import requests
from common.config import ASSETS_DIR, GITHUB_API, USERNAME
from common.svg import escape_svg, wrap_text
from common.visitors import fetch_visitor_count
from scoreboard import make_last_commit_svg


class StateInfo(TypedDict):
    days: tuple[int, int]
    color: str
    border: str
    msg: str
    face: str
    status: str


logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Fetch days since last commit (Search Commits API)
# ---------------------------------------------------------------------------


def fetch_days_since_last_commit(token: str) -> int | None:
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
    }
    try:
        resp = requests.get(
            f"{GITHUB_API}/search/commits",
            headers=headers,
            params={"q": f"author:{USERNAME}", "sort": "author-date", "order": "desc", "per_page": 1},
            timeout=15,
        )
        resp.raise_for_status()
    except requests.RequestException as exc:
        logger.error("fetch_days_since_last_commit: HTTP error: %s", exc)
        return None

    try:
        payload = resp.json()
    except requests.exceptions.JSONDecodeError as exc:
        logger.error("fetch_days_since_last_commit: non-JSON response: %s", exc)
        return None

    items = payload.get("items", []) if isinstance(payload, dict) else []
    if not items:
        logger.warning(
            "GitHub Search Commits API returned no items for author:%s — "
            "possible cause: new account, private commits only, or API delay.",
            USERNAME,
        )
        return None

    try:
        date_str = items[0]["commit"]["author"]["date"]
        dt = datetime.fromisoformat(date_str)
        delta = datetime.now(UTC) - dt
        return delta.days
    except (KeyError, ValueError) as exc:
        logger.error("fetch_days_since_last_commit: unexpected response structure: %s", exc)
        return None


# ---------------------------------------------------------------------------
# SVG: Tamagotchi
# ---------------------------------------------------------------------------

STATES = {
    "happy": {
        "days": (0, 2),
        "color": "#3fb950",
        "border": "#3fb950",
        "msg": "i'm happy! keep committing!",
        "face": """
          <circle cx="200" cy="120" r="60" fill="#1c2128" stroke="#3fb950" stroke-width="2"/>
          <circle cx="183" cy="110" r="6" fill="#3fb950"/>
          <circle cx="217" cy="110" r="6" fill="#3fb950"/>
          <path d="M183 130 Q200 148 217 130" fill="none" stroke="#3fb950" stroke-width="3" stroke-linecap="round"/>
          <circle cx="183" cy="108" r="2" fill="#161b22"/>
          <circle cx="217" cy="108" r="2" fill="#161b22"/>
          <!-- happy stars -->
          <text x="140" y="80" font-size="16">✨</text>
          <text x="248" y="80" font-size="16">✨</text>
        """,
        "status": "ON FIRE",
    },
    "good": {
        "days": (3, 5),
        "color": "#e6861a",
        "border": "#e6861a",
        "msg": "c'mon, one commit won't hurt...",
        "face": """
          <circle cx="200" cy="120" r="60" fill="#1c2128" stroke="#e6861a" stroke-width="2"/>
          <circle cx="183" cy="110" r="6" fill="#e6861a"/>
          <circle cx="217" cy="110" r="6" fill="#e6861a"/>
          <line x1="183" y1="135" x2="217" y2="135" stroke="#e6861a" stroke-width="3" stroke-linecap="round"/>
          <circle cx="183" cy="108" r="2" fill="#161b22"/>
          <circle cx="217" cy="108" r="2" fill="#161b22"/>
          <!-- question mark -->
          <text x="248" y="85" font-size="20">🤔</text>
        """,
        "status": "ON BREAK",
    },
    "tired": {
        "days": (6, 13),
        "color": "#f85149",
        "border": "#f85149",
        "msg": "i'm not okay... where did you go?",
        "face": """
          <circle cx="200" cy="120" r="60" fill="#1c2128" stroke="#f85149" stroke-width="2"/>
          <!-- X eyes -->
          <line x1="177" y1="104" x2="189" y2="116" stroke="#f85149" stroke-width="3"/>
          <line x1="189" y1="104" x2="177" y2="116" stroke="#f85149" stroke-width="3"/>
          <line x1="211" y1="104" x2="223" y2="116" stroke="#f85149" stroke-width="3"/>
          <line x1="223" y1="104" x2="211" y2="116" stroke="#f85149" stroke-width="3"/>
          <path d="M183 138 Q200 125 217 138" fill="none" stroke="#f85149" stroke-width="3" stroke-linecap="round"/>
          <!-- tears -->
          <ellipse cx="183" cy="124" rx="3" ry="5" fill="#388bfd" opacity="0.7"/>
          <ellipse cx="217" cy="124" rx="3" ry="5" fill="#388bfd" opacity="0.7"/>
          <text x="140" y="85" font-size="16">💔</text>
        """,
        "status": "TIRED",
    },
    "dead": {
        "days": (14, 9999),
        "color": "#484f58",
        "border": "#484f58",
        "msg": "i'm dead. the coach called. nobody answered.",
        "face": """
          <circle cx="200" cy="120" r="60" fill="#0d1117" stroke="#484f58" stroke-width="2"/>
          <!-- large X eyes -->
          <line x1="174" y1="101" x2="192" y2="119" stroke="#484f58" stroke-width="4"/>
          <line x1="192" y1="101" x2="174" y2="119" stroke="#484f58" stroke-width="4"/>
          <line x1="208" y1="101" x2="226" y2="119" stroke="#484f58" stroke-width="4"/>
          <line x1="226" y1="101" x2="208" y2="119" stroke="#484f58" stroke-width="4"/>
          <path d="M183 138 Q200 125 217 138" fill="none" stroke="#484f58" stroke-width="3" stroke-linecap="round"/>
          <!-- tombstone -->
          <text x="160" y="85" font-size="22">🪦</text>
          <!-- ghost -->
          <text x="248" y="78" font-size="20">👻</text>
        """,
        "status": "RIP",
    },
}


def get_state(days: int) -> StateInfo:
    for state in STATES.values():
        lo, hi = state["days"]
        if lo <= days <= hi:
            return state
    return STATES["dead"]


def wrap_msg(text: str, max_chars: int = 52) -> list[str]:
    return wrap_text(text, max_chars=max_chars)


def make_tamagotchi_svg(days: int) -> str:
    state = get_state(days)
    msg_lines = wrap_msg(state["msg"])
    msg_svg = ""
    for i, line in enumerate(msg_lines):
        msg_svg += f'<text x="340" y="{230 + i * 22}" font-family="monospace" font-size="13" fill="{state["color"]}" text-anchor="middle" font-style="italic">{escape_svg(line)}</text>\n'

    return f'''<svg width="680" height="300" xmlns="http://www.w3.org/2000/svg">
  <rect width="680" height="300" rx="12" fill="#161b22"/>
  <rect x="1" y="1" width="678" height="298" rx="11" fill="none" stroke="{state["border"]}" stroke-width="1.5"/>

  <!-- header -->
  <text x="24" y="32" font-family="monospace" font-size="11" fill="#8b949e" letter-spacing="2">GITHUB TAMAGOTCHI</text>
  <text x="24" y="52" font-family="monospace" font-size="11" fill="{state["color"]}">@AndreaBonn — {state["status"]}</text>

  <!-- separator -->
  <line x1="24" y1="64" x2="656" y2="64" stroke="#30363d" stroke-width="1"/>

  <!-- tamagotchi screen -->
  <rect x="120" y="74" width="160" height="160" rx="16" fill="#0d1117" stroke="{state["border"]}" stroke-width="1.5"/>

  <!-- character -->
  <g transform="translate(-80, 0)">
    {state["face"]}
  </g>

  <!-- days badge -->
  <rect x="300" y="80" width="120" height="40" rx="8" fill="#1c2128" stroke="{state["border"]}" stroke-width="1"/>
  <text x="360" y="97" font-family="monospace" font-size="10" fill="#8b949e" text-anchor="middle">days without commit</text>
  <text x="360" y="114" font-family="monospace" font-size="22" fill="{state["color"]}" text-anchor="middle" font-weight="bold">{days}</text>

  <!-- health bar -->
  <text x="300" y="144" font-family="monospace" font-size="10" fill="#8b949e">health</text>
  <rect x="300" y="150" width="340" height="8" rx="4" fill="#21262d"/>
  <rect x="300" y="150" width="{max(4, 340 - days * 22):.0f}" height="8" rx="4" fill="{state["color"]}"/>

  <!-- message -->
  {msg_svg}

  <!-- tamagotchi-style buttons -->
  <circle cx="300" cy="278" r="8" fill="#21262d" stroke="{state["border"]}" stroke-width="1"/>
  <circle cx="340" cy="278" r="8" fill="#21262d" stroke="{state["border"]}" stroke-width="1"/>
  <circle cx="380" cy="278" r="8" fill="#21262d" stroke="{state["border"]}" stroke-width="1"/>

  <!-- footer -->
  <text x="656" y="291" font-family="monospace" font-size="10" fill="#484f58" text-anchor="end">commit to keep me alive</text>
</svg>'''


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser()
    parser.add_argument("--token", help="GitHub token")
    parser.add_argument("--demo", action="store_true")
    parser.add_argument("--days", type=int, default=3, help="Days to simulate in demo mode")
    parser.add_argument("--visitors", type=int, default=None, help="Visitors to simulate in demo mode")
    args = parser.parse_args()

    token = args.token or os.environ.get("SNAKE_TOKEN", "")
    if args.demo:
        days = args.days
        visitors = args.visitors if args.visitors is not None else 42
        total_visitors = visitors * 10
        logger.info("Demo mode — %d days, %d recent, %d total", days, visitors, total_visitors)
    elif not token:
        logger.error("No GitHub token provided. Set SNAKE_TOKEN env var or use --token. Use --demo for test data.")
        raise SystemExit(1)
    else:
        logger.info("Fetching data for @%s...", USERNAME)
        days = fetch_days_since_last_commit(token)
        if days is None:
            logger.error("Could not determine days since last commit — aborting")
            raise SystemExit(1)
        visitors, total_visitors = fetch_visitor_count()

    logger.info("Days since last commit: %d", days)
    logger.info("Recent views: %d | Total views: %d", visitors, total_visitors)
    state = get_state(days)
    logger.info("Tamagotchi status: %s", state["status"])

    ASSETS_DIR.mkdir(exist_ok=True)

    try:
        (ASSETS_DIR / "tamagotchi.svg").write_text(make_tamagotchi_svg(days), encoding="utf-8")
        (ASSETS_DIR / "last_commit.svg").write_text(
            make_last_commit_svg(days, visitors=visitors, total_visitors=total_visitors),
            encoding="utf-8",
        )
    except OSError as exc:
        logger.error("Failed to write SVG files to %s: %s", ASSETS_DIR, exc)
        raise SystemExit(1) from exc

    logger.info("tamagotchi.svg generated")
    logger.info("last_commit.svg generated")


if __name__ == "__main__":
    main()
