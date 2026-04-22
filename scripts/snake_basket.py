"""
Snake Basket — GitHub Contribution Graph Animator
For: AndreaBonn | Role: Center/Pivot | Trail: Basketballs

Generates an animated GIF where a "pivot" snake traverses your
contribution graph leaving basketballs on empty cells.

Usage:
    SNAKE_TOKEN=<TOKEN> python snake_basket.py
    python snake_basket.py --demo   (uses demo data, no token required)
"""

import argparse
import logging
import os
import random
from datetime import UTC, datetime, timedelta

import requests
from common.config import USERNAME
from snake_rendering import COLS, ROWS, generate_gif

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Demo data (when no token is available)
# ---------------------------------------------------------------------------


def generate_demo_data() -> tuple[list[list[int]], list[tuple]]:
    """Simulate a year of realistic contributions for AndreaBonn."""
    random.seed(42)  # nosec B311 — fixed seed for reproducible demo data
    contributions = []
    month_labels = []

    today = datetime.now(UTC)
    start = today - timedelta(weeks=52)

    current_month = None
    for c in range(COLS):
        week_data = []
        week_date = start + timedelta(weeks=c)

        m = week_date.strftime("%b")
        if m != current_month:
            current_month = m
            month_labels.append((m, c))

        for r in range(ROWS):
            day = week_date + timedelta(days=r)
            if day > today:
                week_data.append(0)
                continue
            is_weekday = r < 5
            prob = 0.55 if is_weekday else 0.15
            if random.random() < prob:  # nosec B311
                level = random.choices([1, 2, 3, 4], weights=[30, 35, 25, 10])[0]  # nosec B311
            else:
                level = 0
            week_data.append(level)

        contributions.append(week_data)

    return contributions, month_labels


# ---------------------------------------------------------------------------
# Fetch real data from GitHub GraphQL API
# ---------------------------------------------------------------------------

GITHUB_GRAPHQL = "https://api.github.com/graphql"

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        weeks {
          contributionDays {
            contributionCount
            date
          }
        }
      }
    }
  }
}
"""


def fetch_github_data(token: str) -> tuple[list[list[int]], list[tuple]]:
    headers = {"Authorization": f"bearer {token}"}
    try:
        resp = requests.post(
            GITHUB_GRAPHQL, json={"query": QUERY, "variables": {"login": USERNAME}}, headers=headers, timeout=15
        )
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise RuntimeError(f"GitHub GraphQL network error: {exc}") from exc
    data = resp.json()

    if "errors" in data:
        raise RuntimeError(f"GitHub GraphQL API error: {data['errors']}")

    user_data = data.get("data", {}).get("user")
    if user_data is None:
        raise RuntimeError(
            f"GitHub GraphQL: user '{USERNAME}' not found or not accessible. Check USERNAME and token permissions."
        )

    try:
        weeks = user_data["contributionsCollection"]["contributionCalendar"]["weeks"]
    except KeyError as exc:
        raise RuntimeError(
            f"GitHub GraphQL response missing expected field {exc} — API schema may have changed"
        ) from exc

    contributions = []
    month_labels = []
    current_month = None

    for c, week in enumerate(weeks[-52:]):
        week_data = []
        days_in_week = week.get("contributionDays", [])
        if not days_in_week:
            logger.warning("fetch_github_data: week %d has no contributionDays — skipping", c)
            contributions.append([0] * ROWS)
            continue
        try:
            first_day = days_in_week[0]["date"]
            month = datetime.strptime(first_day, "%Y-%m-%d").strftime("%b")
        except (KeyError, ValueError) as exc:
            logger.warning("fetch_github_data: unexpected day format in week %d: %s — skipping", c, exc)
            contributions.append([0] * ROWS)
            continue

        if month != current_month:
            current_month = month
            month_labels.append((month, c))

        for day in days_in_week:
            count = day.get("contributionCount")
            if count is None:
                logger.warning(
                    "fetch_github_data: missing contributionCount in day %s — defaulting to 0",
                    day.get("date", "?"),
                )
                count = 0
            if count == 0:
                level = 0
            elif count <= 3:
                level = 1
            elif count <= 6:
                level = 2
            elif count <= 9:
                level = 3
            else:
                level = 4
            week_data.append(level)

        while len(week_data) < 7:
            week_data.append(0)

        contributions.append(week_data)

    return contributions, month_labels


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description="Snake Basket — GitHub contribution animator")
    parser.add_argument("--demo", action="store_true", help="Use demo data without token")
    parser.add_argument("--output", default="snake_basket.gif", help="Nome file output")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logger.info("Snake Basket — @%s", USERNAME)
    logger.info("=" * 40)

    token = os.environ.get("SNAKE_TOKEN", "")
    if args.demo:
        logger.info("Demo mode (explicit --demo flag)")
        contributions, month_labels = generate_demo_data()
    elif not token:
        logger.error("No GitHub token provided. Set SNAKE_TOKEN env var. Use --demo for test data.")
        raise SystemExit(1)
    else:
        logger.info("Fetching GitHub data for @%s...", USERNAME)
        contributions, month_labels = fetch_github_data(token)

    total_cells = sum(1 for c in contributions for level in c if level == 0)
    logger.info("Empty cells found: %d", total_cells)

    generate_gif(contributions, month_labels, args.output)
    logger.info("\nTo use in your README:\n")
    logger.info("![Snake Basket](./%s)", args.output)
    logger.info("\nOr with GitHub Actions: see README for the automated workflow.")


if __name__ == "__main__":
    main()
