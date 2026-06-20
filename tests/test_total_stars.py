import re

import pytest
import total_stars
from total_stars import compute_total_stars, main, make_total_stars_svg


def _badge_width(svg: str) -> int:
    match = re.search(r'<svg[^>]*\bwidth="(\d+)"', svg)
    assert match is not None
    return int(match.group(1))


def test_compute_total_stars_sums_stargazers():
    repos = [
        {"name": "a", "stargazers_count": 10, "fork": False},
        {"name": "b", "stargazers_count": 5, "fork": False},
    ]
    assert compute_total_stars(repos) == 15


def test_compute_total_stars_excludes_forks():
    repos = [
        {"name": "own", "stargazers_count": 7, "fork": False},
        {"name": "forked", "stargazers_count": 999, "fork": True},
    ]
    assert compute_total_stars(repos) == 7


def test_compute_total_stars_empty_returns_zero():
    assert compute_total_stars([]) == 0


def test_compute_total_stars_missing_field_treated_as_zero():
    repos = [{"name": "a", "fork": False}, {"name": "b", "stargazers_count": 3, "fork": False}]
    assert compute_total_stars(repos) == 3


def test_make_svg_is_svg_element():
    svg = make_total_stars_svg(42).strip()
    assert svg.startswith("<svg") and svg.endswith("</svg>")


def test_make_svg_contains_star_count():
    assert ">1234<" in make_total_stars_svg(1234)


def test_make_svg_aria_label_reports_count():
    svg = make_total_stars_svg(88)
    assert 'aria-label="stars: 88"' in svg


def test_make_svg_width_grows_with_digits():
    assert _badge_width(make_total_stars_svg(1000000)) > _badge_width(make_total_stars_svg(7))


# ---------------------------------------------------------------------------
# main() — integration tests
# ---------------------------------------------------------------------------


def test_main_demo_writes_badge_with_given_count(tmp_path, monkeypatch):
    monkeypatch.setattr(total_stars, "ASSETS_DIR", tmp_path)
    monkeypatch.setattr("sys.argv", ["total_stars", "--demo", "--stars", "77"])
    main()
    out = tmp_path / "total_stars.svg"
    assert 'aria-label="stars: 77"' in out.read_text(encoding="utf-8")


def test_main_no_token_exits_without_writing(tmp_path, monkeypatch):
    monkeypatch.setattr(total_stars, "ASSETS_DIR", tmp_path)
    monkeypatch.setattr("sys.argv", ["total_stars"])
    monkeypatch.delenv("SNAKE_TOKEN", raising=False)
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 1
    assert not (tmp_path / "total_stars.svg").exists()


def test_main_token_success_writes_summed_count(tmp_path, monkeypatch):
    monkeypatch.setattr(total_stars, "ASSETS_DIR", tmp_path)
    monkeypatch.setattr("sys.argv", ["total_stars"])
    monkeypatch.setenv("SNAKE_TOKEN", "tok")
    repos = [
        {"name": "a", "stargazers_count": 30, "fork": False},
        {"name": "b", "stargazers_count": 12, "fork": False},
    ]
    monkeypatch.setattr(total_stars, "fetch_repos", lambda _t: repos)
    main()
    assert 'aria-label="stars: 42"' in (tmp_path / "total_stars.svg").read_text(encoding="utf-8")


def test_main_empty_repos_exits_to_avoid_bogus_zero(tmp_path, monkeypatch):
    monkeypatch.setattr(total_stars, "ASSETS_DIR", tmp_path)
    monkeypatch.setattr("sys.argv", ["total_stars"])
    monkeypatch.setenv("SNAKE_TOKEN", "tok")
    monkeypatch.setattr(total_stars, "fetch_repos", lambda _t: [])
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 1
    assert not (tmp_path / "total_stars.svg").exists()


def test_main_write_failure_exits(tmp_path, monkeypatch):
    monkeypatch.setattr(total_stars, "ASSETS_DIR", tmp_path)
    monkeypatch.setattr("sys.argv", ["total_stars", "--demo", "--stars", "5"])

    def _boom(*_a, **_k):
        raise OSError("disk full")

    monkeypatch.setattr("pathlib.Path.write_text", _boom)
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 1
