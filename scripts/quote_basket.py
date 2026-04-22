"""
Quote del giorno — Basket
Genera un SVG con una citazione NBA diversa ogni giorno.
Output: assets/quote.svg
"""

import logging
import random
from datetime import UTC, datetime

from common.config import ASSETS_DIR
from common.svg import escape_svg, svg_lines, wrap_text

logger = logging.getLogger(__name__)

QUOTES: list[dict[str, str]] = [
    {
        "text": "I've missed more than 9,000 shots in my career. I've lost almost 300 games. I've failed over and over again. And that is why I succeed.",
        "author": "Michael Jordan",
    },
    {
        "text": "The most important thing is to try and inspire people so that they can be great in whatever they want to do.",
        "author": "Kobe Bryant",
    },
    {"text": "You can't win without talent, but you can't win on talent alone.", "author": "Larry Bird"},
    {
        "text": "Ask not what your teammates can do for you. Ask what you can do for your teammates.",
        "author": "Magic Johnson",
    },
    {
        "text": "Good, better, best. Never let it rest. Until your good is better and your better is best.",
        "author": "Tim Duncan",
    },
    {"text": "I like criticism. It makes you strong.", "author": "LeBron James"},
    {"text": "The only way to do great work is to love what you do.", "author": "Kobe Bryant"},
    {"text": "Talent wins games, but teamwork and intelligence wins championships.", "author": "Michael Jordan"},
    {"text": "Dedication makes dreams come true.", "author": "Julius Erving"},
    {"text": "Hard work beats talent when talent doesn't work hard.", "author": "Kevin Durant"},
    {
        "text": "In basketball, you can be the best player, but if you don't work together as a team, it means nothing.",
        "author": "Scottie Pippen",
    },
    {
        "text": "Everything negative — pressure, challenges — is all an opportunity for me to rise.",
        "author": "Kobe Bryant",
    },
    {
        "text": "The strength of the team is each individual member. The strength of each member is the team.",
        "author": "Phil Jackson",
    },
    {"text": "You have to expect things of yourself before you can do them.", "author": "Michael Jordan"},
    {
        "text": "I'll do whatever it takes to win games, whether it's sitting on a bench waving a towel, handing a cup of water to a teammate.",
        "author": "Michael Jordan",
    },
    {
        "text": "Great players are willing to give up their own personal achievement for the achievement of the group.",
        "author": "Kareem Abdul-Jabbar",
    },
    {"text": "Pain is temporary. Quitting lasts forever.", "author": "Kobe Bryant"},
    {"text": "Be the hardest worker in every room you walk into.", "author": "LeBron James"},
    {
        "text": "Championships are not won in the locker rooms or on paper. They are won on the court.",
        "author": "John Wooden",
    },
    {
        "text": "The best teams have chemistry, but chemistry is not enough. You also need talent.",
        "author": "Pat Riley",
    },
    {
        "text": "Push yourself again and again. Don't give an inch until the final buzzer sounds.",
        "author": "Larry Bird",
    },
    {"text": "Success is not owned. It's leased, and rent is due every day.", "author": "J.J. Watt"},
    {
        "text": "I can accept failure. Everyone fails at something. But I can't accept not trying.",
        "author": "Michael Jordan",
    },
    {
        "text": "Mamba mentality is all about focusing on the process and doing whatever it takes.",
        "author": "Kobe Bryant",
    },
    {
        "text": "The game has its ups and downs, but you can never lose focus of your individual goals.",
        "author": "Michael Jordan",
    },
    {
        "text": "Once you are labeled 'the best' you want to stay up there, and you can't do it by loafing around.",
        "author": "Larry Bird",
    },
    {"text": "You have to be able to accept failure to get better.", "author": "LeBron James"},
    {"text": "Winning is about heart, not just legs. It's got to be in the right place.", "author": "Ronnie Lott"},
    {
        "text": "I never feared about my skills because I put in the work. Work ethic eliminates fear.",
        "author": "Michael Jordan",
    },
    {"text": "The only way out is through.", "author": "Bill Russell"},
    {"text": "A champion is someone who gets up when they can't.", "author": "Jack Dempsey"},
    {"text": "First master the fundamentals.", "author": "Larry Bird"},
    {"text": "Shoot for the stars so if you miss you'll still be among the clouds.", "author": "Kareem Abdul-Jabbar"},
    {
        "text": "To be a great champion you must believe you are the best. If you're not, pretend you are.",
        "author": "Muhammad Ali",
    },
    {"text": "Success is no accident. It is hard work, perseverance, learning, studying, sacrifice.", "author": "Pelé"},
    {"text": "The game is won at practice.", "author": "Coach John Wooden"},
]

LINE_H: int = 28
SVG_W: int = 680


def pick_daily_quote() -> dict[str, str]:
    today = datetime.now(UTC).date()
    random.seed(today.toordinal())
    return random.choice(QUOTES)


def generate_svg(quote: dict[str, str], today: datetime) -> str:
    lines = wrap_text(quote["text"])
    text_h = len(lines) * LINE_H
    svg_h = text_h + 130

    author = escape_svg(quote["author"])
    date_str = today.strftime("%d %b %Y")

    return f'''<svg width="{SVG_W}" height="{svg_h}" xmlns="http://www.w3.org/2000/svg">
  <rect width="{SVG_W}" height="{svg_h}" rx="12" fill="#161b22"/>
  <rect x="1" y="1" width="{SVG_W - 2}" height="{svg_h - 2}" rx="11" fill="none" stroke="#e6861a" stroke-width="1.5"/>

  <!-- pallone decorativo -->
  <circle cx="44" cy="44" r="26" fill="#e6861a"/>
  <line x1="44" y1="18" x2="44" y2="70" stroke="#c0580a" stroke-width="2"/>
  <line x1="18" y1="44" x2="70" y2="44" stroke="#c0580a" stroke-width="2"/>
  <path d="M30 24 Q44 38 30 64" fill="none" stroke="#c0580a" stroke-width="2"/>
  <path d="M58 24 Q44 38 58 64" fill="none" stroke="#c0580a" stroke-width="2"/>
  <circle cx="44" cy="44" r="26" fill="none" stroke="#c0580a" stroke-width="1.5"/>

  <!-- header -->
  <text x="80" y="36" font-family="monospace" font-size="16" fill="#8b949e" letter-spacing="2">QUOTE OF THE DAY</text>
  <text x="80" y="58" font-family="monospace" font-size="15" fill="#e6861a">&#x1F3C0; @AndreaBonn</text>

  <!-- separatore -->
  <line x1="24" y1="74" x2="{SVG_W - 24}" y2="74" stroke="#30363d" stroke-width="1"/>

  <!-- citazione -->
  {svg_lines(lines, 100, line_height=LINE_H, svg_width=SVG_W, italic=True)}

  <!-- autore -->
  <text x="{SVG_W - 24}" y="{svg_h - 32}" font-family="monospace" font-size="18" fill="#e6861a" text-anchor="end" font-weight="bold">— {author}</text>
  <text x="{SVG_W - 24}" y="{svg_h - 12}" font-family="monospace" font-size="14" fill="#484f58" text-anchor="end">{date_str}</text>
</svg>'''


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    today = datetime.now(UTC)
    quote = pick_daily_quote()

    svg = generate_svg(quote, today)

    out = ASSETS_DIR / "quote.svg"
    out.parent.mkdir(exist_ok=True)
    out.write_text(svg, encoding="utf-8")
    logger.info("quote.svg generato — %s", quote["author"])


if __name__ == "__main__":
    main()
