import re

from total_stars import compute_total_stars, make_total_stars_svg


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
