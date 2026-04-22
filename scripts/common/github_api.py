import json
import logging
import urllib.error
import urllib.request
from urllib.parse import urlparse

from common.config import GITHUB_API, USERNAME

logger = logging.getLogger(__name__)

_ALLOWED_HOSTS = {"api.github.com"}
_ALLOWED_SCHEMES = {"https"}


def _validate_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in _ALLOWED_SCHEMES:
        raise ValueError(f"URL scheme not allowed: {parsed.scheme}")
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
        with urllib.request.urlopen(req, timeout=15) as resp:  # nosec B310
            return resp.read()
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            logger.debug("Resource not found: %s", url)
        elif exc.code in (401, 403):
            logger.error("GitHub API auth/permission error %d for %s — check token", exc.code, url)
            raise
        elif exc.code == 429:
            logger.error("GitHub API rate limit exceeded for %s", url)
            raise
        else:
            try:
                body = exc.read().decode("utf-8", errors="replace")[:200]
            except OSError as body_exc:
                logger.debug("Could not read error body: %s", body_exc)
                body = "<unreadable>"
            logger.warning("GitHub API HTTP %d for %s: %s — body: %s", exc.code, url, exc, body)
        return None
    except urllib.error.URLError as exc:
        logger.warning("Network error fetching %s: %s", url, exc)
        return None


def fetch_repos(token: str) -> list[dict]:
    repos: list[dict] = []
    page = 1
    while True:
        url = f"{GITHUB_API}/users/{USERNAME}/repos?per_page=100&page={page}&type=public"
        data = _api_get(url, token)
        if data is None:
            break
        try:
            batch = json.loads(data)
        except json.JSONDecodeError as exc:
            logger.error("fetch_repos: invalid JSON from GitHub (page %d): %s", page, exc)
            break
        if not batch:
            break
        repos.extend(batch)
        page += 1
    if not repos:
        logger.warning(
            "fetch_repos returned empty list — possible auth failure or network error. "
            "Check SNAKE_TOKEN and GitHub API availability."
        )
    return repos


def fetch_languages(token: str, repo_name: str) -> dict[str, int]:
    data = _api_get(f"{GITHUB_API}/repos/{USERNAME}/{repo_name}/languages", token)
    if data is None:
        return {}
    try:
        return json.loads(data)
    except json.JSONDecodeError as exc:
        logger.error("fetch_languages(%s): invalid JSON: %s", repo_name, exc)
        return {}


def fetch_file(token: str, repo_name: str, path: str) -> str | None:
    data = _api_get(
        f"{GITHUB_API}/repos/{USERNAME}/{repo_name}/contents/{path}",
        token,
        accept="application/vnd.github.raw+json",
    )
    if data is None:
        return None
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError as exc:
        logger.error("fetch_file(%s/%s): UTF-8 decode failed: %s", repo_name, path, exc)
        return None


def check_file_exists(token: str, repo_name: str, path: str) -> bool:
    return _api_get(f"{GITHUB_API}/repos/{USERNAME}/{repo_name}/contents/{path}", token) is not None
