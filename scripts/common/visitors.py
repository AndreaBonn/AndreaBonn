import json
import logging
import re
from pathlib import Path

import requests

from common.config import USERNAME

KOMAREV_URL: str = "https://komarev.com/ghpvc/"
VISITORS_JSON = Path(__file__).parent.parent.parent / "assets" / "visitors.json"

logger = logging.getLogger(__name__)


def _read_visitors_data() -> dict:
    try:
        return json.loads(VISITORS_JSON.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {"total": 0, "last_komarev": 0}


def _save_visitors_data(data: dict) -> None:
    tmp = VISITORS_JSON.with_suffix(".tmp")
    tmp.write_text(json.dumps(data), encoding="utf-8")
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
    """Returns (recent_komarev_count, cumulative_total)."""
    current = _fetch_komarev_count()
    data = _read_visitors_data()
    last = data["last_komarev"]
    delta = max(0, current - last) if last > 0 else 0
    data["total"] += delta
    data["last_komarev"] = current
    _save_visitors_data(data)
    return current, data["total"]
