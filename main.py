import os
import yaml
import argparse
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from calendar_client import CalendarClient
from clockify_client import ClockifyClient
from matcher import match_project

# CLI arguments
parser = argparse.ArgumentParser()
parser.add_argument("--days-back", type=int, default=0, help="How many days back to look (0=today)")
parser.add_argument("--simulate", action="store_true", help="Run in simulation mode (no Clockify writes)")
args = parser.parse_args()

# Load environment variables
load_dotenv()

GOOGLE_CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE")
GOOGLE_CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID")
CLOCKIFY_API_KEY = os.getenv("CLOCKIFY_API_KEY")
CLOCKIFY_WORKSPACE_ID = os.getenv("CLOCKIFY_WORKSPACE_ID")

# Load project matching rules
with open("rules.yaml", "r") as f:
    rules = yaml.safe_load(f)

# Initialize clients
calendar = CalendarClient(GOOGLE_CREDENTIALS_FILE, GOOGLE_CALENDAR_ID)
clockify = ClockifyClient(CLOCKIFY_API_KEY, CLOCKIFY_WORKSPACE_ID)

# Calculate start and end of target day
now = datetime.now(timezone.utc)
target_day = now - timedelta(days=args.days_back)
start_range = target_day.replace(hour=0, minute=0, second=0, microsecond=0)
end_range = target_day.replace(hour=23, minute=59, second=59, microsecond=0)

events = calendar.get_events_in_range(start_range.isoformat(), end_range.isoformat())
error_log_path = "unmatched_events.log"

with open(error_log_path, "a") as error_log:
    for event in events:
        summary = event.get("summary", "No title")
        description = event.get("description", "")

        # ⛔ Skip Reclaim-created tasks
        if "reclaim.ai" in description:
            print(f"Skipping Reclaim task: {summary}")
            continue

        # ⛔ Skip all-day events
        if "date" in event.get("start", {}):
            print(f"Skipping all-day event: {summary}")
            continue

        # ⛔ Skip events with no invitees
        attendees = event.get("attendees", [])
        if not attendees:
            print(f"Skipping event without invitees: {summary}")
            continue

        # Handle external organizer
        organizer_email = event.get("organizer", {}).get("email", "")
        if not organizer_email.endswith("wechange.company"):
            matching_emails = [
                att.get("email") for att in attendees
                if att.get("email") and not att["email"].endswith("wechange.company")
            ]
            if matching_emails:
                event["external_actor_email"] = matching_emails[0]
            else:
                print(f"Skipping external event without valid participant: {summary}")
                continue

        start = event["start"]["dateTime"]
        end = event["end"]["dateTime"]
        project_id = match_project(event, rules)

        if not project_id:
            warning = f"[WARNING] No matching rule for: '{summary}' at {start}"
            print(warning)
            error_log.write(warning + "\n")
            continue

        if args.simulate:
            print(f"[SIMULATION] Would log: {summary} from {start} to {end} -> Project: {project_id}")
        else:
            print(f"Logging: {summary} from {start} to {end} -> Project: {project_id}")
            clockify.create_time_entry(start, end, summary, project_id)
