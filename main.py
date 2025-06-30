import os
import yaml
import argparse
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from calendar_client import CalendarClient
from clockify_client import ClockifyClient
from matcher import match_project

TAG_CALENDAR_BOT = "calendar-bot"

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=str, required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", type=str, required=True, help="End date (YYYY-MM-DD)")
    parser.add_argument("--simulate", action="store_true")
    parser.add_argument("--purge", action="store_true")
    return parser.parse_args()

def load_config():
    load_dotenv()
    with open("rules.yaml", "r") as f:
        rules = yaml.safe_load(f)

    ignored_emails = set()
    self_email = None

    if os.path.exists("ignored_attendees.yaml"):
        with open("ignored_attendees.yaml", "r") as f:
            data = yaml.safe_load(f)
            ignored_emails = set(data.get("ignored_emails", []))
            self_email = data.get("self_email")

    return {
        "GOOGLE_CREDENTIALS_FILE": os.getenv("GOOGLE_CREDENTIALS_FILE"),
        "GOOGLE_CALENDAR_ID": os.getenv("GOOGLE_CALENDAR_ID"),
        "CLOCKIFY_API_KEY": os.getenv("CLOCKIFY_API_KEY"),
        "CLOCKIFY_WORKSPACE_ID": os.getenv("CLOCKIFY_WORKSPACE_ID"),
        "rules": rules,
        "ignored_emails": ignored_emails,
        "self_email": self_email
    }

def is_reclaim_task(event):
    return "reclaim.ai" in event.get("description", "")

def is_all_day(event):
    return "date" in event.get("start", {})

def has_invitees(event):
    return bool(event.get("attendees", []))

def handle_external_organizer(event):
    organizer_email = event.get("organizer", {}).get("email", "")
    attendees = event.get("attendees", [])
    if not organizer_email.endswith("wechange.company"):
        matching_emails = [
            att.get("email") for att in attendees
            if att.get("email") and not att["email"].endswith("wechange.company")
        ]
        if matching_emails:
            event["external_actor_email"] = matching_emails[0]
            return True
        return False
    return True

def log_error(msg, path="unmatched_events.log"):
    print(msg)
    with open(path, "a") as f:
        f.write(msg + "\n")
        
def is_ignored_attendee_only(event, ignored_emails, self_email):
    attendees = event.get("attendees", [])
    actual_attendees = [
        att.get("email", "").lower()
        for att in attendees
        if att.get("email", "").lower() != self_email.lower()
    ]
    return len(actual_attendees) == 1 and actual_attendees[0] in ignored_emails

def process_events(events, clockify, rules, ignored_emails, self_email, args):
    for event in events:
        summary = event.get("summary", "No title")
        if is_reclaim_task(event):
            print(f"Skipping Reclaim task: {summary}")
            continue
        if is_all_day(event):
            print(f"Skipping all-day event: {summary}")
            continue
        if not has_invitees(event):
            print(f"Skipping event without invitees: {summary}")
            continue
        if is_ignored_attendee_only(event, ignored_emails, self_email):
            print(f"Skipping 1-on-1 meeting with ignored attendee")
            continue
        if not handle_external_organizer(event):
            print(f"Skipping external event without valid participant: {summary}")
            continue

        start = event["start"]["dateTime"]
        end = event["end"]["dateTime"]
        project_name = match_project(event, rules)
        project_id = clockify.resolve_project_name(project_name) if project_name else None

        if project_name and not project_id:
            log_error(f"[WARNING] No Clockify project found for name: '{project_name}' — will skip entry.")
            continue

        if args.simulate:
            print(f"[SIMULATION] Would log: {summary} from {start} to {end} -> Proj. ID: {project_id}, Project Name: {project_name}")
        else:
            print(f"Logging: {summary} from {start} to {end} -> Project: {project_id}")
            existing_entries = clockify.get_time_entries(start, end)
            conflict_found = False
            for entry in existing_entries:
                entry_start = entry.get("timeInterval", {}).get("start")
                entry_end = entry.get("timeInterval", {}).get("end")
                entry_project_id = entry.get("projectId")
                if entry_start == start and entry_end == end:
                    if entry_project_id == project_id:
                        print(f"Skipping duplicate entry for {summary} at {start}")
                        conflict_found = True
                        break
                    else:
                        log_error(f"[WARNING] Conflicting time entry exists at {start} for a different project!")
                        conflict_found = True
                        break
            if conflict_found:
                continue
            clockify.create_time_entry(start, end, summary, project_id, tags=[TAG_CALENDAR_BOT])
    


def main():
    args = parse_args()
    config = load_config()
    calendar = CalendarClient(config["GOOGLE_CREDENTIALS_FILE"], config["GOOGLE_CALENDAR_ID"])
    clockify = ClockifyClient(config["CLOCKIFY_API_KEY"], config["CLOCKIFY_WORKSPACE_ID"])

    try:
        start_date = datetime.strptime(args.start, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        end_date = datetime.strptime(args.end, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        print("[ERROR] Start and end dates must be in YYYY-MM-DD format.")
        return

    if start_date > end_date:
        print("[ERROR] Start date cannot be after end date.")
        return

    if (end_date - start_date).days > 31:
        print("[ERROR] Date range cannot exceed 31 days.")
        return

    tag_map = clockify.get_tag_map()
    calendar_bot_tag_id = next((tid for tid, name in tag_map.items() if name == TAG_CALENDAR_BOT), None)

    if args.purge and calendar_bot_tag_id is None:
        print(f"[ERROR] Tag '{TAG_CALENDAR_BOT}' not found in Clockify. Cannot safely purge.")
        return

    current_day = start_date
    while current_day <= end_date:
        print(f"[INFO] Processing date: {current_day.date()}")
        start_range = current_day.replace(hour=0, minute=0, second=0, microsecond=0)
        end_range = current_day.replace(hour=23, minute=59, second=59, microsecond=0)
        events = calendar.get_events_in_range(start_range.isoformat(), end_range.isoformat())

        if args.purge:
            print(f"[INFO] Purging entries tagged '{TAG_CALENDAR_BOT}' on {current_day.date()}")
            entries_to_delete = clockify.get_time_entries(start_range.isoformat(), end_range.isoformat())
            for entry in entries_to_delete:
                tag_ids = entry.get("tagIds", [])
                if calendar_bot_tag_id in tag_ids:
                    entry_id = entry.get("id")
                    desc = entry.get("description", "")
                    print(f"  Deleting entry: {desc}")
                    clockify.delete_time_entry(entry_id)

        process_events(events, clockify, config["rules"], config["ignored_emails"], config["self_email"], args)
        current_day += timedelta(days=1)
        print(f"[INFO] Finished processing date: {current_day.date()}\n")

if __name__ == "__main__":
    main()
# This script is the main entry point for the calendar to Clockify integration.
# It handles command-line arguments, loads configuration, initializes clients, 