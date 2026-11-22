"""
Where each project's test count and coverage come from.

Every key must match an ``./assets/quality/<key>.svg`` reference in README.md
(enforced by a test). A value is either a static number, for repos that publish
no badge JSON, or the URL of a shields.io endpoint JSON published by the repo.
"""

from dataclasses import dataclass

from common.config import USERNAME

RAW_BASE = f"https://raw.githubusercontent.com/{USERNAME}"


@dataclass(frozen=True)
class QualitySource:
    """Test count and coverage source: a static value or an endpoint JSON URL."""

    tests: int | str
    coverage: float | str

    def __post_init__(self) -> None:
        if isinstance(self.tests, int) and self.tests < 0:
            raise ValueError(f"Static test count must be >= 0, got {self.tests}")
        if not isinstance(self.coverage, str) and not 0 <= self.coverage <= 100:
            raise ValueError(f"Static coverage must be within 0-100, got {self.coverage}")


def endpoint(
    repo: str,
    base: str = "main/badges",
    tests_file: str = "test-badge.json",
    coverage_file: str = "coverage-badge.json",
) -> QualitySource:
    """Build a source pointing at the badge JSON files published inside ``repo``."""
    return QualitySource(
        tests=f"{RAW_BASE}/{repo}/{base}/{tests_file}",
        coverage=f"{RAW_BASE}/{repo}/{base}/{coverage_file}",
    )


def _branch_badges(repo: str) -> QualitySource:
    return endpoint(repo, base="badges", tests_file="tests.json", coverage_file="coverage.json")


QUALITY_SOURCES: dict[str, QualitySource] = {
    # Web App & PWA. Static values (these repos publish no badge JSON), copied on
    # 2026-11-22 from the hand-written README badges: update them by hand.
    "BudgeeByBonn": QualitySource(tests=12123, coverage=98.4),
    "BetTracker-by-Bonn": QualitySource(tests=1715, coverage=95.54),
    "PlotMark": QualitySource(tests=2580, coverage=99.92),
    "meteo-e-spiagge": QualitySource(tests=692, coverage=92.3),
    "card-quiver-by-bonn": QualitySource(tests=1558, coverage=98.0),
    "LifeTrackByBonn": QualitySource(tests=5636, coverage=95.8),
    "RoomMatesByBonn": QualitySource(tests=3006, coverage=87.6),
    "my-team-ai-config-hub": QualitySource(tests=244, coverage=99.57),
    "impara-italiano": endpoint("impara-italiano"),
    "lerne-deutsch": endpoint("lerne-deutsch"),
    # Browser Extensions
    "web-article-summarizer-chrome": endpoint("web-article-summarizer-chrome"),
    "web-article-summarizer-firefox": endpoint("web-article-summarizer-firefox"),
    "quick-tab-launcher": endpoint("quick-tab-launcher"),
    "firefox-session-snapshot": endpoint("firefox-session-snapshot"),
    "dipendenti-in-cloud-notifier": endpoint("dipendenti-in-cloud-notifier"),
    # Mobile / Android
    "AutoGPS-by-Bonn": QualitySource(tests=299, coverage=93.9),
    # Desktop, CLI & TUI
    "command-quiver": endpoint("command-quiver"),
    "sysbar": endpoint("sysbar"),
    "where-is-my-memory": endpoint("where-is-my-memory"),
    "my-workplace-tui": endpoint("my-workplace-tui"),
    "deadline-aura": endpoint("deadline-aura"),
    "nautilus-extensions": endpoint("nautilus-extensions"),
    "core-dump-game": endpoint("core-dump-game"),
    # Dev Tools / GitHub Actions
    "ai-pr-reviewer": endpoint("ai-pr-reviewer"),
    "ai-changelog-generator": endpoint("ai-changelog-generator"),
    "claude-code-available-tools": endpoint("claude-code-available-tools"),
    "remote-terminal-bot": endpoint("remote-terminal-bot"),
    "agy-profiles": endpoint("agy-profiles", base="badges"),
    # Media & AI
    "video-anonimyzer": endpoint("video-anonimyzer"),
    "text-to-speech": endpoint("text-to-speech"),
    "speech-to-text": endpoint("speech-to-text", base="badges/badges"),
    "clone-my-voice": endpoint("clone-my-voice"),
    "image-generator": endpoint("image-generator", base="badges", coverage_file="coverage-backend-badge.json"),
    "audio-filename-fixer": endpoint("audio-filename-fixer"),
    # Other projects
    "campionato-serie-c-26-27": _branch_badges("campionato-serie-c-26-27"),
    "campionato-promozione-26-27": _branch_badges("campionato-promozione-26-27"),
    "campionato-fenice-fipav-26-27": _branch_badges("campionato-fenice-fipav-26-27"),
    "love-pages-by-Bonn": endpoint("love-pages-by-Bonn"),
}
