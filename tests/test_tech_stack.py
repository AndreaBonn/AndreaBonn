from unittest.mock import patch

import pytest
from common.parsers import parse_package_json, parse_pyproject_toml, parse_requirements_txt
from tech_stack import DEMO_DATA, scan_repos
from tech_svg import generate_svg, measure_text


def test_parse_requirements_txt_basic():
    content = "requests==2.31.0\nflask>=2.0\n"
    result = parse_requirements_txt(content)
    assert "requests" in result
    assert "flask" in result


def test_parse_requirements_txt_comments():
    content = "# comment\nrequests==2.31.0\n"
    result = parse_requirements_txt(content)
    assert result == ["requests"]


def test_parse_requirements_txt_flags():
    content = "-r base.txt\nrequests==2.31.0\n"
    result = parse_requirements_txt(content)
    assert result == ["requests"]


def test_parse_requirements_txt_empty():
    assert parse_requirements_txt("") == []


def test_parse_requirements_txt_extras():
    content = "uvicorn[standard]>=0.20\n"
    result = parse_requirements_txt(content)
    assert result == ["uvicorn"]


def test_parse_package_json_basic():
    content = '{"dependencies": {"react": "^18.0"}, "devDependencies": {"jest": "^29"}}'
    result = parse_package_json(content)
    assert "react" in result
    assert "jest" in result


def test_parse_package_json_empty():
    assert parse_package_json("{}") == []


def test_parse_package_json_invalid():
    assert parse_package_json("not json") == []


def test_parse_pyproject_toml_inline():
    content = '[project]\ndependencies = ["requests>=2.31", "flask>=2.0"]\n'
    result = parse_pyproject_toml(content)
    assert "requests" in result
    assert "flask" in result


def test_parse_pyproject_toml_multiline():
    content = """
[project]
dependencies = [
    "requests>=2.31",
    "flask>=2.0",
]
"""
    result = parse_pyproject_toml(content)
    assert "requests" in result
    assert "flask" in result


def test_parse_pyproject_toml_empty():
    assert parse_pyproject_toml("") == []


def test_parse_pyproject_toml_no_project_section():
    content = "[tool.ruff]\nline-length = 120\n"
    assert parse_pyproject_toml(content) == []


def test_parse_pyproject_toml_invalid():
    assert parse_pyproject_toml("not valid toml {{{") == []


def test_measure_text_positive():
    width = measure_text("Python", font_size=14)
    assert width > 0


def test_measure_text_longer_string_wider():
    short = measure_text("Go", font_size=14)
    long = measure_text("JavaScript", font_size=14)
    assert long > short


def test_generate_svg_returns_valid_svg():
    svg = generate_svg(DEMO_DATA)
    assert svg.startswith("<svg")
    assert svg.strip().endswith("</svg>")


def test_generate_svg_contains_categories():
    svg = generate_svg(DEMO_DATA)
    assert "LANGUAGES" in svg
    assert "FRAMEWORK" in svg
    assert "AI / ML" in svg
    assert "TOOLS" in svg


def test_generate_svg_contains_tech_names():
    svg = generate_svg(DEMO_DATA)
    assert "Python" in svg
    assert "React" in svg


def test_generate_svg_empty_data():
    svg = generate_svg({})
    assert svg.startswith("<svg")
    assert svg.strip().endswith("</svg>")


def test_generate_svg_single_item_category():
    """Categoria con un solo item — ratio = 1.0, font_size = 16, bold."""
    data = {"linguaggio": {"Python": 100}}
    svg = generate_svg(data)
    assert "Python" in svg
    assert 'font-weight="bold"' in svg


def test_generate_svg_equal_counts_all_same_size():
    """Tutti gli item con lo stesso count → ratio = 1.0 per tutti."""
    data = {"framework": {"React": 5, "FastAPI": 5, "Django": 5}}
    svg = generate_svg(data)
    assert "React" in svg
    assert "FastAPI" in svg
    assert "Django" in svg


def test_generate_svg_escapes_special_chars_in_names():
    data = {"tool": {"C++ <latest>": 1}}
    svg = generate_svg(data)
    assert "C++ &lt;latest&gt;" in svg


def test_generate_svg_multiple_rows_layout():
    """Molti item → deve wrappare su più righe senza crash."""
    data = {"linguaggio": {f"Lang{i}": i + 1 for i in range(20)}}
    svg = generate_svg(data)
    assert svg.startswith("<svg")
    assert svg.strip().endswith("</svg>")


# ---------------------------------------------------------------------------
# scan_repos — logica aggregazione con mock
# ---------------------------------------------------------------------------


@patch("tech_stack.check_file_exists")
@patch("tech_stack.fetch_file")
@patch("tech_stack.fetch_languages")
@patch("tech_stack.fetch_repos")
def test_scan_repos_languages_categorized(mock_repos, mock_langs, mock_file, mock_exists):
    mock_repos.return_value = [{"name": "my-project", "fork": False, "topics": []}]
    mock_langs.return_value = {"Python": 50000, "JavaScript": 20000}
    mock_file.return_value = None
    mock_exists.return_value = False

    result = scan_repos(token="tok")
    assert "Python" in result["linguaggio"]
    assert result["linguaggio"]["Python"] == 50000
    assert "JavaScript" in result["linguaggio"]


@patch("tech_stack.check_file_exists")
@patch("tech_stack.fetch_file")
@patch("tech_stack.fetch_languages")
@patch("tech_stack.fetch_repos")
def test_scan_repos_forks_skipped(mock_repos, mock_langs, mock_file, mock_exists):
    mock_repos.return_value = [
        {"name": "my-project", "fork": False, "topics": []},
        {"name": "forked-repo", "fork": True, "topics": []},
    ]
    mock_langs.return_value = {"Python": 10000}
    mock_file.return_value = None
    mock_exists.return_value = False

    scan_repos(token="tok")
    # fetch_languages chiamata solo per il repo non-fork
    assert mock_langs.call_count == 1


@patch("tech_stack.check_file_exists")
@patch("tech_stack.fetch_file")
@patch("tech_stack.fetch_languages")
@patch("tech_stack.fetch_repos")
def test_scan_repos_excluded_languages_ignored(mock_repos, mock_langs, mock_file, mock_exists):
    mock_repos.return_value = [{"name": "repo", "fork": False, "topics": []}]
    mock_langs.return_value = {"Python": 50000, "Procfile": 100}
    mock_file.return_value = None
    mock_exists.return_value = False

    result = scan_repos(token="tok")
    assert "Procfile" not in result["linguaggio"]


@patch("tech_stack.check_file_exists")
@patch("tech_stack.fetch_file")
@patch("tech_stack.fetch_languages")
@patch("tech_stack.fetch_repos")
def test_scan_repos_dockerfile_categorized_as_tool(mock_repos, mock_langs, mock_file, mock_exists):
    mock_repos.return_value = [{"name": "repo", "fork": False, "topics": []}]
    mock_langs.return_value = {"Dockerfile": 500}
    mock_file.return_value = None
    mock_exists.return_value = False

    result = scan_repos(token="tok")
    assert "Docker" in result["tool"]


@patch("tech_stack.check_file_exists")
@patch("tech_stack.fetch_file")
@patch("tech_stack.fetch_languages")
@patch("tech_stack.fetch_repos")
def test_scan_repos_topics_mapped(mock_repos, mock_langs, mock_file, mock_exists):
    mock_repos.return_value = [{"name": "repo", "fork": False, "topics": ["machine-learning", "docker"]}]
    mock_langs.return_value = {}
    mock_file.return_value = None
    mock_exists.return_value = False

    result = scan_repos(token="tok")
    assert "Machine Learning" in result["ai_ml"]
    assert "Docker" in result["tool"]


@patch("tech_stack.check_file_exists")
@patch("tech_stack.fetch_file")
@patch("tech_stack.fetch_languages")
@patch("tech_stack.fetch_repos")
def test_scan_repos_python_deps_detected(mock_repos, mock_langs, mock_file, mock_exists):
    mock_repos.return_value = [{"name": "repo", "fork": False, "topics": []}]
    mock_langs.return_value = {}
    mock_file.side_effect = lambda _tok, _repo, path: (
        "fastapi>=0.100\npandas>=2.0\n" if path == "requirements.txt" else None
    )
    mock_exists.return_value = False

    result = scan_repos(token="tok")
    assert "FastAPI" in result["framework"]
    assert "Pandas" in result["ai_ml"]


@patch("tech_stack.check_file_exists")
@patch("tech_stack.fetch_file")
@patch("tech_stack.fetch_languages")
@patch("tech_stack.fetch_repos")
def test_scan_repos_js_deps_detected(mock_repos, mock_langs, mock_file, mock_exists):
    mock_repos.return_value = [{"name": "repo", "fork": False, "topics": []}]
    mock_langs.return_value = {}
    mock_file.side_effect = lambda _tok, _repo, path: (
        '{"dependencies": {"react": "^18", "express": "^4"}}' if path == "package.json" else None
    )
    mock_exists.return_value = False

    result = scan_repos(token="tok")
    assert "React" in result["framework"]
    assert "Express" in result["framework"]


@patch("tech_stack.check_file_exists")
@patch("tech_stack.fetch_file")
@patch("tech_stack.fetch_languages")
@patch("tech_stack.fetch_repos")
def test_scan_repos_tool_detection_via_files(mock_repos, mock_langs, mock_file, mock_exists):
    mock_repos.return_value = [{"name": "repo", "fork": False, "topics": []}]
    mock_langs.return_value = {}
    mock_file.return_value = None
    # Dockerfile esiste, .github/workflows esiste
    mock_exists.side_effect = lambda _tok, _repo, path: path in ("Dockerfile", ".github/workflows")

    result = scan_repos(token="tok")
    assert "Docker" in result["tool"]
    assert "GitHub Actions" in result["tool"]


@patch("tech_stack.check_file_exists")
@patch("tech_stack.fetch_file")
@patch("tech_stack.fetch_languages")
@patch("tech_stack.fetch_repos")
def test_scan_repos_git_always_present(mock_repos, mock_langs, mock_file, mock_exists):
    mock_repos.return_value = [
        {"name": "repo1", "fork": False, "topics": []},
        {"name": "repo2", "fork": False, "topics": []},
    ]
    mock_langs.return_value = {}
    mock_file.return_value = None
    mock_exists.return_value = False

    result = scan_repos(token="tok")
    assert result["tool"]["Git"] >= 2


@patch("tech_stack.fetch_repos")
def test_scan_repos_empty_repos_raises(mock_repos):
    mock_repos.return_value = []
    with pytest.raises(RuntimeError, match="No public repos found"):
        scan_repos(token="tok")
