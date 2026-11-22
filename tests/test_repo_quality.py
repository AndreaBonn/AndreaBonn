import http.client
import json
import re
import urllib.error
from pathlib import Path

import pytest
import repo_quality
from quality_sources import QUALITY_SOURCES, QualitySource
from repo_quality import (
    BadgeFetchError,
    build_badge,
    coverage_color,
    fetch_badge_message,
    format_coverage,
    format_test_count,
    main,
    make_quality_badge,
    parse_coverage,
    parse_test_count,
    write_quality_badges,
)

README = Path(__file__).parent.parent / "README.md"


def _badge_width(svg: str) -> int:
    match = re.search(r'<svg[^>]*\bwidth="(\d+)"', svg)
    assert match is not None
    return int(match.group(1))


# ---------------------------------------------------------------------------
# Parsing shields endpoint messages
# ---------------------------------------------------------------------------


def test_parse_test_count_reads_passed_number():
    assert parse_test_count("1383 passed") == 1383


@pytest.mark.parametrize("message", ["0 passed", "no results", "pending", "", "12 failed"])
def test_parse_test_count_rejects_values_that_look_like_errors(message):
    assert parse_test_count(message) is None


@pytest.mark.parametrize(("message", "expected"), [("98.4%", 98.4), ("100.0%", 100.0), ("85%", 85.0)])
def test_parse_coverage_reads_percentage(message, expected):
    assert parse_coverage(message) == expected


@pytest.mark.parametrize("message", ["pending", "", "101%", "98.4"])
def test_parse_coverage_rejects_invalid_values(message):
    assert parse_coverage(message) is None


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("count", "expected"),
    [(692, "692"), (999, "999"), (1000, "1k"), (1558, "1.5k"), (12123, "12.1k")],
)
def test_format_test_count_abbreviates_thousands_without_rounding_up(count, expected):
    assert format_test_count(count) == expected


@pytest.mark.parametrize(
    ("pct", "expected"),
    [(98.4, "98.4%"), (100.0, "100%"), (99.96, "99.9%"), (95.54, "95.5%"), (98.0, "98%")],
)
def test_format_coverage_truncates_to_one_decimal(pct, expected):
    assert format_coverage(pct) == expected


def test_coverage_color_green_at_threshold_and_above():
    assert coverage_color(90.0) == coverage_color(100.0) == repo_quality.COVERAGE_GOOD


def test_coverage_color_amber_below_threshold():
    assert coverage_color(89.9) == repo_quality.COVERAGE_LOW
    assert repo_quality.COVERAGE_LOW != repo_quality.COVERAGE_GOOD


# ---------------------------------------------------------------------------
# Badge rendering
# ---------------------------------------------------------------------------


def test_make_quality_badge_shows_both_values():
    svg = make_quality_badge(tests=12123, coverage=98.4)
    assert ">12.1k</text>" in svg
    assert ">98.4%</text>" in svg
    assert 'aria-label="12123 tests passed, 98.4% coverage"' in svg
    assert repo_quality.COVERAGE_GOOD in svg


def test_make_quality_badge_has_fixed_width_regardless_of_values():
    assert _badge_width(make_quality_badge(tests=5, coverage=100.0)) == _badge_width(
        make_quality_badge(tests=12123, coverage=99.9)
    )


def test_make_quality_badge_missing_values_render_dash_without_coverage_color():
    svg = make_quality_badge(tests=None, coverage=None)
    assert svg.count(">–</text>") == 2
    assert repo_quality.COVERAGE_GOOD not in svg
    assert repo_quality.COVERAGE_LOW not in svg
    assert 'aria-label="tests not available, coverage not available"' in svg


def test_make_quality_badge_low_coverage_is_amber():
    assert repo_quality.COVERAGE_LOW in make_quality_badge(tests=10, coverage=77.0)


# ---------------------------------------------------------------------------
# Fetching
# ---------------------------------------------------------------------------


class _FakeResponse:
    def __init__(self, body: bytes):
        self._body = body

    def read(self, size: int = -1) -> bytes:
        return self._body if size < 0 else self._body[:size]

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        return False


def _serve(monkeypatch, body: bytes):
    monkeypatch.setattr(repo_quality.urllib.request, "urlopen", lambda *_a, **_k: _FakeResponse(body))


def test_fetch_badge_message_returns_message(monkeypatch):
    _serve(monkeypatch, json.dumps({"message": "154 passed"}).encode())
    assert fetch_badge_message("https://raw.githubusercontent.com/AndreaBonn/x/main/b.json") == "154 passed"


@pytest.mark.parametrize(
    "url",
    [
        "https://evil.example.com/b.json",
        "http://raw.githubusercontent.com/AndreaBonn/x/main/b.json",
        "https://raw.githubusercontent.com.evil.com/b.json",
    ],
)
def test_fetch_badge_message_rejects_foreign_host_or_scheme(url):
    with pytest.raises(ValueError, match="not allowed"):
        fetch_badge_message(url)


def test_fetch_badge_message_truncated_read_raises_fetch_error(monkeypatch):
    class _Truncated(_FakeResponse):
        def read(self, *_a):
            raise http.client.IncompleteRead(b"{")

    monkeypatch.setattr(repo_quality.urllib.request, "urlopen", lambda *_a, **_k: _Truncated(b""))
    with pytest.raises(BadgeFetchError):
        fetch_badge_message("https://raw.githubusercontent.com/AndreaBonn/x/main/b.json")


def test_fetch_badge_message_network_error_raises_fetch_error(monkeypatch):
    def _boom(*_a, **_k):
        raise urllib.error.URLError("offline")

    monkeypatch.setattr(repo_quality.urllib.request, "urlopen", _boom)
    with pytest.raises(BadgeFetchError):
        fetch_badge_message("https://raw.githubusercontent.com/AndreaBonn/x/main/b.json")


@pytest.mark.parametrize("payload", [{"label": "tests"}, {"message": 12}, ["not", "a", "dict"]])
def test_fetch_badge_message_without_string_message_raises_fetch_error(monkeypatch, payload):
    _serve(monkeypatch, json.dumps(payload).encode())
    with pytest.raises(BadgeFetchError, match="message"):
        fetch_badge_message("https://raw.githubusercontent.com/AndreaBonn/x/main/b.json")


def test_fetch_badge_message_bad_json_raises_fetch_error(monkeypatch):
    _serve(monkeypatch, b"<html>not json</html>")
    with pytest.raises(BadgeFetchError):
        fetch_badge_message("https://raw.githubusercontent.com/AndreaBonn/x/main/b.json")


# ---------------------------------------------------------------------------
# build_badge / write_quality_badges
# ---------------------------------------------------------------------------


def test_build_badge_static_source_needs_no_network(monkeypatch):
    monkeypatch.setattr(repo_quality, "fetch_badge_message", pytest.fail)
    svg, complete = build_badge(QualitySource(tests=299, coverage=93.9))
    assert ">299</text>" in svg and ">93.9%</text>" in svg
    assert complete


def test_build_badge_endpoint_with_error_message_renders_dash(monkeypatch):
    messages = {"t.json": "pending", "c.json": "89.98%"}
    monkeypatch.setattr(repo_quality, "fetch_badge_message", lambda url: messages[url.rsplit("/", 1)[1]])
    svg, complete = build_badge(QualitySource(tests="https://h/t.json", coverage="https://h/c.json"))
    assert ">–</text>" in svg and ">89.9%</text>" in svg
    assert not complete


def test_write_quality_badges_keeps_existing_file_when_upstream_value_is_invalid(tmp_path, monkeypatch):
    monkeypatch.setattr(repo_quality, "fetch_badge_message", lambda _url: "0 passed")
    (tmp_path / "RepoA.svg").write_text("previous good badge", encoding="utf-8")
    sources = {"RepoA": QualitySource(tests="https://h/t.json", coverage=90.0)}
    assert write_quality_badges(sources, tmp_path) == 0
    assert (tmp_path / "RepoA.svg").read_text(encoding="utf-8") == "previous good badge"


def test_write_quality_badges_overwrites_existing_file_when_values_are_valid(tmp_path, monkeypatch):
    monkeypatch.setattr(repo_quality, "fetch_badge_message", lambda _url: "154 passed")
    (tmp_path / "RepoA.svg").write_text("previous", encoding="utf-8")
    sources = {"RepoA": QualitySource(tests="https://h/t.json", coverage=90.0)}
    assert write_quality_badges(sources, tmp_path) == 1
    assert ">154</text>" in (tmp_path / "RepoA.svg").read_text(encoding="utf-8")


@pytest.mark.parametrize(("tests", "coverage"), [(-1, 90.0), (10, 150.0), (10, -0.1)])
def test_quality_source_rejects_invalid_static_values(tests, coverage):
    with pytest.raises(ValueError):
        QualitySource(tests=tests, coverage=coverage)


def test_write_quality_badges_keeps_existing_file_when_fetch_fails(tmp_path, monkeypatch):
    def _fail(_url):
        raise BadgeFetchError("offline")

    monkeypatch.setattr(repo_quality, "fetch_badge_message", _fail)
    (tmp_path / "RepoA.svg").write_text("previous", encoding="utf-8")
    sources = {"RepoA": QualitySource(tests="https://h/t.json", coverage=90.0)}
    assert write_quality_badges(sources, tmp_path) == 0
    assert (tmp_path / "RepoA.svg").read_text(encoding="utf-8") == "previous"


def test_write_quality_badges_without_previous_file_writes_partial_badge(tmp_path, monkeypatch):
    def _fail(_url):
        raise BadgeFetchError("offline")

    monkeypatch.setattr(repo_quality, "fetch_badge_message", _fail)
    sources = {"RepoA": QualitySource(tests="https://h/t.json", coverage=90.0)}
    assert write_quality_badges(sources, tmp_path) == 1
    svg = (tmp_path / "RepoA.svg").read_text(encoding="utf-8")
    assert ">–</text>" in svg and ">90%</text>" in svg


def test_write_quality_badges_creates_dir_and_one_file_per_repo(tmp_path):
    out = tmp_path / "quality"
    sources = {"RepoA": QualitySource(tests=10, coverage=99.0), "RepoB": QualitySource(tests=20, coverage=80.0)}
    assert write_quality_badges(sources, out) == 2
    assert ">10</text>" in (out / "RepoA.svg").read_text(encoding="utf-8")
    assert (out / "RepoB.svg").exists()


def test_main_writes_badges_into_assets_quality(tmp_path, monkeypatch):
    monkeypatch.setattr(repo_quality, "ASSETS_DIR", tmp_path)
    monkeypatch.setattr(repo_quality, "QUALITY_SOURCES", {"RepoA": QualitySource(tests=1, coverage=100.0)})
    main()
    svg = (tmp_path / "quality" / "RepoA.svg").read_text(encoding="utf-8")
    assert ">1</text>" in svg and ">100%</text>" in svg


# ---------------------------------------------------------------------------
# README <-> sources consistency
# ---------------------------------------------------------------------------


def test_every_readme_quality_badge_has_a_source_and_vice_versa():
    referenced = set(re.findall(r"\./assets/quality/([A-Za-z0-9._-]+)\.svg", README.read_text(encoding="utf-8")))
    assert referenced, "README must reference at least one quality badge"
    assert referenced == set(QUALITY_SOURCES)
