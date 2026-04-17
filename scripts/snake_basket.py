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
import math
import os
import random
import sys
from datetime import datetime, timedelta

try:
    import requests
except ImportError:
    requests = None

from PIL import Image, ImageDraw

# ---------------------------------------------------------------------------
# Configurazione visiva
# ---------------------------------------------------------------------------

USERNAME = "AndreaBonn"

CELL_SIZE   = 13   # px per cella del contribution graph
CELL_GAP    = 3    # gap tra celle
COLS        = 52   # settimane
ROWS        = 7    # giorni (lun-dom)
PAD_LEFT    = 36   # spazio per etichette giorni
PAD_TOP     = 28   # spazio per etichette mesi
PAD_RIGHT   = 16
PAD_BOTTOM  = 16

CANVAS_W = PAD_LEFT + COLS * (CELL_SIZE + CELL_GAP) - CELL_GAP + PAD_RIGHT
CANVAS_H = PAD_TOP  + ROWS * (CELL_SIZE + CELL_GAP) - CELL_GAP + PAD_BOTTOM

# Palette colori contribution graph (tema basket: arancio + verde campo)
BG_COLOR        = (22, 27, 34)       # sfondo scuro GitHub-style
EMPTY_COLOR     = (30, 40, 50)       # cella vuota
CONTRIB_COLORS  = [
    (14, 68, 41),    # livello 1 — verde scuro
    (0, 109, 50),    # livello 2
    (38, 166, 78),   # livello 3
    (57, 211, 83),   # livello 4 — verde brillante
]
TEXT_COLOR      = (139, 148, 158)    # grigio GitHub
GRID_LINE_COLOR = (48, 54, 61)

# Colori basket
SNAKE_HEAD_COLOR = (255, 140, 0)     # arancio NBA
SNAKE_BODY_COLOR = (200, 100, 0)     # arancio scuro

# ---------------------------------------------------------------------------
# Disegno pallone da basket (SVG-style con Pillow)
# ---------------------------------------------------------------------------

def draw_basketball(draw: ImageDraw.ImageDraw, cx: int, cy: int, r: int):
    """Disegna un pallone da basket stilizzato nella cella."""
    # Corpo arancio
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(230, 90, 20))
    # Linee caratteristiche del pallone
    lc = (180, 50, 0)
    lw = max(1, r // 5)
    # Linea verticale
    draw.arc([cx - r, cy - r, cx + r, cy + r], start=0, end=360, fill=lc, width=lw)
    draw.line([cx, cy - r, cx, cy + r], fill=lc, width=lw)
    # Linea orizzontale
    draw.line([cx - r, cy, cx + r, cy], fill=lc, width=lw)
    # Curve laterali
    offset = int(r * 0.55)
    draw.arc([cx - r - offset, cy - r, cx + r - offset, cy + r],
             start=320, end=40, fill=lc, width=lw)
    draw.arc([cx - r + offset, cy - r, cx + r + offset, cy + r],
             start=140, end=220, fill=lc, width=lw)

def draw_snake_head(draw: ImageDraw.ImageDraw, cx: int, cy: int, r: int):
    """Testa del serpente — pivot con numero 5."""
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=SNAKE_HEAD_COLOR)
    # Numero 5 sulla testa (pivot classico)
    draw.text((cx, cy), "5", fill=(255, 255, 255), anchor="mm")

# ---------------------------------------------------------------------------
# Posizione pixel di una cella
# ---------------------------------------------------------------------------

def cell_xy(col: int, row: int):
    x = PAD_LEFT + col * (CELL_SIZE + CELL_GAP)
    y = PAD_TOP  + row * (CELL_SIZE + CELL_GAP)
    return x, y

def cell_center(col: int, row: int):
    x, y = cell_xy(col, row)
    return x + CELL_SIZE // 2, y + CELL_SIZE // 2

# ---------------------------------------------------------------------------
# Rendering base del contribution graph
# ---------------------------------------------------------------------------

def render_base(contributions: list[list[int]], month_labels: list[tuple]) -> Image.Image:
    """Renderizza il contribution graph di base senza animazione."""
    img = Image.new("RGB", (CANVAS_W, CANVAS_H), BG_COLOR)
    draw = ImageDraw.Draw(img)

    # Etichette giorni (lun, mer, ven)
    day_names = ["", "Mon", "", "Wed", "", "Fri", ""]
    for r, name in enumerate(day_names):
        if name:
            cx, cy = cell_center(0, r)
            draw.text((PAD_LEFT - 6, cy), name, fill=TEXT_COLOR, anchor="rm",
                      font_size=9)

    # Etichette mesi
    for label, col in month_labels:
        x, _ = cell_xy(col, 0)
        draw.text((x, PAD_TOP - 14), label, fill=TEXT_COLOR, font_size=9)

    # Celle
    for c in range(COLS):
        for r in range(ROWS):
            level = contributions[c][r]
            color = EMPTY_COLOR if level == 0 else CONTRIB_COLORS[level - 1]
            x, y = cell_xy(c, r)
            draw.rounded_rectangle([x, y, x + CELL_SIZE, y + CELL_SIZE],
                                   radius=2, fill=color)
    return img

# ---------------------------------------------------------------------------
# Percorso serpente a serpentina
# ---------------------------------------------------------------------------

def build_snake_path(contributions: list[list[int]]) -> list[tuple]:
    """
    Percorso a serpentina: colonna per colonna,
    alternando su e giù. Passa SOLO per celle vuote (level == 0).
    """
    path = []
    for c in range(COLS):
        rows = range(ROWS) if c % 2 == 0 else range(ROWS - 1, -1, -1)
        for r in rows:
            if contributions[c][r] == 0:
                path.append((c, r))
    return path

# ---------------------------------------------------------------------------
# Generazione GIF
# ---------------------------------------------------------------------------

def generate_gif(contributions: list[list[int]],
                 month_labels: list[tuple],
                 output_path: str = "snake_basket.gif"):

    path = build_snake_path(contributions)
    if not path:
        print("Nessuna cella vuota trovata — il tuo GitHub è già pieno di contributi!")
        return

    print(f"Celle vuote da mangiare: {len(path)}")
    print(f"Generazione frames...")

    base_img = render_base(contributions, month_labels)
    frames   = []
    eaten    = set()   # celle già mangiate (diventano palloni)

    snake_length = 5   # lunghezza iniziale del serpente (pivot = fisico)
    r_ball = CELL_SIZE // 2 - 1

    # Quanti step per frame (velocità animazione)
    step_per_frame = max(1, len(path) // 120)

    for i, (col, row) in enumerate(path):
        if i % step_per_frame != 0 and i != len(path) - 1:
            eaten.add((col, row))
            continue

        eaten.add((col, row))

        # Clona base
        frame = base_img.copy()
        draw  = ImageDraw.Draw(frame)

        # Disegna i palloni sulle celle già mangiate
        for (ec, er) in eaten:
            cx, cy = cell_center(ec, er)
            draw_basketball(draw, cx, cy, r_ball)

        # Corpo del serpente (ultime N posizioni nel path)
        snake_positions = path[max(0, i - snake_length + 1): i + 1]
        for j, (sc, sr) in enumerate(snake_positions[:-1]):
            cx, cy = cell_center(sc, sr)
            body_r = max(2, r_ball - 1)
            draw.ellipse([cx - body_r, cy - body_r, cx + body_r, cy + body_r],
                         fill=SNAKE_BODY_COLOR)

        # Testa
        hcx, hcy = cell_center(col, row)
        draw_snake_head(draw, hcx, hcy, r_ball)

        frames.append(frame)

    # Frame finale: tutti i palloni, niente serpente
    final = base_img.copy()
    draw  = ImageDraw.Draw(final)
    for (ec, er) in [(p[0], p[1]) for p in path]:
        cx, cy = cell_center(ec, er)
        draw_basketball(draw, cx, cy, r_ball)

    # Aggiungi il frame finale 3 volte per pausa
    for _ in range(3):
        frames.append(final)

    if not frames:
        print("Nessun frame generato.")
        return

    frames[0].save(
        output_path,
        save_all=True,
        append_images=frames[1:],
        loop=0,
        duration=80,   # ms per frame
        optimize=True,
    )
    print(f"GIF salvata: {output_path} ({len(frames)} frames)")

# ---------------------------------------------------------------------------
# Dati demo (quando non si ha il token)
# ---------------------------------------------------------------------------

def generate_demo_data():
    """Simula un anno di contributi realistici per AndreaBonn."""
    random.seed(42)   # seed fisso = riproducibile
    contributions = []
    month_labels  = []

    today = datetime.today()
    start = today - timedelta(weeks=52)

    current_month = None
    for c in range(COLS):
        week_data = []
        week_date = start + timedelta(weeks=c)

        # Etichetta mese
        m = week_date.strftime("%b")
        if m != current_month:
            current_month = m
            month_labels.append((m, c))

        for r in range(ROWS):
            day = week_date + timedelta(days=r)
            if day > today:
                week_data.append(0)
                continue
            # Pattern realistico: più attivo nei giorni feriali
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

def fetch_github_data(token: str):
    if requests is None:
        print("Installa requests: pip install requests")
        sys.exit(1)

    headers = {"Authorization": f"bearer {token}"}
    resp = requests.post(GITHUB_GRAPHQL,
                         json={"query": QUERY, "variables": {"login": USERNAME}},
                         headers=headers, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    if "errors" in data:
        print("Errore API GitHub:", data["errors"])
        sys.exit(1)

    weeks = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]

    contributions  = []
    month_labels   = []
    current_month  = None

    for c, week in enumerate(weeks[-52:]):  # ultime 52 settimane
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

        # Padding se la settimana ha meno di 7 giorni
        while len(week_data) < 7:
            week_data.append(0)

        contributions.append(week_data)

    return contributions, month_labels

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Snake Basket — GitHub contribution animator")
    parser.add_argument("--token", help="GitHub Personal Access Token (read:user)")
    parser.add_argument("--demo",  action="store_true", help="Usa dati demo senza token")
    parser.add_argument("--output", default="snake_basket.gif", help="Nome file output")
    args = parser.parse_args()

    print(f"Snake Basket — @{USERNAME}")
    print("=" * 40)

    token = args.token or os.environ.get("SNAKE_TOKEN", "")
    if args.demo or not token:
        print("Modalita demo (dati simulati)")
        contributions, month_labels = generate_demo_data()
    else:
        print(f"Fetching dati GitHub per @{USERNAME}...")
        contributions, month_labels = fetch_github_data(token)

    total_cells = sum(1 for c in contributions for level in c if level == 0)
    print(f"Celle vuote trovate: {total_cells}")

    generate_gif(contributions, month_labels, args.output)
    print(f"\nPer usarla nel README:\n")
    print(f"![Snake Basket](./{args.output})")
    print(f"\nOppure con GitHub Actions: vedi README per il workflow automatico.")

if __name__ == "__main__":
    main()
