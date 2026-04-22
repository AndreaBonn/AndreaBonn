import json
import re


def parse_package_json(content: str) -> list[str]:
    try:
        data = json.loads(content)
        deps: set[str] = set()
        for key in ("dependencies", "devDependencies"):
            if key in data:
                deps.update(data[key].keys())
        return list(deps)
    except (json.JSONDecodeError, AttributeError):
        return []


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
    pkgs: list[str] = []
    in_deps = False
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("dependencies") and "=" in stripped:
            in_deps = True
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
