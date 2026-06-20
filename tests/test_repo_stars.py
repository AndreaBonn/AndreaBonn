import re

import pytest
import repo_stars
from repo_stars import build_star_map, main, make_stars_badge, write_badges


def _badge_width(svg: str) -> int:
    match = re.search(r'<svg[^>]*\bwidth="(\d+)"', svg)
    assert match is not None
    return int(match.group(1))


def test_build_star_map_maps_name_to_stars():
    repos = [
        {"name": "RepoA", "stargazers_count": 12},
        {"name": "RepoB", "stargazers_count": 0},
    ]
    assert build_star_map(repos) == {"RepoA": 12, "RepoB": 0}


def test_build_star_map_missing_count_is_zero():
    assert build_star_map([{"name": "RepoA"}]) == {"RepoA": 0}


def test_build_star_map_skips_unsafe_names():
    repos = [
        {"name": "good-repo", "stargazers_count": 3},
        {"name": "../evil", "stargazers_count": 99},
        {"name": "has space", "stargazers_count": 1},
    ]
    assert build_star_map(repos) == {"good-repo": 3}


def test_build_star_map_skips_missing_name():
    assert build_star_map([{"stargazers_count": 5}]) == {}


def test_make_badge_shows_count():
    svg = make_stars_badge(42)
    assert ">42</text>" in svg
    assert 'aria-label="stars: 42"' in svg


def test_make_badge_is_blue_flat_square():
    svg = make_stars_badge(0)
    assert 'fill="#007ec6"' in svg
    assert 'shape-rendering="crispEdges"' in svg


def test_make_badge_is_svg_element():
    svg = make_stars_badge(7).strip()
    assert svg.startswith("<svg") and svg.endswith("</svg>")


def test_make_badge_wider_for_more_digits():
    assert _badge_width(make_stars_badge(1234)) > _badge_width(make_stars_badge(1))


def test_write_badges_creates_one_file_per_repo(tmp_path):
    star_map = {"RepoA": 5, "RepoB": 0}
    written = write_badges(star_map, tmp_path)
    assert written == 2
    assert (tmp_path / "RepoA.svg").read_text(encoding="utf-8").count(">5</text>") == 1
    assert (tmp_path / "RepoB.svg").exists()


def test_write_badges_creates_missing_dir(tmp_path):
    out = tmp_path / "stars"
    write_badges({"RepoA": 1}, out)
    assert (out / "RepoA.svg").exists()


def test_write_badges_write_failure_exits(tmp_path, monkeypatch):
    def _boom(*_a, **_k):
        raise OSError("disk full")

    monkeypatch.setattr("pathlib.Path.write_text", _boom)
    with pytest.raises(SystemExit) as exc:
        write_badges({"RepoA": 1}, tmp_path)
    assert exc.value.code == 1


# ---------------------------------------------------------------------------
# main() — integration tests
# ---------------------------------------------------------------------------


def test_main_demo_writes_badges_for_demo_repos(tmp_path, monkeypatch):
    monkeypatch.setattr(repo_stars, "ASSETS_DIR", tmp_path)
    monkeypatch.setattr("sys.argv", ["repo_stars", "--demo"])
    main()
    stars_dir = tmp_path / "stars"
    assert (stars_dir / "DemoRepo.svg").exists()
    assert (stars_dir / "AnotherRepo.svg").exists()


def test_main_no_token_exits_without_writing(tmp_path, monkeypatch):
    monkeypatch.setattr(repo_stars, "ASSETS_DIR", tmp_path)
    monkeypatch.setattr("sys.argv", ["repo_stars"])
    monkeypatch.delenv("SNAKE_TOKEN", raising=False)
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 1
    assert not (tmp_path / "stars").exists()


def test_main_token_success_writes_badge_per_repo(tmp_path, monkeypatch):
    monkeypatch.setattr(repo_stars, "ASSETS_DIR", tmp_path)
    monkeypatch.setattr("sys.argv", ["repo_stars"])
    monkeypatch.setenv("SNAKE_TOKEN", "tok")
    repos = [
        {"name": "RepoA", "stargazers_count": 8},
        {"name": "RepoB", "stargazers_count": 0},
    ]
    monkeypatch.setattr(repo_stars, "fetch_repos", lambda _t: repos)
    main()
    assert ">8</text>" in (tmp_path / "stars" / "RepoA.svg").read_text(encoding="utf-8")
    assert (tmp_path / "stars" / "RepoB.svg").exists()


def test_main_empty_repos_exits_to_avoid_wiping_badges(tmp_path, monkeypatch):
    monkeypatch.setattr(repo_stars, "ASSETS_DIR", tmp_path)
    monkeypatch.setattr("sys.argv", ["repo_stars"])
    monkeypatch.setenv("SNAKE_TOKEN", "tok")
    monkeypatch.setattr(repo_stars, "fetch_repos", lambda _t: [])
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 1
