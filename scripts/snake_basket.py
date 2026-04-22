"""
Snake Basket — GitHub Contribution Graph Animator
Per: AndreaBonn | Ruolo: Center/Pivot | Scia: Palloni da basket

Genera una GIF animata dove un serpente "pivot" percorre il tuo
contribution graph lasciando palloni da basket sulle celle vuote.

Usage:
    python snake_basket.py --token YOUR_GITHUB_TOKEN
    python snake_basket.py --demo   (usa dati fittizi, no token richiesto)
"""

import argparse
import logging
import os
import random
from datetime import datetime, timedelta

import requests
from common.config import USERNAME
from snake_rendering import COLS, ROWS, generate_gif

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Dati demo (quando non si ha il token)
# ---------------------------------------------------------------------------


def generate_demo_data() -> tuple[list[list[int]], list[tuple]]:
    """Simula un anno di contributi realistici per AndreaBonn."""
    random.seed(42)  # seed fisso = riproducibile
    contributions = []
    month_labels = []

    today = datetime.today()
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
            if random.random() < prob:
                level = random.choices([1, 2, 3, 4], weights=[30, 35, 25, 10])[0]
            else:
                level = 0
            week_data.append(level)

        contributions.append(week_data)

    return contributions, month_labels


# ---------------------------------------------------------------------------
# Fetch dati reali da GitHub GraphQL API
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
    resp = requests.post(
        GITHUB_GRAPHQL, json={"query": QUERY, "variables": {"login": USERNAME}}, headers=headers, timeout=15
    )
    resp.raise_for_status()
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
        first_day = week["contributionDays"][0]["date"]
        month = datetime.strptime(first_day, "%Y-%m-%d").strftime("%b")

        if month != current_month:
            current_month = month
            month_labels.append((month, c))

        for day in week["contributionDays"]:
            count = day["contributionCount"]
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
    parser.add_argument("--token", help="GitHub Personal Access Token (read:user)")
    parser.add_argument("--demo", action="store_true", help="Usa dati demo senza token")
    parser.add_argument("--output", default="snake_basket.gif", help="Nome file output")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logger.info("Snake Basket — @%s", USERNAME)
    logger.info("=" * 40)

    token = args.token or os.environ.get("SNAKE_TOKEN", "")
    if args.demo:
        logger.info("Demo mode (explicit --demo flag)")
        contributions, month_labels = generate_demo_data()
    elif not token:
        logger.error("No GitHub token provided. Set SNAKE_TOKEN env var or use --token. Use --demo for test data.")
        raise SystemExit(1)
    else:
        logger.info("Fetching dati GitHub per @%s...", USERNAME)
        contributions, month_labels = fetch_github_data(token)

    total_cells = sum(1 for c in contributions for level in c if level == 0)
    logger.info("Celle vuote trovate: %d", total_cells)

    generate_gif(contributions, month_labels, args.output)
    logger.info("\nPer usarla nel README:\n")
    logger.info("![Snake Basket](./%s)", args.output)
    logger.info("\nOppure con GitHub Actions: vedi README per il workflow automatico.")


if __name__ == "__main__":
    main()
