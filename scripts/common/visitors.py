import json
import logging
import re
from datetime import UTC, datetime, timedelta
from pathlib import Path

import requests

from common.config import USERNAME

KOMAREV_URL: str = "https://komarev.com/ghpvc/"
VISITORS_JSON = Path(__file__).parent.parent.parent / "assets" / "visitors.json"

logger = logging.getLogger(__name__)


def _read_visitors_data() -> dict:
    try:
        data = json.loads(VISITORS_JSON.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        data = {}
    if "history" not in data:
        data = _migrate_legacy(data)
    return data


def _migrate_legacy(old: dict) -> dict:
    """Migra dal vecchio formato {total, last_komarev} al nuovo con history."""
    return {
        "last_komarev": old.get("last_komarev", 0),
        "total": old.get("total", 0),
        "history": [],
    }


def _save_visitors_data(data: dict) -> None:
    tmp = VISITORS_JSON.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    tmp.replace(VISITORS_JSON)


def _fetch_komarev_count() -> int:
    try:
        resp = requests.get(
            KOMAREV_URL,
            params={"username": USERNAME, "style": "flat", "label": "views"},
            timeout=10,
        )
        resp.raise_for_status()
        numbers = re.findall(r">(\d[\d,.]*)<", resp.text)
        if numbers:
            count = int(numbers[-1].replace(",", "").replace(".", ""))
            return min(count, 10_000_000)
    except (requests.RequestException, ValueError) as exc:
        logger.warning("komarev fetch failed: %s", exc)
    return 0


def fetch_visitor_count() -> tuple[int, int]:
    """Returns (views_last_14_days, cumulative_total)."""
    current = _fetch_komarev_count()
    data = _read_visitors_data()

    last = data["last_komarev"]
    delta = max(0, current - last) if last > 0 else 0
    data["last_komarev"] = current
    data.setdefault("total", 0)
    data["total"] += delta

    today = datetime.now(UTC).strftime("%Y-%m-%d")
    history: list[dict] = data["history"]

    if history and history[-1]["date"] == today:
        history[-1]["views"] += delta
    else:
        history.append({"date": today, "views": delta})

    cutoff = (datetime.now(UTC) - timedelta(days=14)).strftime("%Y-%m-%d")
    history[:] = [entry for entry in history if entry["date"] >= cutoff]

    views_14d = sum(entry["views"] for entry in history)

    _save_visitors_data(data)
    return views_14d, data["total"]
