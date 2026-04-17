"""
GitHub Tamagotchi + Giorni dall'ultimo commit
Genera due SVG:
  - assets/tamagotchi.svg  → personaggio che cambia stato in base ai commit
  - assets/last_commit.svg → giorni passati dall'ultimo commit

Richiede: GITHUB_TOKEN con permesso read:user e public_repo
Usage: python tamagotchi.py --token <TOKEN>
       python tamagotchi.py --demo --days <N>
"""

import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import requests
except ImportError:
    requests = None

USERNAME = "AndreaBonn"
GITHUB_API = "https://api.github.com"

# ---------------------------------------------------------------------------
# Fetch giorni dall'ultimo commit (eventi pubblici)
# ---------------------------------------------------------------------------

def fetch_days_since_last_commit(token: str) -> int:
    if requests is None:
        return 0
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github+json"}
    # Cerca negli eventi pubblici i PushEvent
    resp = requests.get(f"{GITHUB_API}/users/{USERNAME}/events/public",
                        headers=headers, params={"per_page": 100}, timeout=15)
    resp.raise_for_status()
    events = resp.json()
    for event in events:
        if event.get("type") == "PushEvent":
            created = event.get("created_at", "")
            if created:
                dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                delta = datetime.now(timezone.utc) - dt
                return delta.days
    return 99  # nessun push trovato recentemente

# ---------------------------------------------------------------------------
# SVG: giorni dall'ultimo commit
# ---------------------------------------------------------------------------

def make_last_commit_svg(days: int) -> str:
    if days == 0:
        color = "#3fb950"
        label = "oggi — fresco di commit!"
        bar_w = 600
    elif days <= 2:
        color = "#3fb950"
        label = f"{days} {'giorno' if days == 1 else 'giorni'} fa — ottimo ritmo"
        bar_w = max(60, 600 - days * 80)
    elif days <= 5:
        color = "#e6861a"
        label = f"{days} giorni fa — stai scaldando?"
        bar_w = max(60, 600 - days * 60)
    elif days <= 14:
        color = "#f85149"
        label = f"{days} giorni fa — torna in campo!"
        bar_w = max(30, 200 - days * 8)
    else:
        color = "#8b949e"
        label = f"{days} giorni fa — il coach ti cerca"
        bar_w = 20

    bar_pct = min(100, max(3, int(bar_w / 6)))

    return f'''<svg width="680" height="90" xmlns="http://www.w3.org/2000/svg">
  <rect width="680" height="90" rx="12" fill="#161b22"/>
  <rect x="1" y="1" width="678" height="88" rx="11" fill="none" stroke="{color}" stroke-width="1.5"/>

  <!-- icona orologio -->
  <circle cx="42" cy="45" r="22" fill="#1c2128" stroke="{color}" stroke-width="1.5"/>
  <line x1="42" y1="28" x2="42" y2="45" stroke="{color}" stroke-width="2" stroke-linecap="round"/>
  <line x1="42" y1="45" x2="54" y2="52" stroke="{color}" stroke-width="2" stroke-linecap="round"/>

  <text x="76" y="32" font-family="monospace" font-size="11" fill="#8b949e" letter-spacing="2">ULTIMO COMMIT</text>
  <text x="76" y="52" font-family="monospace" font-size="16" fill="{color}" font-weight="bold">{label}</text>

  <!-- barra progressione -->
  <rect x="76" y="62" width="580" height="6" rx="3" fill="#21262d"/>
  <rect x="76" y="62" width="{bar_pct*5.8:.0f}" height="6" rx="3" fill="{color}"/>
</svg>'''

# ---------------------------------------------------------------------------
# SVG: Tamagotchi
# ---------------------------------------------------------------------------

STATES = {
    "happy": {
        "days": (0, 2),
        "color": "#3fb950",
        "border": "#3fb950",
        "msg": "sono felice! continua a committare!",
        "face": '''
          <circle cx="200" cy="120" r="60" fill="#1c2128" stroke="#3fb950" stroke-width="2"/>
          <circle cx="183" cy="110" r="6" fill="#3fb950"/>
          <circle cx="217" cy="110" r="6" fill="#3fb950"/>
          <path d="M183 130 Q200 148 217 130" fill="none" stroke="#3fb950" stroke-width="3" stroke-linecap="round"/>
          <circle cx="183" cy="108" r="2" fill="#161b22"/>
          <circle cx="217" cy="108" r="2" fill="#161b22"/>
          <!-- stelle felici -->
          <text x="140" y="80" font-size="16">✨</text>
          <text x="248" y="80" font-size="16">✨</text>
        ''',
        "status": "IN FORMA"
    },
    "good": {
        "days": (3, 5),
        "color": "#e6861a",
        "border": "#e6861a",
        "msg": "dai, un commit non fa male...",
        "face": '''
          <circle cx="200" cy="120" r="60" fill="#1c2128" stroke="#e6861a" stroke-width="2"/>
          <circle cx="183" cy="110" r="6" fill="#e6861a"/>
          <circle cx="217" cy="110" r="6" fill="#e6861a"/>
          <line x1="183" y1="135" x2="217" y2="135" stroke="#e6861a" stroke-width="3" stroke-linecap="round"/>
          <circle cx="183" cy="108" r="2" fill="#161b22"/>
          <circle cx="217" cy="108" r="2" fill="#161b22"/>
          <!-- punto interrogativo -->
          <text x="248" y="85" font-size="20">🤔</text>
        ''',
        "status": "IN PAUSA"
    },
    "tired": {
        "days": (6, 13),
        "color": "#f85149",
        "border": "#f85149",
        "msg": "sto male... dove sei andato?",
        "face": '''
          <circle cx="200" cy="120" r="60" fill="#1c2128" stroke="#f85149" stroke-width="2"/>
          <!-- occhi a X -->
          <line x1="177" y1="104" x2="189" y2="116" stroke="#f85149" stroke-width="3"/>
          <line x1="189" y1="104" x2="177" y2="116" stroke="#f85149" stroke-width="3"/>
          <line x1="211" y1="104" x2="223" y2="116" stroke="#f85149" stroke-width="3"/>
          <line x1="223" y1="104" x2="211" y2="116" stroke="#f85149" stroke-width="3"/>
          <path d="M183 138 Q200 125 217 138" fill="none" stroke="#f85149" stroke-width="3" stroke-linecap="round"/>
          <!-- lacrime -->
          <ellipse cx="183" cy="124" rx="3" ry="5" fill="#388bfd" opacity="0.7"/>
          <ellipse cx="217" cy="124" rx="3" ry="5" fill="#388bfd" opacity="0.7"/>
          <text x="140" y="85" font-size="16">💔</text>
        ''',
        "status": "STANCO"
    },
    "dead": {
        "days": (14, 9999),
        "color": "#484f58",
        "border": "#484f58",
        "msg": "sono morto. il coach ha chiamato. non ha risposto nessuno.",
        "face": '''
          <circle cx="200" cy="120" r="60" fill="#0d1117" stroke="#484f58" stroke-width="2"/>
          <!-- occhi a X grandi -->
          <line x1="174" y1="101" x2="192" y2="119" stroke="#484f58" stroke-width="4"/>
          <line x1="192" y1="101" x2="174" y2="119" stroke="#484f58" stroke-width="4"/>
          <line x1="208" y1="101" x2="226" y2="119" stroke="#484f58" stroke-width="4"/>
          <line x1="226" y1="101" x2="208" y2="119" stroke="#484f58" stroke-width="4"/>
          <path d="M183 138 Q200 125 217 138" fill="none" stroke="#484f58" stroke-width="3" stroke-linecap="round"/>
          <!-- lapide -->
          <text x="160" y="85" font-size="22">🪦</text>
          <!-- spiritello -->
          <text x="248" y="78" font-size="20">👻</text>
        ''',
        "status": "RIP"
    },
}

def get_state(days: int) -> dict:
    for state in STATES.values():
        lo, hi = state["days"]
        if lo <= days <= hi:
            return state
    return STATES["dead"]

def wrap_msg(text, max_chars=52):
    words = text.split()
    lines, line = [], ""
    for w in words:
        if len(line) + len(w) + 1 <= max_chars:
            line += ("" if not line else " ") + w
        else:
            lines.append(line); line = w
    if line: lines.append(line)
    return lines

def make_tamagotchi_svg(days: int) -> str:
    state = get_state(days)
    msg_lines = wrap_msg(state["msg"])
    msg_svg = ""
    for i, l in enumerate(msg_lines):
        msg_svg += f'<text x="340" y="{230 + i*22}" font-family="monospace" font-size="13" fill="{state["color"]}" text-anchor="middle" font-style="italic">{l}</text>\n'

    return f'''<svg width="680" height="300" xmlns="http://www.w3.org/2000/svg">
  <rect width="680" height="300" rx="12" fill="#161b22"/>
  <rect x="1" y="1" width="678" height="298" rx="11" fill="none" stroke="{state["border"]}" stroke-width="1.5"/>

  <!-- header -->
  <text x="24" y="32" font-family="monospace" font-size="11" fill="#8b949e" letter-spacing="2">GITHUB TAMAGOTCHI</text>
  <text x="24" y="52" font-family="monospace" font-size="11" fill="{state["color"]}">@AndreaBonn — {state["status"]}</text>

  <!-- separatore -->
  <line x1="24" y1="64" x2="656" y2="64" stroke="#30363d" stroke-width="1"/>

  <!-- schermo tamagotchi -->
  <rect x="120" y="74" width="160" height="160" rx="16" fill="#0d1117" stroke="{state["border"]}" stroke-width="1.5"/>

  <!-- personaggio -->
  <g transform="translate(-80, 0)">
    {state["face"]}
  </g>

  <!-- giorni badge -->
  <rect x="300" y="80" width="120" height="40" rx="8" fill="#1c2128" stroke="{state["border"]}" stroke-width="1"/>
  <text x="360" y="97" font-family="monospace" font-size="10" fill="#8b949e" text-anchor="middle">giorni senza commit</text>
  <text x="360" y="114" font-family="monospace" font-size="22" fill="{state["color"]}" text-anchor="middle" font-weight="bold">{days}</text>

  <!-- barra vitale -->
  <text x="300" y="144" font-family="monospace" font-size="10" fill="#8b949e">vita</text>
  <rect x="300" y="150" width="340" height="8" rx="4" fill="#21262d"/>
  <rect x="300" y="150" width="{max(4, 340 - days * 22):.0f}" height="8" rx="4" fill="{state["color"]}"/>

  <!-- messaggio -->
  {msg_svg}

  <!-- pulsanti stile tamagotchi -->
  <circle cx="300" cy="278" r="8" fill="#21262d" stroke="{state["border"]}" stroke-width="1"/>
  <circle cx="340" cy="278" r="8" fill="#21262d" stroke="{state["border"]}" stroke-width="1"/>
  <circle cx="380" cy="278" r="8" fill="#21262d" stroke="{state["border"]}" stroke-width="1"/>

  <!-- footer -->
  <text x="656" y="291" font-family="monospace" font-size="10" fill="#484f58" text-anchor="end">commit to keep me alive</text>
</svg>'''

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--token", help="GitHub token")
    parser.add_argument("--demo", action="store_true")
    parser.add_argument("--days", type=int, default=3, help="Giorni da simulare in demo")
    args = parser.parse_args()

    token = args.token or os.environ.get("SNAKE_TOKEN", "")
    if args.demo or not token:
        days = args.days
        print(f"Demo mode — simulando {days} giorni senza commit")
    else:
        print(f"Fetching dati per @{USERNAME}...")
        days = fetch_days_since_last_commit(token)

    print(f"Giorni dall'ultimo commit: {days}")
    state = get_state(days)
    print(f"Stato tamagotchi: {state['status']}")

    base = Path(__file__).parent.parent / "assets"
    base.mkdir(exist_ok=True)

    (base / "tamagotchi.svg").write_text(make_tamagotchi_svg(days), encoding="utf-8")
    (base / "last_commit.svg").write_text(make_last_commit_svg(days), encoding="utf-8")

    print("tamagotchi.svg generato")
    print("last_commit.svg generato")

if __name__ == "__main__":
    main()
