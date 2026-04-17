"""
Oggi nella storia NBA
Genera un SVG con un evento storico NBA accaduto in questa data.
Output: assets/nba_today.svg
"""

import random
from datetime import datetime, timezone
from pathlib import Path

NBA_HISTORY = {
    (1, 1):  [{"text": "Nel 1970 gli NBA All-Star Game arrivano a quota 20 edizioni.", "icon": "🌟"}],
    (1, 7):  [{"text": "Nel 1972 i Lakers vincono la 33ª partita consecutiva, record NBA ancora imbattuto.", "icon": "🔥"}],
    (1, 13): [{"text": "Nel 1990 Michael Jordan segna 61 punti contro Cleveland.", "icon": "💥"}],
    (1, 20): [{"text": "Nel 1968 Wilt Chamberlain diventa il primo giocatore a toccare quota 25.000 punti in carriera.", "icon": "🏆"}],
    (2, 3):  [{"text": "Nel 1995 Michael Jordan gioca la sua ultima partita prima del primo ritiro.", "icon": "😢"}],
    (2, 14): [{"text": "Nel 1990 si svolge il primo Slam Dunk Contest vinto da Dominique Wilkins.", "icon": "🏀"}],
    (2, 17): [{"text": "Nel 1963 nasce Michael Jordan, considerato il più grande di tutti i tempi.", "icon": "🐐"}],
    (3, 2):  [{"text": "Nel 1962 Wilt Chamberlain segna 100 punti in una singola partita contro i Knicks.", "icon": "💯"}],
    (3, 6):  [{"text": "Nel 1987 Michael Jordan diventa il secondo giocatore nella storia a segnare 3.000 punti in una stagione.", "icon": "⚡"}],
    (3, 18): [{"text": "Nel 1995 Michael Jordan annuncia il suo ritorno con il leggendario fax: 'I'm back'.", "icon": "👑"}],
    (3, 24): [{"text": "Nel 2000 Vince Carter segna quella che molti definiscono la schiacciata del secolo alle Olimpiadi.", "icon": "🚀"}],
    (4, 5):  [{"text": "Nel 2019 LeBron James supera Michael Jordan nella classifica dei punti segnati in playoff.", "icon": "👑"}],
    (4, 9):  [{"text": "Nel 2019 Dirk Nowitzki annuncia il ritiro dopo 21 stagioni con i Dallas Mavericks.", "icon": "🎯"}],
    (4, 13): [{"text": "Nel 2016 Kobe Bryant conclude la carriera con 60 punti nella sua ultima partita.", "icon": "🐍"}],
    (4, 20): [{"text": "Nel 1986 Michael Jordan segna 63 punti contro i Celtics di Larry Bird in playoff.", "icon": "💣"}],
    (5, 7):  [{"text": "Nel 1989 Magic Johnson vince il suo terzo titolo di MVP delle Finals.", "icon": "✨"}],
    (5, 17): [{"text": "Nel 1996 i Chicago Bulls di Jordan finiscono la stagione regolare con 72 vittorie, record storico.", "icon": "🏆"}],
    (6, 1):  [{"text": "Nel 2016 LeBron James guida Cleveland alla rimonta da 3-1 contro Golden State.", "icon": "🔥"}],
    (6, 11): [{"text": "Nel 1997 Michael Jordan gioca con la febbre alta e segna 38 punti: nasce la leggenda del 'Flu Game'.", "icon": "🤒"}],
    (6, 12): [{"text": "Nel 2011 Dirk Nowitzki vince l'unico titolo NBA della sua carriera contro i Miami Heat.", "icon": "🏆"}],
    (6, 14): [{"text": "Nel 1998 Michael Jordan segna il canestro decisivo nella gara 6 delle Finals: ultimo titolo con i Bulls.", "icon": "🎯"}],
    (6, 19): [{"text": "Nel 2016 i Cleveland Cavaliers vincono il primo titolo della loro storia, guidati da LeBron James.", "icon": "👑"}],
    (7, 1):  [{"text": "Nel 2010 LeBron James annuncia 'The Decision': lascia Cleveland per Miami.", "icon": "📺"}],
    (7, 4):  [{"text": "Nel 2016 Kevin Durant firma con i Golden State Warriors, scuotendo l'NBA intera.", "icon": "💣"}],
    (8, 8):  [{"text": "Nel 2008 il Team USA vince l'oro olimpico a Pechino con il 'Redeem Team'.", "icon": "🥇"}],
    (8, 23): [{"text": "Nel 2020 Kobe Bryant avrebbe compiuto 42 anni. Il suo numero 8 e il 24 restano ritirati a LA.", "icon": "💛"}],
    (9, 9):  [{"text": "Nel 2015 Kobe Bryant supera Michael Jordan nella classifica all-time dei punti segnati.", "icon": "🐍"}],
    (10, 15):[{"text": "Nel 1984 Michael Jordan debutta in NBA con i Chicago Bulls.", "icon": "🌅"}],
    (11, 1): [{"text": "Nel 1950 il primo giocatore afroamericano, Earl Lloyd, scende in campo in una partita NBA.", "icon": "✊"}],
    (11, 7): [{"text": "Nel 1991 Magic Johnson annuncia di essere positivo all'HIV, sconvolgendo il mondo dello sport.", "icon": "💔"}],
    (12, 6): [{"text": "Nel 1969 Wilt Chamberlain stabilisce il record di rimbalzi in carriera.", "icon": "📊"}],
    (12, 25):[{"text": "Ogni anno il giorno di Natale l'NBA propone le partite più attese della stagione.", "icon": "🎄"}],
}

def get_today_event():
    today = datetime.now(timezone.utc)
    key = (today.month, today.day)
    if key in NBA_HISTORY:
        return random.choice(NBA_HISTORY[key])
    random.seed(today.timetuple().tm_yday + today.year)
    all_events = [e for events in NBA_HISTORY.values() for e in events]
    return random.choice(all_events)

def wrap_text(text, max_chars=45):
    words = text.split()
    lines, line = [], ""
    for word in words:
        if len(line) + len(word) + 1 <= max_chars:
            line += ("" if not line else " ") + word
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines

today = datetime.now(timezone.utc)
event = get_today_event()
lines = wrap_text(event["text"])
LINE_H = 28
SVG_H = max(130, len(lines) * LINE_H + 120)
SVG_W = 680

def svg_lines(lines, start_y):
    out = ""
    for i, l in enumerate(lines):
        out += f'<text x="340" y="{start_y + i*LINE_H}" font-family="monospace" font-size="18" fill="#e6edf3" text-anchor="middle">{l}</text>\n'
    return out

svg = f'''<svg width="{SVG_W}" height="{SVG_H}" xmlns="http://www.w3.org/2000/svg">
  <rect width="{SVG_W}" height="{SVG_H}" rx="12" fill="#161b22"/>
  <rect x="1" y="1" width="{SVG_W-2}" height="{SVG_H-2}" rx="11" fill="none" stroke="#388bfd" stroke-width="1.5"/>

  <!-- icona evento -->
  <rect x="16" y="16" width="52" height="52" rx="10" fill="#1c2128"/>
  <text x="42" y="50" font-size="26" text-anchor="middle">{event["icon"]}</text>

  <!-- header -->
  <text x="80" y="36" font-family="monospace" font-size="13" fill="#8b949e" letter-spacing="2">OGGI NELLA STORIA NBA</text>
  <text x="80" y="56" font-family="monospace" font-size="13" fill="#388bfd">{today.strftime("%d %B").upper()}</text>

  <!-- separatore -->
  <line x1="24" y1="74" x2="{SVG_W-24}" y2="74" stroke="#30363d" stroke-width="1"/>

  <!-- testo evento -->
  {svg_lines(lines, 100)}

  <!-- footer -->
  <text x="{SVG_W-24}" y="{SVG_H-12}" font-family="monospace" font-size="12" fill="#484f58" text-anchor="end">@AndreaBonn • storia NBA</text>
</svg>'''

out = Path(__file__).parent.parent / "assets" / "nba_today.svg"
out.parent.mkdir(exist_ok=True)
out.write_text(svg, encoding="utf-8")
print(f"nba_today.svg generato — {event['icon']} {event['text'][:40]}...")
