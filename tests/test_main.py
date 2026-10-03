import pytest
from unittest.mock import MagicMock, patch
from types import SimpleNamespace
from main import (
    is_reclaim_task, is_all_day, has_invitees, handle_external_organizer,
    is_noproject_tagged, is_ignored_attendee_only, parse_args, ConfigError,
    process_events, is_long_duration_event, is_solo_event
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

def test_is_long_duration_event():
    assert is_long_duration_event({
        "start": {"dateTime": "2026-07-22T07:30:00+03:00"},
        "end": {"dateTime": "2026-08-07T08:30:00+03:00"},
    })
    assert is_long_duration_event({
        "start": {"dateTime": "2026-07-23T07:00:00+03:00"},
        "end": {"dateTime": "2026-07-28T08:00:00+03:00"},
    })
    assert not is_long_duration_event({
        "start": {"dateTime": "2026-08-31T11:00:00+03:00"},
        "end": {"dateTime": "2026-08-31T11:30:00+03:00"},
    })
    assert not is_long_duration_event({
        "start": {"dateTime": "2026-08-31T10:00:00Z"},
        "end": {"dateTime": "2026-08-31T18:00:00Z"},
    })
    assert is_long_duration_event({
        "start": {"dateTime": "2026-08-31T10:00:00Z"},
        "end": {"dateTime": "2026-08-31T22:00:01Z"},
    })
    assert not is_long_duration_event({"start": {"date": "2026-07-22"}})

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

def test_is_ignored_attendee_only_multiple_ignored_attendees():
    # Reproduces events like "כושר - נבחרת הנוער" with several attendees that
    # are all on the ignore list: should be skipped, not just when there is
    # exactly one other attendee.
    ignored_emails = {"ignore1@x.com", "ignore2@x.com"}
    self_email = "me@x.com"
    event = {
        "attendees": [
            {"email": "me@x.com"},
            {"email": "ignore1@x.com"},
            {"email": "ignore2@x.com"},
        ]
    }
    assert is_ignored_attendee_only(event, ignored_emails, self_email)

def test_is_ignored_attendee_only_mixed_attendees_not_skipped():
    # If even one other attendee isn't on the ignore list, the event is a
    # real meeting and must not be skipped.
    ignored_emails = {"ignore1@x.com"}
    self_email = "me@x.com"
    event = {
        "attendees": [
            {"email": "me@x.com"},
            {"email": "ignore1@x.com"},
            {"email": "other@x.com"},
        ]
    }
    assert not is_ignored_attendee_only(event, ignored_emails, self_email)

def test_is_ignored_attendee_only_no_other_attendees_not_skipped():
    # Only self on the event: nothing to ignore, so it should not be treated
    # as an ignored-attendee meeting.
    ignored_emails = {"ignore1@x.com"}
    self_email = "me@x.com"
    event = {"attendees": [{"email": "me@x.com"}]}
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

def test_process_events_skips_long_duration_event():
    clockify = MagicMock()
    args = SimpleNamespace(simulate=False)
    events = [
        {
            "summary": "טומי בחול",
            "description": "",
            "start": {"dateTime": "2026-07-22T07:30:00+03:00"},
            "end": {"dateTime": "2026-08-07T08:30:00+03:00"},
            "attendees": [{"email": "naama@wechange.company"}, {"email": "me@wechange.company"}],
            "organizer": {"email": "me@wechange.company"},
        },
    ]
    process_events(events, clockify, {}, set(), "me@wechange.company", args)
    clockify.create_time_entry.assert_not_called()

def test_process_events_customer_filter_skips_other_customers():
    # Only events matching the --customer filter's project name should be
    # logged; events that resolve to a different project are skipped.
    clockify = MagicMock()
    clockify.get_time_entries.return_value = []
    clockify.resolve_project_name.side_effect = lambda name: {
        "Ingenio": "pid-ingenio",
        "8200": "pid-8200",
    }.get(name)
    args = SimpleNamespace(simulate=False, customer="Ingenio")
    rules = {"ingenio.com": "Ingenio", "8200.com": "8200"}
    events = [
        {
            "summary": "Ingenio meeting",
            "description": "",
            "start": {"dateTime": "2024-01-01T10:00:00Z"},
            "end": {"dateTime": "2024-01-01T11:00:00Z"},
            "attendees": [{"email": "a@ingenio.com"}],
            "organizer": {"email": "me@wechange.company"},
        },
        {
            "summary": "8200 meeting",
            "description": "",
            "start": {"dateTime": "2024-01-01T11:00:00Z"},
            "end": {"dateTime": "2024-01-01T12:00:00Z"},
            "attendees": [{"email": "a@8200.com"}],
            "organizer": {"email": "me@wechange.company"},
        },
    ]
    process_events(events, clockify, rules, set(), "me@wechange.company", args)
    clockify.create_time_entry.assert_called_once()
    assert clockify.create_time_entry.call_args[0][2] == "Ingenio meeting"

def test_process_events_customer_filter_skips_unmatched_project():
    # An event that matches no project rule at all must also be skipped
    # when a --customer filter is active (no project name to compare).
    clockify = MagicMock()
    args = SimpleNamespace(simulate=False, customer="Ingenio")
    events = [
        {
            "summary": "No project meeting",
            "description": "",
            "start": {"dateTime": "2024-01-01T10:00:00Z"},
            "end": {"dateTime": "2024-01-01T11:00:00Z"},
            "attendees": [{"email": "a@unknown.com"}],
            "organizer": {"email": "me@wechange.company"},
        },
    ]
    process_events(events, clockify, {}, set(), "me@wechange.company", args)
    clockify.create_time_entry.assert_not_called()

def test_process_events_no_customer_filter_processes_all():
    # Without --customer, behavior is unchanged: all matched events are
    # processed regardless of project.
    clockify = MagicMock()
    clockify.get_time_entries.return_value = []
    clockify.resolve_project_name.return_value = "pid-ingenio"
    args = SimpleNamespace(simulate=False, customer=None)
    rules = {"ingenio.com": "Ingenio"}
    events = [
        {
            "summary": "Ingenio meeting",
            "description": "",
            "start": {"dateTime": "2024-01-01T10:00:00Z"},
            "end": {"dateTime": "2024-01-01T11:00:00Z"},
            "attendees": [{"email": "a@ingenio.com"}],
            "organizer": {"email": "me@wechange.company"},
        },
    ]
    process_events(events, clockify, rules, set(), "me@wechange.company", args)
    clockify.create_time_entry.assert_called_once()

def test_is_solo_event_no_attendees_field():
    assert is_solo_event({}, "me@x.com")

def test_is_solo_event_only_self_attendee():
    event = {"attendees": [{"email": "me@x.com"}]}
    assert is_solo_event(event, "me@x.com")

def test_is_solo_event_false_with_other_attendee():
    event = {"attendees": [{"email": "me@x.com"}, {"email": "other@x.com"}]}
    assert not is_solo_event(event, "me@x.com")

def test_process_events_skips_solo_event_without_project_hint():
    # A self-organized event with no other attendees and no explicit #proj
    # tag is noise (e.g. "נסיעה לאינגיניו" drive-time block) and should be
    # skipped rather than logged with Project Name: None.
    clockify = MagicMock()
    args = SimpleNamespace(simulate=False)
    events = [
        {
            "summary": "נסיעה לאינגיניו",
            "description": "",
            "start": {"dateTime": "2024-01-01T08:00:00+03:00"},
            "end": {"dateTime": "2024-01-01T09:00:00+03:00"},
            "attendees": [{"email": "me@wechange.company", "self": True}],
            "organizer": {"email": "me@wechange.company"},
        },
    ]
    process_events(events, clockify, {}, set(), "me@wechange.company", args)
    clockify.create_time_entry.assert_not_called()

def test_process_events_logs_solo_event_with_explicit_proj_tag():
    # The same kind of solo event, but explicitly tagged #proj, should
    # still be logged against that project (occasional billable solo work).
    clockify = MagicMock()
    clockify.get_time_entries.return_value = []
    clockify.resolve_project_name.return_value = "pid-ingenio"
    args = SimpleNamespace(simulate=False)
    events = [
        {
            "summary": "נסיעה לאינגיניו",
            "description": "#proj Ingenio",
            "start": {"dateTime": "2024-01-01T08:00:00+03:00"},
            "end": {"dateTime": "2024-01-01T09:00:00+03:00"},
            "attendees": [{"email": "me@wechange.company", "self": True}],
            "organizer": {"email": "me@wechange.company"},
        },
    ]
    process_events(events, clockify, {}, set(), "me@wechange.company", args)
    clockify.create_time_entry.assert_called_once()
    assert clockify.create_time_entry.call_args[0][3] == "pid-ingenio"