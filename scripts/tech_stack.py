"""
Tech Stack Word Cloud Generator
Fetches languages and dependencies from all public GitHub repos,
auto-categorizes and generates an SVG with colored pills.

Usage: python tech_stack.py --token <GITHUB_TOKEN>
       python tech_stack.py --demo
"""

import argparse
import json
import math
import os
import re
import sys
import urllib.request
import urllib.error
from pathlib import Path

USERNAME = "AndreaBonn"
GITHUB_API = "https://api.github.com"

# ---------------------------------------------------------------------------
# Mapping: package name → (display name, category)
# ---------------------------------------------------------------------------

TECH_MAP = {
    # Python frameworks
    "fastapi": ("FastAPI", "framework"),
    "flask": ("Flask", "framework"),
    "django": ("Django", "framework"),
    "streamlit": ("Streamlit", "framework"),
    "gradio": ("Gradio", "framework"),
    "pydantic": ("Pydantic", "framework"),
    "pydantic-settings": ("Pydantic", "framework"),
    "uvicorn": ("Uvicorn", "framework"),
    "gunicorn": ("Gunicorn", "framework"),
    "celery": ("Celery", "framework"),
    "httpx": ("HTTPX", "framework"),
    "aiohttp": ("aiohttp", "framework"),
    # JS frameworks
    "react": ("React", "framework"),
    "react-dom": ("React", "framework"),
    "next": ("Next.js", "framework"),
    "vue": ("Vue.js", "framework"),
    "express": ("Express", "framework"),
    "tailwindcss": ("Tailwind CSS", "framework"),
    "vite": ("Vite", "framework"),
    # AI/ML
    "tensorflow": ("TensorFlow", "ai_ml"),
    "torch": ("PyTorch", "ai_ml"),
    "torchvision": ("PyTorch", "ai_ml"),
    "scikit-learn": ("Scikit-learn", "ai_ml"),
    "sklearn": ("Scikit-learn", "ai_ml"),
    "pandas": ("Pandas", "ai_ml"),
    "polars": ("Polars", "ai_ml"),
    "numpy": ("NumPy", "ai_ml"),
    "scipy": ("SciPy", "ai_ml"),
    "matplotlib": ("Matplotlib", "ai_ml"),
    "seaborn": ("Seaborn", "ai_ml"),
    "plotly": ("Plotly", "ai_ml"),
    "ultralytics": ("YOLO", "ai_ml"),
    "yolov5": ("YOLO", "ai_ml"),
    "opencv-python": ("OpenCV", "ai_ml"),
    "opencv-python-headless": ("OpenCV", "ai_ml"),
    "cv2": ("OpenCV", "ai_ml"),
    "transformers": ("Transformers", "ai_ml"),
    "langchain": ("LangChain", "ai_ml"),
    "openai": ("OpenAI SDK", "ai_ml"),
    "anthropic": ("Anthropic SDK", "ai_ml"),
    "groq": ("Groq SDK", "ai_ml"),
    "huggingface-hub": ("HuggingFace", "ai_ml"),
    "xgboost": ("XGBoost", "ai_ml"),
    "lightgbm": ("LightGBM", "ai_ml"),
    "statsmodels": ("Statsmodels", "ai_ml"),
    "pillow": ("Pillow", "ai_ml"),
    "spacy": ("spaCy", "ai_ml"),
    "nltk": ("NLTK", "ai_ml"),
    "keras": ("Keras", "ai_ml"),
    # Database
    "sqlalchemy": ("SQLAlchemy", "database"),
    "psycopg2": ("PostgreSQL", "database"),
    "psycopg2-binary": ("PostgreSQL", "database"),
    "asyncpg": ("PostgreSQL", "database"),
    "pymongo": ("MongoDB", "database"),
    "redis": ("Redis", "database"),
    "firebase-admin": ("Firebase", "database"),
    "firebase": ("Firebase", "database"),
    "firestore": ("Firestore", "database"),
    "supabase": ("Supabase", "database"),
    "prisma": ("Prisma", "database"),
    "mongoose": ("MongoDB", "database"),
    "sqlite3": ("SQLite", "database"),
    "alembic": ("Alembic", "database"),
    # Tools (detected via files, not packages)
    "docker": ("Docker", "tool"),
    "github-actions": ("GitHub Actions", "tool"),
    "git": ("Git", "tool"),
    "playwright": ("Playwright", "tool"),
    "selenium": ("Selenium", "tool"),
    "pytest": ("Pytest", "tool"),
    "jest": ("Jest", "tool"),
    "eslint": ("ESLint", "tool"),
    "ruff": ("Ruff", "tool"),
    "mypy": ("MyPy", "tool"),
    "webpack": ("Webpack", "tool"),
    # Messaging / API
    "python-telegram-bot": ("Telegram Bot API", "framework"),
    "telebot": ("Telegram Bot API", "framework"),
    "aiogram": ("Telegram Bot API", "framework"),
    "slack-sdk": ("Slack SDK", "framework"),
    "discord.py": ("Discord.py", "framework"),
    "beautifulsoup4": ("BeautifulSoup", "tool"),
    "bs4": ("BeautifulSoup", "tool"),
    "scrapy": ("Scrapy", "tool"),
    "requests": ("Requests", "tool"),
}

# GitHub topics → (display name, category)
TOPIC_MAP = {
    "python": ("Python", "linguaggio"),
    "javascript": ("JavaScript", "linguaggio"),
    "typescript": ("TypeScript", "linguaggio"),
    "react": ("React", "framework"),
    "nextjs": ("Next.js", "framework"),
    "fastapi": ("FastAPI", "framework"),
    "docker": ("Docker", "tool"),
    "machine-learning": ("Machine Learning", "ai_ml"),
    "deep-learning": ("Deep Learning", "ai_ml"),
    "computer-vision": ("Computer Vision", "ai_ml"),
    "artificial-intelligence": ("AI", "ai_ml"),
    "data-science": ("Data Science", "ai_ml"),
    "nlp": ("NLP", "ai_ml"),
    "firebase": ("Firebase", "database"),
    "postgresql": ("PostgreSQL", "database"),
    "mongodb": ("MongoDB", "database"),
}

# GitHub language → display name (linguaggi)
LANG_DISPLAY = {
    "Python": "Python",
    "JavaScript": "JavaScript",
    "TypeScript": "TypeScript",
    "Shell": "Shell",
    "HTML": "HTML",
    "CSS": "CSS",
    "Dockerfile": "Docker",
    "Go": "Go",
    "Rust": "Rust",
    "Java": "Java",
    "Kotlin": "Kotlin",
    "C": "C",
    "C++": "C++",
    "C#": "C#",
    "Ruby": "Ruby",
    "PHP": "PHP",
    "Swift": "Swift",
    "Dart": "Dart",
    "R": "R",
    "Jupyter Notebook": "Jupyter",
    "HCL": "Terraform",
    "Makefile": "Make",
}

LANG_EXCLUDE = {"Procfile", "Batchfile", "Nix", "Nunjucks", "EJS", "Pug"}

CATEGORIES = {
    "linguaggio": {"label": "LANGUAGES", "color": "#3fb950", "bg": "#1a3a2a"},
    "framework": {"label": "FRAMEWORK", "color": "#388bfd", "bg": "#1a2a3a"},
    "ai_ml": {"label": "AI / ML", "color": "#e6861a", "bg": "#3a2a1a"},
    "database": {"label": "DATABASE", "color": "#bc8cff", "bg": "#2a1a3a"},
    "tool": {"label": "TOOLS", "color": "#8b949e", "bg": "#1c2128"},
}

# ---------------------------------------------------------------------------
# Fetch from GitHub API (stdlib only)
# ---------------------------------------------------------------------------

def _api_get(url: str, token: str, accept: str = "application/vnd.github+json") -> bytes | None:
    req = urllib.request.Request(url, headers={
        "Authorization": f"token {token}",
        "Accept": accept,
        "User-Agent": "tech-stack-generator",
    })
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.read()
    except urllib.error.HTTPError:
        return None


def fetch_repos(token: str) -> list[dict]:
    repos = []
    page = 1
    while True:
        url = f"{GITHUB_API}/users/{USERNAME}/repos?per_page=100&page={page}&type=public"
        data = _api_get(url, token)
        if data is None:
            break
        batch = json.loads(data)
        if not batch:
            break
        repos.extend(batch)
        page += 1
    return repos


def fetch_languages(token: str, repo_name: str) -> dict[str, int]:
    data = _api_get(f"{GITHUB_API}/repos/{USERNAME}/{repo_name}/languages", token)
    if data:
        return json.loads(data)
    return {}


def fetch_file(token: str, repo_name: str, path: str) -> str | None:
    data = _api_get(
        f"{GITHUB_API}/repos/{USERNAME}/{repo_name}/contents/{path}",
        token,
        accept="application/vnd.github.raw+json",
    )
    if data:
        return data.decode("utf-8")
    return None


def check_file_exists(token: str, repo_name: str, path: str) -> bool:
    return _api_get(f"{GITHUB_API}/repos/{USERNAME}/{repo_name}/contents/{path}", token) is not None


# ---------------------------------------------------------------------------
# Parsing dipendenze
# ---------------------------------------------------------------------------

def parse_package_json(content: str) -> list[str]:
    try:
        data = json.loads(content)
        deps = set()
        for key in ("dependencies", "devDependencies"):
            if key in data:
                deps.update(data[key].keys())
        return list(deps)
    except (json.JSONDecodeError, AttributeError):
        return []


def parse_requirements_txt(content: str) -> list[str]:
    pkgs = []
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("-"):
            continue
        # nome pacchetto prima di ==, >=, ~=, [, etc.
        name = re.split(r"[>=<~!\[;@\s]", line)[0].strip().lower()
        if name:
            pkgs.append(name)
    return pkgs


def parse_pyproject_toml(content: str) -> list[str]:
    pkgs = []
    in_deps = False
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("dependencies") and "=" in stripped:
            in_deps = True
            # inline list: dependencies = ["pkg1", "pkg2"]
            inline = re.findall(r'"([^"]+)"', stripped)
            for dep in inline:
                name = re.split(r"[>=<~!\[;@\s]", dep)[0].strip().lower()
                if name:
                    pkgs.append(name)
            continue
        if in_deps:
            if stripped.startswith("]"):
                in_deps = False
                continue
            if stripped.startswith('"'):
                dep = stripped.strip('",')
                name = re.split(r"[>=<~!\[;@\s]", dep)[0].strip().lower()
                if name:
                    pkgs.append(name)
    return pkgs


# ---------------------------------------------------------------------------
# Scan completo
# ---------------------------------------------------------------------------

def scan_repos(token: str) -> dict[str, dict[str, int]]:
    """Returns {category: {display_name: count}}."""
    result: dict[str, dict[str, int]] = {cat: {} for cat in CATEGORIES}

    repos = fetch_repos(token)
    print(f"Found {len(repos)} public repos")

    for repo in repos:
        name = repo["name"]
        is_fork = repo.get("fork", False)
        if is_fork:
            continue

        print(f"  Scanning {name}...")

        # 1. Linguaggi da GitHub API
        languages = fetch_languages(token, name)
        for lang, bytes_count in languages.items():
            if lang in LANG_EXCLUDE:
                continue
            display = LANG_DISPLAY.get(lang, lang)
            # Dockerfile → tool Docker
            if lang == "Dockerfile":
                result["tool"][display] = result["tool"].get(display, 0) + 1
            else:
                result["linguaggio"][display] = result["linguaggio"].get(display, 0) + bytes_count

        # 2. Topics
        for topic in repo.get("topics", []):
            if topic in TOPIC_MAP:
                display, cat = TOPIC_MAP[topic]
                result[cat][display] = result[cat].get(display, 0) + 1

        # 3. Dipendenze Python
        for dep_file, parser in [
            ("requirements.txt", parse_requirements_txt),
            ("pyproject.toml", parse_pyproject_toml),
        ]:
            content = fetch_file(token, name, dep_file)
            if content:
                for pkg in parser(content):
                    pkg_lower = pkg.lower().replace("_", "-")
                    if pkg_lower in TECH_MAP:
                        display, cat = TECH_MAP[pkg_lower]
                        result[cat][display] = result[cat].get(display, 0) + 1

        # 4. Dipendenze JS
        content = fetch_file(token, name, "package.json")
        if content:
            for pkg in parse_package_json(content):
                pkg_lower = pkg.lower().replace("@", "").split("/")[-1]
                if pkg_lower in TECH_MAP:
                    display, cat = TECH_MAP[pkg_lower]
                    result[cat][display] = result[cat].get(display, 0) + 1

        # 5. Tool detection via files
        if check_file_exists(token, name, "Dockerfile") or check_file_exists(token, name, "docker-compose.yml"):
            result["tool"]["Docker"] = result["tool"].get("Docker", 0) + 1
        if check_file_exists(token, name, ".github/workflows"):
            result["tool"]["GitHub Actions"] = result["tool"].get("GitHub Actions", 0) + 1

    # Git è sempre presente
    result["tool"]["Git"] = max(result["tool"].get("Git", 0), len(repos))

    return result


# ---------------------------------------------------------------------------
# SVG generation — word cloud a pill
# ---------------------------------------------------------------------------

def measure_text(text: str, font_size: int) -> int:
    """Stima larghezza testo monospace."""
    return int(len(text) * font_size * 0.62) + 16


def generate_svg(data: dict[str, dict[str, int]]) -> str:
    SVG_W = 880
    PADDING_X = 24
    PILL_H = 28
    PILL_GAP = 8
    SECTION_GAP = 16
    HEADER_H = 28

    # Calcola font sizes per categoria (normalizzati)
    def get_items(cat_data: dict[str, int]) -> list[tuple[str, int, int]]:
        """Ritorna [(name, count, font_size)] ordinati per count desc."""
        if not cat_data:
            return []
        items = sorted(cat_data.items(), key=lambda x: -x[1])
        max_count = items[0][1]
        min_count = items[-1][1]
        result = []
        for name, count in items:
            if max_count == min_count:
                ratio = 1.0
            else:
                ratio = (count - min_count) / (max_count - min_count)
            font_size = int(11 + ratio * 5)  # 11-16px range
            result.append((name, count, font_size))
        return result

    # Pre-calculate layout
    sections = []
    y_cursor = 28 + 10  # dopo top bar

    for cat_key, cat_info in CATEGORIES.items():
        items = get_items(data.get(cat_key, {}))
        if not items:
            continue

        section_y = y_cursor
        y_cursor += HEADER_H  # label categoria

        # Layout pills in rows
        rows = []
        current_row = []
        row_w = PADDING_X

        for name, count, font_size in items:
            pill_w = measure_text(name, font_size) + 12
            if row_w + pill_w + PILL_GAP > SVG_W - PADDING_X and current_row:
                rows.append(current_row)
                current_row = []
                row_w = PADDING_X
            current_row.append((name, count, font_size, pill_w))
            row_w += pill_w + PILL_GAP

        if current_row:
            rows.append(current_row)

        y_cursor += len(rows) * (PILL_H + PILL_GAP)
        y_cursor += SECTION_GAP

        sections.append({
            "cat": cat_key,
            "info": cat_info,
            "rows": rows,
            "y": section_y,
        })

    SVG_H = y_cursor + 10

    # Build SVG
    svg_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {SVG_W} {SVG_H}" width="100%">',
        f'  <rect width="{SVG_W}" height="{SVG_H}" rx="10" fill="#0d1117"/>',
        f'  <rect x="1" y="1" width="{SVG_W-2}" height="{SVG_H-2}" rx="9" fill="none" stroke="#30363d" stroke-width="1.5"/>',
        # Top bar
        f'  <rect x="1" y="1" width="{SVG_W-2}" height="26" rx="9" fill="#1c2128"/>',
        f'  <rect x="1" y="18" width="{SVG_W-2}" height="9" fill="#1c2128"/>',
        f'  <line x1="1" y1="27" x2="{SVG_W-1}" y2="27" stroke="#30363d" stroke-width="1"/>',
        f'  <circle cx="16" cy="14" r="3" fill="#e6861a" opacity="0.8"/>',
        f'  <circle cx="{SVG_W-16}" cy="14" r="3" fill="#e6861a" opacity="0.8"/>',
        f'  <text x="{SVG_W//2}" y="19" text-anchor="middle" font-family="monospace" font-size="11" fill="#8b949e" letter-spacing="4" font-weight="bold">TECH STACK</text>',
    ]

    for section in sections:
        info = section["info"]
        y = section["y"]

        # Category label
        svg_parts.append(
            f'  <text x="{PADDING_X}" y="{y + 18}" font-family="monospace" '
            f'font-size="12" fill="{info["color"]}" letter-spacing="2" '
            f'font-weight="bold">{info["label"]}</text>'
        )

        # Separator line
        svg_parts.append(
            f'  <line x1="{PADDING_X}" y1="{y + 24}" '
            f'x2="{SVG_W - PADDING_X}" y2="{y + 24}" '
            f'stroke="{info["color"]}" stroke-width="0.5" opacity="0.3"/>'
        )

        pill_y = y + HEADER_H
        for row in section["rows"]:
            # Center the row
            total_row_w = sum(pw for _, _, _, pw in row) + PILL_GAP * (len(row) - 1)
            x = (SVG_W - total_row_w) // 2

            for name, count, font_size, pill_w in row:
                # Pill background
                svg_parts.append(
                    f'  <rect x="{x}" y="{pill_y}" width="{pill_w}" '
                    f'height="{PILL_H}" rx="14" fill="{info["bg"]}" '
                    f'stroke="{info["color"]}" stroke-width="0.8" opacity="0.9"/>'
                )
                # Pill text
                text_y = pill_y + PILL_H // 2 + font_size // 3
                svg_parts.append(
                    f'  <text x="{x + pill_w // 2}" y="{text_y}" '
                    f'text-anchor="middle" font-family="monospace" '
                    f'font-size="{font_size}" fill="{info["color"]}" '
                    f'font-weight="{"bold" if font_size >= 14 else "normal"}">'
                    f'{name}</text>'
                )
                x += pill_w + PILL_GAP

            pill_y += PILL_H + PILL_GAP

    svg_parts.append("</svg>")
    return "\n".join(svg_parts)


# ---------------------------------------------------------------------------
# Demo data
# ---------------------------------------------------------------------------

DEMO_DATA = {
    "linguaggio": {
        "Python": 500000, "JavaScript": 200000, "TypeScript": 150000,
        "Shell": 30000, "SQL": 20000, "HTML": 80000, "CSS": 60000,
    },
    "framework": {
        "React": 5, "FastAPI": 3, "Firebase": 3, "Pydantic": 2,
        "Telegram Bot API": 2, "Tailwind CSS": 1, "Vite": 1,
    },
    "ai_ml": {
        "YOLO": 2, "Scikit-learn": 3, "Pandas": 4, "Polars": 2,
        "OpenCV": 2, "NumPy": 3, "Matplotlib": 2, "Pillow": 1,
    },
    "database": {
        "Firebase": 2, "SQLite": 1,
    },
    "tool": {
        "Git": 15, "GitHub Actions": 8, "Docker": 4, "Pytest": 3,
        "Ruff": 2, "Playwright": 1, "BeautifulSoup": 1,
    },
}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--token", help="GitHub token")
    parser.add_argument("--demo", action="store_true")
    args = parser.parse_args()

    token = args.token or os.environ.get("SNAKE_TOKEN", "")

    if args.demo or not token:
        print("Demo mode")
        data = DEMO_DATA
    else:
        data = scan_repos(token)

    # Stampa riepilogo
    for cat, items in data.items():
        if items:
            print(f"\n{cat}:")
            for name, count in sorted(items.items(), key=lambda x: -x[1]):
                print(f"  {name}: {count}")

    svg = generate_svg(data)
    out = Path(__file__).parent.parent / "assets" / "tech_stack.svg"
    out.parent.mkdir(exist_ok=True)
    out.write_text(svg, encoding="utf-8")
    print(f"\ntech_stack.svg generated ({len(svg)} bytes)")


if __name__ == "__main__":
    main()
