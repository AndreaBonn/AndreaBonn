import json
import logging
import urllib.error
import urllib.request
from urllib.parse import urlparse

from common.config import GITHUB_API, USERNAME

logger = logging.getLogger(__name__)

_ALLOWED_HOSTS = {"api.github.com"}


def _validate_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.hostname not in _ALLOWED_HOSTS:
        raise ValueError(f"URL host not allowed: {parsed.hostname}")


def _api_get(url: str, token: str, accept: str = "application/vnd.github+json") -> bytes | None:
    _validate_url(url)
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"token {token}",
            "Accept": accept,
            "User-Agent": "tech-stack-generator",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.read()
    except (urllib.error.HTTPError, urllib.error.URLError) as exc:
        logger.warning("API request failed for %s: %s", url, exc)
        return None


def fetch_repos(token: str) -> list[dict]:
    repos: list[dict] = []
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
