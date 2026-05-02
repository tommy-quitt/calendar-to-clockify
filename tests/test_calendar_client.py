import pytest
from unittest.mock import patch, MagicMock
from calendar_client import CalendarClient

def test_get_events_in_range():
    with patch('calendar_client.service_account.Credentials.from_service_account_file') as mock_creds, \
         patch('calendar_client.build') as mock_build:
        mock_service = MagicMock()
        mock_events = MagicMock()
        mock_events.list.return_value.execute.return_value = {'items': [ {'id': '1'}, {'id': '2'} ]}
        mock_service.events.return_value = mock_events
        mock_build.return_value = mock_service
        client = CalendarClient('fake_path.json', 'cal_id')
        events = client.get_events_in_range('2024-01-01T00:00:00Z', '2024-01-01T23:59:59Z')
        assert events == [{'id': '1'}, {'id': '2'}] 