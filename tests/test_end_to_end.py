import pytest
from unittest.mock import patch, MagicMock
from types import SimpleNamespace
import main

def test_end_to_end(monkeypatch):
    # Mock command-line arguments
    monkeypatch.setattr(main, 'parse_args', lambda: SimpleNamespace(
        start='2024-01-01',
        end='2024-01-01',
        simulate=True,
        purge=False
    ))

    # Mock config loading
    monkeypatch.setattr(main, 'load_config', lambda: {
        'GOOGLE_CREDENTIALS_FILE': 'fake.json',
        'GOOGLE_CALENDAR_ID': 'calid',
        'CLOCKIFY_API_KEY': 'apikey',
        'CLOCKIFY_WORKSPACE_ID': 'wsid',
        'rules': {},
        'ignored_emails': set(),
        'self_email': 'me@domain.com'
    })

    # Mock CalendarClient
    fake_event = {
        'summary': 'Test Meeting',
        'description': '',
        'start': {'dateTime': '2024-01-01T10:00:00Z'},
        'end': {'dateTime': '2024-01-01T11:00:00Z'},
        'attendees': [{'email': 'me@domain.com', 'responseStatus': 'accepted'}],
        'organizer': {'email': 'someoneelse@domain.com'}
    }
    with patch('main.CalendarClient') as MockCal, \
         patch('main.ClockifyClient') as MockClock, \
         patch('main.match_project', return_value=None):
        mock_cal = MockCal.return_value
        mock_cal.get_events_in_range.return_value = [fake_event]
        mock_clock = MockClock.return_value
        mock_clock.get_tag_map.return_value = {'1': 'calendar-bot'}
        mock_clock.get_time_entries.return_value = []
        mock_clock.resolve_project_name.return_value = 'pid'
        mock_clock.create_time_entry.return_value = {'id': 'tid'}
        # Run main
        main.main()
        # Check that get_events_in_range and create_time_entry were called
        mock_cal.get_events_in_range.assert_called()
        # In simulate mode, create_time_entry should not be called
        assert not mock_clock.create_time_entry.called or mock_clock.create_time_entry.call_count == 0

def test_dialog_functionality(monkeypatch):
    """Test that the dialog is called when no command-line arguments are provided"""
    # Mock sys.argv to simulate no command-line arguments
    monkeypatch.setattr('sys.argv', ['main.py'])
    
    # Mock the dialog function to return test parameters
    mock_dialog_result = SimpleNamespace(
        start='2024-01-01',
        end='2024-01-01',
        simulate=True,
        purge=False
    )
    monkeypatch.setattr('main.get_parameters_via_dialog', lambda: mock_dialog_result)
    
    # Mock config loading
    monkeypatch.setattr(main, 'load_config', lambda: {
        'GOOGLE_CREDENTIALS_FILE': 'fake.json',
        'GOOGLE_CALENDAR_ID': 'calid',
        'CLOCKIFY_API_KEY': 'apikey',
        'CLOCKIFY_WORKSPACE_ID': 'wsid',
        'rules': {},
        'ignored_emails': set(),
        'self_email': 'me@domain.com'
    })

    # Mock CalendarClient
    fake_event = {
        'summary': 'Test Meeting',
        'description': '',
        'start': {'dateTime': '2024-01-01T10:00:00Z'},
        'end': {'dateTime': '2024-01-01T11:00:00Z'},
        'attendees': [{'email': 'me@domain.com', 'responseStatus': 'accepted'}],
        'organizer': {'email': 'someoneelse@domain.com'}
    }
    with patch('main.CalendarClient') as MockCal, \
         patch('main.ClockifyClient') as MockClock, \
         patch('main.match_project', return_value=None):
        mock_cal = MockCal.return_value
        mock_cal.get_events_in_range.return_value = [fake_event]
        mock_clock = MockClock.return_value
        mock_clock.get_tag_map.return_value = {'1': 'calendar-bot'}
        mock_clock.get_time_entries.return_value = []
        mock_clock.resolve_project_name.return_value = 'pid'
        mock_clock.create_time_entry.return_value = {'id': 'tid'}
        # Run main
        main.main()
        # Check that get_events_in_range and create_time_entry were called
        mock_cal.get_events_in_range.assert_called()
        # In simulate mode, create_time_entry should not be called
        assert not mock_clock.create_time_entry.called or mock_clock.create_time_entry.call_count == 0

def test_dialog_cancellation(monkeypatch):
    """Test that the script exits gracefully when dialog is cancelled"""
    # Mock sys.argv to simulate no command-line arguments
    monkeypatch.setattr('sys.argv', ['main.py'])
    
    # Mock the dialog function to return None (cancelled)
    monkeypatch.setattr('main.get_parameters_via_dialog', lambda: None)
    
    # Mock sys.exit to prevent actual exit during testing
    with patch('sys.exit') as mock_exit:
        main.parse_args()
        mock_exit.assert_called_with(0)

def test_main_continues_after_day_api_error(monkeypatch):
    monkeypatch.setattr(main, 'parse_args', lambda: SimpleNamespace(
        start='2024-01-01',
        end='2024-01-02',
        simulate=True,
        purge=False
    ))
    monkeypatch.setattr(main, 'load_config', lambda: {
        'GOOGLE_CREDENTIALS_FILE': 'fake.json',
        'GOOGLE_CALENDAR_ID': 'calid',
        'CLOCKIFY_API_KEY': 'apikey',
        'CLOCKIFY_WORKSPACE_ID': 'wsid',
        'rules': {},
        'ignored_emails': set(),
        'self_email': 'me@domain.com'
    })
    with patch('main.CalendarClient') as MockCal, \
         patch('main.ClockifyClient') as MockClock:
        mock_cal = MockCal.return_value
        mock_cal.get_events_in_range.side_effect = [Exception("calendar down"), []]
        mock_clock = MockClock.return_value
        mock_clock.get_tag_map.return_value = {'1': 'calendar-bot'}
        main.main()
        assert mock_cal.get_events_in_range.call_count == 2 