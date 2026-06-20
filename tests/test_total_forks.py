import re

import pytest
import total_forks
from total_forks import compute_total_forks, main, make_total_forks_svg


def _badge_width(svg: str) -> int:
    match = re.search(r'<svg[^>]*\bwidth="(\d+)"', svg)
    assert match is not None
    return int(match.group(1))


def test_compute_total_forks_sums_forks():
    repos = [
        {"name": "a", "forks_count": 10, "fork": False},
        {"name": "b", "forks_count": 5, "fork": False},
    ]
    assert compute_total_forks(repos) == 15


def test_compute_total_forks_excludes_forks():
    repos = [
        {"name": "own", "forks_count": 7, "fork": False},
        {"name": "forked", "forks_count": 999, "fork": True},
    ]
    assert compute_total_forks(repos) == 7


def test_compute_total_forks_empty_returns_zero():
    assert compute_total_forks([]) == 0


def test_compute_total_forks_missing_field_treated_as_zero():
    repos = [{"name": "a", "fork": False}, {"name": "b", "forks_count": 3, "fork": False}]
    assert compute_total_forks(repos) == 3


def test_make_svg_is_svg_element():
    svg = make_total_forks_svg(42).strip()
    assert svg.startswith("<svg") and svg.endswith("</svg>")


def test_make_svg_contains_fork_count():
    assert ">1234<" in make_total_forks_svg(1234)


def test_make_svg_aria_label_reports_count():
    svg = make_total_forks_svg(88)
    assert 'aria-label="forks: 88"' in svg


def test_make_svg_width_grows_with_digits():
    assert _badge_width(make_total_forks_svg(1000000)) > _badge_width(make_total_forks_svg(7))


# ---------------------------------------------------------------------------
# main() — integration tests
# ---------------------------------------------------------------------------


def test_main_demo_writes_badge_with_given_count(tmp_path, monkeypatch):
    monkeypatch.setattr(total_forks, "ASSETS_DIR", tmp_path)
    monkeypatch.setattr("sys.argv", ["total_forks", "--demo", "--forks", "9"])
    main()
    out = tmp_path / "total_forks.svg"
    assert 'aria-label="forks: 9"' in out.read_text(encoding="utf-8")


def test_main_no_token_exits_without_writing(tmp_path, monkeypatch):
    monkeypatch.setattr(total_forks, "ASSETS_DIR", tmp_path)
    monkeypatch.setattr("sys.argv", ["total_forks"])
    monkeypatch.delenv("SNAKE_TOKEN", raising=False)
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 1
    assert not (tmp_path / "total_forks.svg").exists()


def test_main_token_success_writes_summed_count(tmp_path, monkeypatch):
    monkeypatch.setattr(total_forks, "ASSETS_DIR", tmp_path)
    monkeypatch.setattr("sys.argv", ["total_forks"])
    monkeypatch.setenv("SNAKE_TOKEN", "tok")
    repos = [
        {"name": "a", "forks_count": 20, "fork": False},
        {"name": "b", "forks_count": 4, "fork": False},
    ]
    monkeypatch.setattr(total_forks, "fetch_repos", lambda _t: repos)
    main()
    assert 'aria-label="forks: 24"' in (tmp_path / "total_forks.svg").read_text(encoding="utf-8")


def test_main_empty_repos_exits_to_avoid_bogus_zero(tmp_path, monkeypatch):
    monkeypatch.setattr(total_forks, "ASSETS_DIR", tmp_path)
    monkeypatch.setattr("sys.argv", ["total_forks"])
    monkeypatch.setenv("SNAKE_TOKEN", "tok")
    monkeypatch.setattr(total_forks, "fetch_repos", lambda _t: [])
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 1
    assert not (tmp_path / "total_forks.svg").exists()


def test_main_write_failure_exits(tmp_path, monkeypatch):
    monkeypatch.setattr(total_forks, "ASSETS_DIR", tmp_path)
    monkeypatch.setattr("sys.argv", ["total_forks", "--demo", "--forks", "3"])

    def _boom(*_a, **_k):
        raise OSError("disk full")

    monkeypatch.setattr("pathlib.Path.write_text", _boom)
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 1
