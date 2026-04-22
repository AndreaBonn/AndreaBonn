"""
Tech Stack Word Cloud Generator
Fetches languages and dependencies from all public GitHub repos,
auto-categorizes and generates an SVG with colored pills.

Usage: SNAKE_TOKEN=<GITHUB_TOKEN> python tech_stack.py
       python tech_stack.py --demo
"""

import argparse
import logging
import os

from common.config import ASSETS_DIR
from common.github_api import check_file_exists, fetch_file, fetch_languages, fetch_repos
from common.parsers import parse_package_json, parse_pyproject_toml, parse_requirements_txt
from tech_mappings import CATEGORIES, LANG_DISPLAY, LANG_EXCLUDE, TECH_MAP, TOPIC_MAP
from tech_svg import generate_svg

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Scan completo
# ---------------------------------------------------------------------------


def scan_repos(token: str) -> dict[str, dict[str, int]]:
    """Returns {category: {display_name: count}}."""
    result: dict[str, dict[str, int]] = {cat: {} for cat in CATEGORIES}

    repos = fetch_repos(token)
    if not repos:
        logger.error("No public repos found for user — cannot generate tech stack")
        raise RuntimeError("No public repos found")
    logger.info("Found %d public repos", len(repos))

    for repo in repos:
        name = repo.get("name")
        if not name:
            logger.warning("scan_repos: repo entry missing 'name' field — skipping: %s", repo)
            continue
        is_fork = repo.get("fork", False)
        if is_fork:
            continue

        logger.info("  Scanning %s...", name)

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
# Demo data
# ---------------------------------------------------------------------------

DEMO_DATA = {
    "linguaggio": {
        "Python": 500000,
        "JavaScript": 200000,
        "TypeScript": 150000,
        "Shell": 30000,
        "SQL": 20000,
        "HTML": 80000,
        "CSS": 60000,
    },
    "framework": {
        "React": 5,
        "FastAPI": 3,
        "Firebase": 3,
        "Pydantic": 2,
        "Telegram Bot API": 2,
        "Tailwind CSS": 1,
        "Vite": 1,
    },
    "ai_ml": {
        "YOLO": 2,
        "Scikit-learn": 3,
        "Pandas": 4,
        "Polars": 2,
        "OpenCV": 2,
        "NumPy": 3,
        "Matplotlib": 2,
        "Pillow": 1,
    },
    "database": {
        "Firebase": 2,
        "SQLite": 1,
    },
    "tool": {
        "Git": 15,
        "GitHub Actions": 8,
        "Docker": 4,
        "Pytest": 3,
        "Ruff": 2,
        "Playwright": 1,
        "BeautifulSoup": 1,
    },
}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser()
    parser.add_argument("--demo", action="store_true")
    args = parser.parse_args()

    token = os.environ.get("SNAKE_TOKEN", "")

    if args.demo:
        logger.info("Demo mode (explicit --demo flag)")
        data = DEMO_DATA
    elif not token:
        logger.error("No GitHub token provided. Set SNAKE_TOKEN env var. Use --demo for test data.")
        raise SystemExit(1)
    else:
        data = scan_repos(token)

    for cat, items in data.items():
        if items:
            logger.info("\n%s:", cat)
            for name, count in sorted(items.items(), key=lambda x: -x[1]):
                logger.info("  %s: %d", name, count)

    svg = generate_svg(data)
    ASSETS_DIR.mkdir(exist_ok=True)
    out = ASSETS_DIR / "tech_stack.svg"
    try:
        out.write_text(svg, encoding="utf-8")
    except OSError as exc:
        logger.error("Failed to write tech_stack.svg to %s: %s", out, exc)
        raise SystemExit(1) from exc
    logger.info("\ntech_stack.svg generated (%d bytes)", len(svg))


if __name__ == "__main__":
    main()
