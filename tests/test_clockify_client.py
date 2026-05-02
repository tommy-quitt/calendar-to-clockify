import pytest
from unittest.mock import patch, MagicMock
from clockify_client import ClockifyClient

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