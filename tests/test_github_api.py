import urllib.error
from unittest.mock import MagicMock, patch

import pytest
from common.github_api import (
    _validate_url,
    check_file_exists,
    fetch_file,
    fetch_languages,
    fetch_repos,
)


def test_validate_url_allowed_host():
    _validate_url("https://api.github.com/users/test")


def test_validate_url_rejects_bad_host():
    with pytest.raises(ValueError, match="host not allowed"):
        _validate_url("https://evil.com/api")


def test_validate_url_rejects_bad_scheme():
    with pytest.raises(ValueError, match="scheme not allowed"):
        _validate_url("http://api.github.com/users/test")


def test_validate_url_rejects_file_scheme():
    with pytest.raises(ValueError, match="scheme not allowed"):
        _validate_url("file:///etc/passwd")


@patch("common.github_api.urllib.request.urlopen")
def test_api_get_success(mock_urlopen):
    # First call returns data, second returns empty list to stop pagination
    mock_resp_page1 = MagicMock()
    mock_resp_page1.read.return_value = b'[{"name": "repo1"}]'
    mock_resp_page1.__enter__ = MagicMock(return_value=mock_resp_page1)
    mock_resp_page1.__exit__ = MagicMock(return_value=False)

    mock_resp_page2 = MagicMock()
    mock_resp_page2.read.return_value = b"[]"
    mock_resp_page2.__enter__ = MagicMock(return_value=mock_resp_page2)
    mock_resp_page2.__exit__ = MagicMock(return_value=False)

    mock_urlopen.side_effect = [mock_resp_page1, mock_resp_page2]

    repos = fetch_repos(token="test-token")
    assert len(repos) == 1
    assert repos[0]["name"] == "repo1"


@patch("common.github_api.urllib.request.urlopen")
def test_api_get_404_returns_none(mock_urlopen):
    mock_urlopen.side_effect = urllib.error.HTTPError(
        url="https://api.github.com/test", code=404, msg="Not Found", hdrs={}, fp=None
    )
    result = fetch_file(token="test-token", repo_name="repo", path="missing.txt")
    assert result is None


@patch("common.github_api.urllib.request.urlopen")
def test_api_get_401_raises(mock_urlopen):
    mock_urlopen.side_effect = urllib.error.HTTPError(
        url="https://api.github.com/test", code=401, msg="Unauthorized", hdrs={}, fp=None
    )
    with pytest.raises(urllib.error.HTTPError):
        fetch_repos(token="bad-token")


@patch("common.github_api.urllib.request.urlopen")
def test_api_get_429_raises(mock_urlopen):
    mock_urlopen.side_effect = urllib.error.HTTPError(
        url="https://api.github.com/test", code=429, msg="Rate Limited", hdrs={}, fp=None
    )
    with pytest.raises(urllib.error.HTTPError):
        fetch_repos(token="test-token")


@patch("common.github_api.urllib.request.urlopen")
def test_api_get_network_error_returns_none(mock_urlopen):
    mock_urlopen.side_effect = urllib.error.URLError("Connection refused")
    result = fetch_languages(token="test-token", repo_name="repo")
    assert result == {}


@patch("common.github_api.urllib.request.urlopen")
def test_fetch_repos_empty_logs_warning(mock_urlopen):
    mock_urlopen.side_effect = urllib.error.URLError("timeout")
    repos = fetch_repos(token="test-token")
    assert repos == []


@patch("common.github_api.urllib.request.urlopen")
def test_check_file_exists_true(mock_urlopen):
    mock_resp = MagicMock()
    mock_resp.read.return_value = b"{}"
    mock_resp.__enter__ = MagicMock(return_value=mock_resp)
    mock_resp.__exit__ = MagicMock(return_value=False)
    mock_urlopen.return_value = mock_resp

    assert check_file_exists(token="test-token", repo_name="repo", path="README.md") is True


@patch("common.github_api.urllib.request.urlopen")
def test_check_file_exists_false(mock_urlopen):
    mock_urlopen.side_effect = urllib.error.HTTPError(
        url="https://api.github.com/test", code=404, msg="Not Found", hdrs={}, fp=None
    )
    assert check_file_exists(token="test-token", repo_name="repo", path="missing.txt") is False


@patch("common.github_api.urllib.request.urlopen")
def test_fetch_repos_invalid_json_returns_empty(mock_urlopen):
    mock_resp = MagicMock()
    mock_resp.read.return_value = b"<html>Service Unavailable</html>"
    mock_resp.__enter__ = MagicMock(return_value=mock_resp)
    mock_resp.__exit__ = MagicMock(return_value=False)
    mock_urlopen.return_value = mock_resp

    repos = fetch_repos(token="test-token")
    assert repos == []


@patch("common.github_api.urllib.request.urlopen")
def test_fetch_languages_invalid_json_returns_empty(mock_urlopen):
    mock_resp = MagicMock()
    mock_resp.read.return_value = b"not json"
    mock_resp.__enter__ = MagicMock(return_value=mock_resp)
    mock_resp.__exit__ = MagicMock(return_value=False)
    mock_urlopen.return_value = mock_resp

    result = fetch_languages(token="test-token", repo_name="repo")
    assert result == {}


@patch("common.github_api.urllib.request.urlopen")
def test_fetch_file_non_utf8_returns_none(mock_urlopen):
    mock_resp = MagicMock()
    mock_resp.read.return_value = b"\x80\x81\x82\xff"
    mock_resp.__enter__ = MagicMock(return_value=mock_resp)
    mock_resp.__exit__ = MagicMock(return_value=False)
    mock_urlopen.return_value = mock_resp

    result = fetch_file(token="test-token", repo_name="repo", path="binary.dat")
    assert result is None
