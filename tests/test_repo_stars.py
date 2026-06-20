import re

from repo_stars import build_star_map, make_stars_badge, write_badges


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
