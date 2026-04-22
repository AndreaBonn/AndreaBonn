from tech_stack import (
    DEMO_DATA,
    generate_svg,
    measure_text,
    parse_package_json,
    parse_pyproject_toml,
    parse_requirements_txt,
)


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
    content = 'dependencies = ["requests>=2.31", "flask>=2.0"]\n'
    result = parse_pyproject_toml(content)
    assert "requests" in result
    assert "flask" in result


def test_parse_pyproject_toml_multiline():
    content = """
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
