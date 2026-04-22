import json
import logging
import re
import tomllib

logger = logging.getLogger(__name__)


def parse_package_json(content: str) -> list[str]:
    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        logger.warning("package.json parse failed — file may be malformed: %s", exc)
        return []

    deps: set[str] = set()
    for key in ("dependencies", "devDependencies"):
        section = data.get(key)
        if section is None:
            continue
        if not isinstance(section, dict):
            logger.warning(
                "package.json '%s' is not a dict (got %s) — skipping",
                key,
                type(section).__name__,
            )
            continue
        deps.update(section.keys())
    return list(deps)


def parse_requirements_txt(content: str) -> list[str]:
    pkgs: list[str] = []
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("-"):
            continue
        name = re.split(r"[>=<~!\[;@\s]", line)[0].strip().lower()
        if name:
            pkgs.append(name)
    return pkgs


def parse_pyproject_toml(content: str) -> list[str]:
    try:
        data = tomllib.loads(content)
    except tomllib.TOMLDecodeError as exc:
        logger.warning("pyproject.toml parse failed — file may be malformed: %s", exc)
        return []

    pkgs: list[str] = []
    deps = data.get("project", {}).get("dependencies", [])
    if not isinstance(deps, list):
        return pkgs
    for dep in deps:
        name = re.split(r"[>=<~!\[;@\s]", dep)[0].strip().lower()
        if name:
            pkgs.append(name)
    return pkgs
