import os
import yaml
from dotenv import load_dotenv
from calendar_client import CalendarClient
from clockify_client import ClockifyClient
from matcher import match_project

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

events = calendar.get_today_events()
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

        # ⛔ Skip events you did not organize unless you can find a matching participant
        organizer_email = event.get("organizer", {}).get("email", "")
        if not organizer_email.endswith("wechange.company"):
            # Find first participant not from wechange.company
            matching_emails = [
                att.get("email") for att in attendees
                if att.get("email") and not att["email"].endswith("wechange.company")
            ]
            if matching_emails:
                event["external_actor_email"] = matching_emails[0]
            else:
                print(f"Skipping external event without valid participant: {summary}")
                continue

        # Extract time details
        start = event["start"]["dateTime"]
        end = event["end"]["dateTime"]

        # Determine matching rule using override email if present
        project_id = match_project(event, rules)

        if not project_id:
            warning = f"[WARNING] No matching rule for: '{summary}' at {start}"
            print(warning)
            error_log.write(warning + "\n")
            continue

        print(f"Logging: {summary} from {start} to {end} -> Project: {project_id}")
        clockify.create_time_entry(start, end, summary, project_id)
