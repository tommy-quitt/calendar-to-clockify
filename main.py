import os
from dotenv import load_dotenv
from calendar_client import CalendarClient
from clockify_client import ClockifyClient
from matcher import match_project
import yaml

load_dotenv()

GOOGLE_CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE")
GOOGLE_CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID")
CLOCKIFY_API_KEY = os.getenv("CLOCKIFY_API_KEY")
CLOCKIFY_WORKSPACE_ID = os.getenv("CLOCKIFY_WORKSPACE_ID")

with open("rules.yaml", "r") as f:
    rules = yaml.safe_load(f)

calendar = CalendarClient(GOOGLE_CREDENTIALS_FILE, GOOGLE_CALENDAR_ID)
clockify = ClockifyClient(CLOCKIFY_API_KEY, CLOCKIFY_WORKSPACE_ID)

events = calendar.get_today_events()

for event in events:
    start = event["start"]["dateTime"]
    end = event["end"]["dateTime"]
    description = event.get("summary", "No title")
    project_id = match_project(event, rules)
    print(f"Logging: {description} from {start} to {end} -> Project: {project_id}")
    clockify.create_time_entry(start, end, description, project_id)
