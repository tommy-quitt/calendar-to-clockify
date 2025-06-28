from google.oauth2 import service_account
from googleapiclient.discovery import build

class CalendarClient:
    def __init__(self, credentials_path, calendar_id):
        creds = service_account.Credentials.from_service_account_file(
            credentials_path,
            scopes=['https://www.googleapis.com/auth/calendar.readonly']
        )
        self.service = build('calendar', 'v3', credentials=creds)
        self.calendar_id = calendar_id

    def get_events_in_range(self, start_iso, end_iso):
        """
        Fetch events between the specified ISO 8601 start and end times.
        """
        events_result = self.service.events().list(
            calendarId=self.calendar_id,
            timeMin=start_iso,
            timeMax=end_iso,
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        return events_result.get('items', [])
