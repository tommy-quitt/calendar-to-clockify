import pytest
from unittest.mock import patch, MagicMock
from clockify_client import ClockifyClient, RateLimitError

@patch('clockify_client.requests.get')
def test_get_projects(mock_get):
    mock_get.return_value.json.return_value = [
        {"id": "1", "name": "Proj1", "archived": False},
        {"id": "2", "name": "Proj2", "archived": True}
    ]
    mock_get.return_value.raise_for_status = lambda: None
    client = ClockifyClient('api', 'ws')
    projects = client.get_projects()
    assert len(projects) == 2
    assert projects[0]["name"] == "Proj1"

@patch('clockify_client.requests.get')
def test_resolve_project_name(mock_get):
    mock_get.return_value.json.return_value = [
        {"id": "1", "name": "Proj1", "archived": False}
    ]
    mock_get.return_value.raise_for_status = lambda: None
    client = ClockifyClient('api', 'ws')
    pid = client.resolve_project_name("Proj1")
    assert pid == "1"
    assert client.resolve_project_name("Nonexistent") is None

@patch('clockify_client.requests.post')
@patch('clockify_client.requests.get')
def test_create_time_entry(mock_get, mock_post):
    # Mock tag ensure
    mock_get.return_value.json.return_value = [ {"id": "tagid", "name": "calendar-bot"} ]
    mock_get.return_value.raise_for_status = lambda: None
    # Mock time entry creation
    mock_post.return_value.json.return_value = {"id": "entryid"}
    mock_post.return_value.raise_for_status = lambda: None
    client = ClockifyClient('api', 'ws')
    result = client.create_time_entry('start', 'end', 'desc', 'projid')
    assert result["id"] == "entryid" 

def _resp(status, headers=None):
    r = MagicMock()
    r.status_code = status
    r.headers = headers or {}
    return r


@patch('clockify_client.time.sleep')
@patch('clockify_client.requests.get')
def test_retries_short_rate_limit(mock_get, mock_sleep):
    mock_get.side_effect = [_resp(429, {"Retry-After": "3"}), _resp(200)]
    client = ClockifyClient('key', 'ws')
    assert client._request("get", "url").status_code == 200
    assert mock_get.call_count == 2
    mock_sleep.assert_any_call(3.0)


@patch('clockify_client.time.sleep')
@patch('clockify_client.requests.get')
def test_long_rate_limit_raises_instead_of_sleeping(mock_get, mock_sleep):
    mock_get.return_value = _resp(429, {"Retry-After": "3000"})
    client = ClockifyClient('key', 'ws')
    with pytest.raises(RateLimitError, match="try again after"):
        client._request("get", "url")
    assert mock_get.call_count == 1


@patch('clockify_client.requests.get')
def test_tags_fetched_once_for_map_and_ensure(mock_get):
    mock_get.return_value.json.return_value = [{"id": "t1", "name": "calendar-bot"}]
    client = ClockifyClient('key', 'ws')
    assert client.get_tag_map() == {"t1": "calendar-bot"}
    assert client.ensure_tag() == "t1"
    assert mock_get.call_count == 1


@patch('clockify_client.time.sleep')
@patch('clockify_client.requests.get')
def test_rate_limit_without_retry_after_stops_immediately(mock_get, mock_sleep):
    mock_get.return_value = _resp(429)
    client = ClockifyClient('key', 'ws')
    with pytest.raises(RateLimitError):
        client._request("get", "url")
    assert mock_get.call_count == 1
    mock_sleep.assert_not_called()
