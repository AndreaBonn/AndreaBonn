"""
NBA Today in History
Generates an SVG with a historical NBA event that happened on this date.
Output: assets/nba_today.svg
"""

import logging
import random
from datetime import UTC, datetime

from common.config import ASSETS_DIR
from common.svg import svg_lines, wrap_text

logger = logging.getLogger(__name__)

NBA_HISTORY: dict[tuple[int, int], list[dict[str, str]]] = {
    (1, 1): [{"text": "In 1970 the NBA All-Star Game reaches its 20th edition.", "icon": "🌟"}],
    (1, 7): [
        {"text": "In 1972 the Lakers win their 33rd consecutive game, an NBA record that still stands.", "icon": "🔥"}
    ],
    (1, 13): [{"text": "In 1990 Michael Jordan scores 61 points against Cleveland.", "icon": "💥"}],
    (1, 20): [
        {"text": "In 1968 Wilt Chamberlain becomes the first player to reach 25,000 career points.", "icon": "🏆"}
    ],
    (2, 3): [{"text": "In 1995 Michael Jordan plays his last game before his first retirement.", "icon": "😢"}],
    (2, 14): [{"text": "In 1990 the first Slam Dunk Contest won by Dominique Wilkins takes place.", "icon": "🏀"}],
    (2, 17): [{"text": "In 1963 Michael Jordan is born, widely considered the greatest of all time.", "icon": "🐐"}],
    (3, 2): [{"text": "In 1962 Wilt Chamberlain scores 100 points in a single game against the Knicks.", "icon": "💯"}],
    (3, 6): [
        {
            "text": "In 1987 Michael Jordan becomes the second player in history to score 3,000 points in a season.",
            "icon": "⚡",
        }
    ],
    (3, 18): [
        {"text": "In 1995 Michael Jordan announces his return with the legendary fax: 'I'm back'.", "icon": "👑"}
    ],
    (3, 24): [
        {
            "text": "In 2000 Vince Carter throws down what many call the dunk of the century at the Olympics.",
            "icon": "🚀",
        }
    ],
    (4, 5): [
        {"text": "In 2019 LeBron James passes Michael Jordan on the all-time playoff scoring list.", "icon": "👑"}
    ],
    (4, 9): [
        {
            "text": "In 2019 Dirk Nowitzki announces his retirement after 21 seasons with the Dallas Mavericks.",
            "icon": "🎯",
        }
    ],
    (4, 13): [{"text": "In 2016 Kobe Bryant ends his career with 60 points in his final game.", "icon": "🐍"}],
    (4, 20): [{"text": "In 1986 Michael Jordan scores 63 points against the Celtics in the playoffs.", "icon": "💣"}],
    (5, 7): [{"text": "In 1989 Magic Johnson wins his third Finals MVP award.", "icon": "✨"}],
    (5, 17): [
        {"text": "In 1996 the Chicago Bulls finish the regular season with 72 wins, a historic record.", "icon": "🏆"}
    ],
    (6, 1): [{"text": "In 2016 LeBron James leads Cleveland to a 3-1 comeback against Golden State.", "icon": "🔥"}],
    (6, 11): [
        {
            "text": "In 1997 Michael Jordan plays with a high fever and scores 38 points: the legendary 'Flu Game'.",
            "icon": "🤒",
        }
    ],
    (6, 12): [{"text": "In 2011 Dirk Nowitzki wins his only NBA title against the Miami Heat.", "icon": "🏆"}],
    (6, 14): [
        {
            "text": "In 1998 Michael Jordan hits the game-winning shot in Game 6 of the Finals: last title with the Bulls.",
            "icon": "🎯",
        }
    ],
    (6, 19): [
        {
            "text": "In 2016 the Cleveland Cavaliers win the first championship in franchise history, led by LeBron James.",
            "icon": "👑",
        }
    ],
    (7, 1): [{"text": "In 2010 LeBron James announces 'The Decision': leaving Cleveland for Miami.", "icon": "📺"}],
    (7, 4): [
        {"text": "In 2016 Kevin Durant signs with the Golden State Warriors, shaking the entire NBA.", "icon": "💣"}
    ],
    (8, 8): [{"text": "In 2008 Team USA wins Olympic gold in Beijing with the 'Redeem Team'.", "icon": "🥇"}],
    (8, 23): [
        {"text": "In 2020 Kobe Bryant would have turned 42. His numbers 8 and 24 remain retired in LA.", "icon": "💛"}
    ],
    (9, 9): [{"text": "In 2015 Kobe Bryant passes Michael Jordan on the all-time scoring list.", "icon": "🐍"}],
    (10, 15): [{"text": "In 1984 Michael Jordan makes his NBA debut with the Chicago Bulls.", "icon": "🌅"}],
    (11, 1): [
        {"text": "In 1950 Earl Lloyd becomes the first African American player to play in an NBA game.", "icon": "✊"}
    ],
    (11, 7): [{"text": "In 1991 Magic Johnson announces he is HIV positive, shocking the sports world.", "icon": "💔"}],
    (12, 6): [{"text": "In 1969 Wilt Chamberlain sets the all-time career rebounding record.", "icon": "📊"}],
    (12, 25): [
        {
            "text": "Every year on Christmas Day the NBA showcases the most anticipated games of the season.",
            "icon": "🎄",
        }
    ],
}

LINE_H: int = 28
SVG_W: int = 680


def get_today_event(today: datetime) -> dict[str, str]:
    key = (today.month, today.day)
    rng = random.Random(today.timetuple().tm_yday + today.year)
    if key in NBA_HISTORY:
        return rng.choice(NBA_HISTORY[key])
    all_events = [e for events in NBA_HISTORY.values() for e in events]
    return rng.choice(all_events)


def generate_svg(event: dict[str, str], today: datetime) -> str:
    lines = wrap_text(event["text"])
    svg_h = max(140, len(lines) * LINE_H + 130)
    icon = event["icon"]
    date_label = today.strftime("%B %d").upper()

    return f'''<svg width="{SVG_W}" height="{svg_h}" xmlns="http://www.w3.org/2000/svg">
  <rect width="{SVG_W}" height="{svg_h}" rx="12" fill="#161b22"/>
  <rect x="1" y="1" width="{SVG_W - 2}" height="{svg_h - 2}" rx="11" fill="none" stroke="#388bfd" stroke-width="1.5"/>

  <!-- event icon -->
  <rect x="16" y="16" width="52" height="52" rx="10" fill="#1c2128"/>
  <text x="42" y="50" font-size="26" text-anchor="middle">{icon}</text>

  <!-- header -->
  <text x="80" y="36" font-family="monospace" font-size="16" fill="#8b949e" letter-spacing="2">TODAY IN NBA HISTORY</text>
  <text x="80" y="58" font-family="monospace" font-size="15" fill="#388bfd">{date_label}</text>

  <!-- separator -->
  <line x1="24" y1="74" x2="{SVG_W - 24}" y2="74" stroke="#30363d" stroke-width="1"/>

  <!-- event text -->
  {svg_lines(lines, 100, line_height=LINE_H, svg_width=SVG_W)}

  <!-- footer -->
  <text x="{SVG_W - 24}" y="{svg_h - 12}" font-family="monospace" font-size="14" fill="#484f58" text-anchor="end">@AndreaBonn • NBA history</text>
</svg>'''


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    today = datetime.now(UTC)
    event = get_today_event(today)

    svg = generate_svg(event, today)

    out = ASSETS_DIR / "nba_today.svg"
    out.parent.mkdir(exist_ok=True)
    out.write_text(svg, encoding="utf-8")
    logger.info("nba_today.svg generated — %s %s...", event["icon"], event["text"][:40])


if __name__ == "__main__":
    main()
