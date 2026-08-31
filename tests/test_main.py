import pytest
from unittest.mock import MagicMock, patch
from types import SimpleNamespace
from main import (
    is_reclaim_task, is_all_day, has_invitees, handle_external_organizer,
    is_noproject_tagged, is_ignored_attendee_only, parse_args, ConfigError,
    process_events
)

def test_is_reclaim_task():
    event = {"description": "This is a reclaim.ai task"}
    assert is_reclaim_task(event)
    event = {"description": "Regular event"}
    assert not is_reclaim_task(event)

def test_is_all_day():
    event = {"start": {"date": "2024-01-01"}}
    assert is_all_day(event)
    event = {"start": {"dateTime": "2024-01-01T10:00:00Z"}}
    assert not is_all_day(event)

def test_has_invitees():
    event = {"attendees": [ {"email": "a@b.com"} ]}
    assert has_invitees(event)
    event = {"attendees": []}
    assert not has_invitees(event)
    event = {}
    assert not has_invitees(event)

def test_handle_external_organizer():
    event = {
        "organizer": {"email": "external@other.com"},
        "attendees": [
            {"email": "external2@other.com"},
            {"email": "someone@wechange.company"}
        ]
    }
    assert handle_external_organizer(event)
    assert event["external_actor_email"] == "external2@other.com"
    event = {
        "organizer": {"email": "external@other.com"},
        "attendees": [
            {"email": "someone@wechange.company"}
        ]
    }
    assert handle_external_organizer(event)
    assert event["external_actor_email"] == "external@other.com"
    event = {
        "organizer": {"email": "someone@wechange.company"},
        "attendees": [
            {"email": "external2@other.com"}
        ]
    }
    assert handle_external_organizer(event)

def test_handle_external_organizer_skips_resource_calendar():
    event = {
        "organizer": {"email": "external@ingenio.com"},
        "attendees": [
            {"email": "c_room@resource.calendar.google.com"},
            {"email": "someone@wechange.company"},
            {"email": "other@ingenio.com"},
        ]
    }
    assert handle_external_organizer(event)
    assert event["external_actor_email"] == "other@ingenio.com"

    event = {
        "organizer": {"email": "external@ingenio.com"},
        "attendees": [
            {"email": "c_room@resource.calendar.google.com"},
            {"email": "someone@wechange.company"},
        ]
    }
    assert handle_external_organizer(event)
    assert event["external_actor_email"] == "external@ingenio.com"

def test_is_noproject_tagged():
    event = {"description": "#noproject something"}
    assert is_noproject_tagged(event)
    event = {"description": "No tag here"}
    assert not is_noproject_tagged(event)
    event = {"description": "#NoProject"}
    assert is_noproject_tagged(event)

def test_is_ignored_attendee_only():
    event = {"attendees": [ {"email": "ignore@x.com"} ]}
    ignored_emails = {"ignore@x.com"}
    self_email = "me@x.com"
    assert is_ignored_attendee_only(event, ignored_emails, self_email)
    event = {"attendees": [ {"email": "ignore@x.com"}, {"email": "me@x.com"} ]}
    assert is_ignored_attendee_only(event, ignored_emails, self_email)
    event = {"attendees": [ {"email": "other@x.com"} ]}
    assert not is_ignored_attendee_only(event, ignored_emails, self_email)

def test_parse_args_with_command_line(monkeypatch):
    """Test parse_args with command-line arguments"""
    # Mock sys.argv to simulate command-line arguments
    monkeypatch.setattr('sys.argv', ['main.py', '--start', '2024-01-01', '--end', '2024-01-02', '--simulate'])
    
    args = parse_args()
    assert args.start == '2024-01-01'
    assert args.end == '2024-01-02'
    assert args.simulate is True
    assert args.purge is False

def test_parse_args_with_dialog(monkeypatch):
    """Test parse_args with dialog (no command-line arguments)"""
    # Mock sys.argv to simulate no command-line arguments
    monkeypatch.setattr('sys.argv', ['main.py'])
    
    # Mock the dialog function to return test parameters
    mock_dialog_result = SimpleNamespace(
        start='2024-01-01',
        end='2024-01-02',
        simulate=True,
        purge=False
    )
    monkeypatch.setattr('main.get_parameters_via_dialog', lambda: mock_dialog_result)
    
    args = parse_args()
    assert args.start == '2024-01-01'
    assert args.end == '2024-01-02'
    assert args.simulate is True
    assert args.purge is False

def test_parse_args_dialog_cancelled(monkeypatch):
    """Test parse_args when dialog is cancelled"""
    # Mock sys.argv to simulate no command-line arguments
    monkeypatch.setattr('sys.argv', ['main.py'])
    
    # Mock the dialog function to return None (cancelled)
    monkeypatch.setattr('main.get_parameters_via_dialog', lambda: None)
    
    # Mock sys.exit to prevent actual exit during testing
    with patch('sys.exit') as mock_exit:
        parse_args()
        mock_exit.assert_called_with(0)

def test_parse_args_invalid_date_format(monkeypatch):
    """Test parse_args with invalid date format"""
    # Mock sys.argv to simulate command-line arguments with invalid date
    monkeypatch.setattr('sys.argv', ['main.py', '--start', 'invalid-date', '--end', '2024-01-02'])
    
    with pytest.raises(ConfigError, match="Start and end dates must be in YYYY-MM-DD format"):
        parse_args()

def test_parse_args_start_after_end(monkeypatch):
    """Test parse_args with start date after end date"""
    # Mock sys.argv to simulate command-line arguments with invalid date range
    monkeypatch.setattr('sys.argv', ['main.py', '--start', '2024-01-02', '--end', '2024-01-01'])
    
    with pytest.raises(ConfigError, match="Start date cannot be after end date"):
        parse_args()

def test_parse_args_date_range_too_large(monkeypatch):
    """Test parse_args with date range exceeding 31 days"""
    # Mock sys.argv to simulate command-line arguments with too large date range
    monkeypatch.setattr('sys.argv', ['main.py', '--start', '2024-01-01', '--end', '2024-03-01'])
    
    with pytest.raises(ConfigError, match="Date range cannot exceed 31 days"):
        parse_args()

def test_process_events_continues_after_api_error():
    clockify = MagicMock()
    clockify.resolve_project_name.return_value = "pid"
    clockify.get_time_entries.side_effect = [Exception("network"), []]
    args = SimpleNamespace(simulate=False)
    events = [
        {
            "summary": "First",
            "description": "",
            "start": {"dateTime": "2024-01-01T10:00:00Z"},
            "end": {"dateTime": "2024-01-01T11:00:00Z"},
            "attendees": [{"email": "a@other.com"}],
            "organizer": {"email": "me@wechange.company"},
        },
        {
            "summary": "Second",
            "description": "",
            "start": {"dateTime": "2024-01-01T11:00:00Z"},
            "end": {"dateTime": "2024-01-01T12:00:00Z"},
            "attendees": [{"email": "a@other.com"}],
            "organizer": {"email": "me@wechange.company"},
        },
    ]
    with patch("main.log_error"):
        process_events(events, clockify, {}, set(), "me@wechange.company", args)
    clockify.create_time_entry.assert_called_once()
    assert clockify.create_time_entry.call_args[0][2] == "Second" 