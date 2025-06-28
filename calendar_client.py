from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime

class CalendarClient:
    def __init__(self, credentials_path, calendar_id):
        creds = service_account.Credentials.from_service_account_file(
            credentials_path, scopes=['https://www.googleapis.com/auth/calendar.readonly'])
        self.service = build('calendar', 'v3', credentials=creds)
        self.calendar_id = calendar_id

    def get_today_events(self):
        now = datetime.utcnow()
        start = now.replace(hour=0, minute=0, second=0).isoformat() + 'Z'
        end = now.replace(hour=23, minute=59, second=59).isoformat() + 'Z'
        events_result = self.service.events().list(
            calendarId=self.calendar_id, timeMin=start, timeMax=end, singleEvents=True, orderBy='startTime').execute()
        return events_result.get('items', [])
