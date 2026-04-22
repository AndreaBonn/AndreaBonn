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
    except FileNotFoundError:
        logger.info("visitors.json not found, starting fresh")
        data = {}
    except json.JSONDecodeError as exc:
        logger.error("visitors.json is corrupted (%s), resetting — historical data may be lost", exc)
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
    try:
        tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
        tmp.replace(VISITORS_JSON)
    except OSError as exc:
        logger.error("Failed to persist visitors.json: %s — update will be lost", exc)
        raise


def _fetch_komarev_count() -> int | None:
    """Returns the raw count, or None on any failure."""
    try:
        resp = requests.get(
            KOMAREV_URL,
            params={"username": USERNAME, "style": "flat", "label": "views"},
            timeout=10,
        )
        resp.raise_for_status()
    except requests.RequestException as exc:
        logger.warning("komarev network request failed: %s", exc)
        return None

    try:
        numbers = re.findall(r">(\d[\d,.]*)<", resp.text)
        if not numbers:
            logger.warning("komarev response contained no numeric values (HTML changed?)")
            return None
        count = int(numbers[-1].replace(",", "").replace(".", ""))
        return min(count, 10_000_000)
    except ValueError as exc:
        logger.error("komarev count parsing failed — possible HTML format change: %s", exc)
        return None


def fetch_visitor_count() -> tuple[int, int]:
    """Returns (views_last_14_days, cumulative_total)."""
    current = _fetch_komarev_count()
    data = _read_visitors_data()

    if current is None:
        fallback = data.get("last_komarev", 0)
        logger.warning("Skipping komarev update — using last known value: %d", fallback)
        current = fallback

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
