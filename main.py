import os
import yaml
import argparse
import sys
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkcalendar import DateEntry
from types import SimpleNamespace
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from calendar_client import CalendarClient
from clockify_client import ClockifyClient
from matcher import match_project
from ui_dialog import get_parameters_via_dialog

TAG_CALENDAR_BOT = "calendar-bot"
MAX_EVENT_DURATION_HOURS = 10

class ConfigError(Exception):
    pass

def parse_args():
    import argparse
    from datetime import datetime, timezone
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=str, required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", type=str, required=True, help="End date (YYYY-MM-DD)")
    parser.add_argument("--simulate", action="store_true")
    parser.add_argument("--purge", action="store_true")
    # Only show dialog if no parameters are provided (other than script name)
    if len(sys.argv) == 1:
        args = get_parameters_via_dialog()
        if args is None:
            print("[INFO] User cancelled parameter input dialog.")
            sys.exit(0)
        return args
    else:
        args = parser.parse_args()
        # Validate date format and logic
        try:
            start_date = datetime.strptime(args.start, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            end_date = datetime.strptime(args.end, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            raise ConfigError("[ERROR] Start and end dates must be in YYYY-MM-DD format.")
        if start_date > end_date:
            raise ConfigError("[ERROR] Start date cannot be after end date.")
        if (end_date - start_date).days > 31:
            raise ConfigError("[ERROR] Date range cannot exceed 31 days.")
        return args

def load_config():
    # Limitation: rules.yaml, ignored_attendees.yaml, .env, credentials, and
    # unmatched_events.log are resolved relative to the process current working
    # directory, not this file's location. Running from another folder (Task
    # Scheduler, PyInstaller, IDE) can miss config or write logs elsewhere.
    load_dotenv()
    # Validate rules.yaml
    if not os.path.exists("rules.yaml"):
        raise ConfigError("[ERROR] rules.yaml file is missing. Please provide a rules.yaml file.")
    try:
        with open("rules.yaml", "r") as f:
            rules = yaml.safe_load(f)
    except Exception as e:
        raise ConfigError(f"[ERROR] Failed to load rules.yaml: {e}")
    if not rules or not isinstance(rules, dict):
        raise ConfigError("[ERROR] rules.yaml is empty or not a valid mapping. Please check its contents.")

    ignored_emails = set()
    self_email = None
    if os.path.exists("ignored_attendees.yaml"):
        try:
            with open("ignored_attendees.yaml", "r") as f:
                data = yaml.safe_load(f)
        except Exception as e:
            raise ConfigError(f"[ERROR] Failed to load ignored_attendees.yaml: {e}")
        if not isinstance(data, dict):
            raise ConfigError("[ERROR] ignored_attendees.yaml must be a mapping with 'ignored_emails' and 'self_email'.")
        raw_ignored_emails = data.get("ignored_emails", [])
        self_email = data.get("self_email")
        if not isinstance(raw_ignored_emails, list) or not all(isinstance(e, str) for e in raw_ignored_emails):
            raise ConfigError("[ERROR] 'ignored_emails' in ignored_attendees.yaml must be a list of strings.")
        ignored_emails = {e.lower() for e in raw_ignored_emails}
        if self_email is not None and not isinstance(self_email, str):
            raise ConfigError("[ERROR] 'self_email' in ignored_attendees.yaml must be a string.")
        if self_email is not None:
            self_email = self_email.lower()

    # Validate environment variables
    env_vars = [
        ("GOOGLE_CREDENTIALS_FILE", "Path to Google service account credentials JSON file (set GOOGLE_CREDENTIALS_FILE)", True),
        ("GOOGLE_CALENDAR_ID", "Google Calendar ID (set GOOGLE_CALENDAR_ID)", True),
        ("CLOCKIFY_API_KEY", "Clockify API key (set CLOCKIFY_API_KEY)", True),
        ("CLOCKIFY_WORKSPACE_ID", "Clockify workspace ID (set CLOCKIFY_WORKSPACE_ID)", True)
    ]
    config = {}
    for var, hint, required in env_vars:
        value = os.getenv(var)
        if required and not value:
            raise ConfigError(f"[ERROR] Missing environment variable: {var}. Hint: {hint}")
        config[var] = value
    # Check credentials file exists
    if not os.path.exists(config["GOOGLE_CREDENTIALS_FILE"]):
        raise ConfigError(f"[ERROR] GOOGLE_CREDENTIALS_FILE '{config['GOOGLE_CREDENTIALS_FILE']}' does not exist.")

    config.update({
        "rules": rules,
        "ignored_emails": ignored_emails,
        "self_email": self_email
    })
    return config

def is_reclaim_task(event):
    return "reclaim.ai" in event.get("description", "")

def is_all_day(event):
    return "date" in event.get("start", {})

def _parse_event_datetime(value):
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))

def is_long_duration_event(event, max_hours=MAX_EVENT_DURATION_HOURS):
    """True for timed events longer than max_hours (away/OOO-style blocks)."""
    try:
        start = _parse_event_datetime(event.get("start", {}).get("dateTime"))
        end = _parse_event_datetime(event.get("end", {}).get("dateTime"))
    except ValueError:
        return False
    if start is None or end is None:
        return False
    return (end - start) > timedelta(hours=max_hours)

def has_invitees(event):
    return bool(event.get("attendees", []))

def is_resource_calendar_email(email):
    return email.lower().endswith("@resource.calendar.google.com")

def handle_external_organizer(event):
    """
    Handles calendar events organized by external (non-wechange.company) attendees.
    
    How it works:
    - If the organizer's email does NOT end with "wechange.company", this is an external event
    - In that case, finds the first attendee who does NOT have a wechange.company email
      and is not a Google Calendar room/resource
    - If none remain, falls back to the organizer's email
    - Sets that email as the "external_actor_email" in the event dictionary
    - Returns True if the event should be processed, False if it should be skipped
    Limitation: when several external attendees exist, Google Calendar attendee
    order is arbitrary, so the first non-wechange / non-room address wins.
    
    Returns:
        bool: True if event should be processed, False if it should be skipped
    """
    organizer_email = event.get("organizer", {}).get("email", "")
    attendees = event.get("attendees", [])
    if not organizer_email.endswith("wechange.company"):
        matching_emails = [
            att.get("email") for att in attendees
            if att.get("email")
            and not att["email"].endswith("wechange.company")
            and not is_resource_calendar_email(att["email"])
        ]
        if matching_emails:
            event["external_actor_email"] = matching_emails[0]
            return True
        if organizer_email and not is_resource_calendar_email(organizer_email):
            event["external_actor_email"] = organizer_email
            return True
        return False
    return True

def is_noproject_tagged(event):
    description = event.get("description", "")
    return "#noproject" in description.lower()

def log_error(msg, path="unmatched_events.log"):
    print(msg)
    with open(path, "a") as f:
        f.write(msg + "\n")
        
def is_ignored_attendee_only(event, ignored_emails, self_email):
    if not self_email:
        return False

    attendees = event.get("attendees", [])
    actual_attendees = [
        att.get("email", "").lower()
        for att in attendees
        if att.get("email", "").lower() != self_email
    ]
    return len(actual_attendees) == 1 and actual_attendees[0] in ignored_emails

def process_events(events, clockify, rules, ignored_emails, self_email, args):
    for event in events:
        summary = event.get("summary", "No title")
        # Limitation: cancelled Google Calendar events (status == "cancelled")
        # are not filtered and may still be logged as time entries.
        if is_reclaim_task(event):
            print(f"Skipping Reclaim task: {summary}")
            continue
        if is_all_day(event):
            print(f"Skipping all-day event: {summary}")
            continue
        if is_long_duration_event(event):
            print(f"Skipping long event (>{MAX_EVENT_DURATION_HOURS}h, away/OOO-style): {summary}")
            continue
        if is_noproject_tagged(event):
            print(f"Skipping event due to '#noproject' tag in description: {summary}")
            continue
        if not has_invitees(event):
            print(f"Skipping event without invitees: {summary}")
            continue
        if is_ignored_attendee_only(event, ignored_emails, self_email):
            print(f"Skipping 1-on-1 meeting with ignored attendee: {summary}")
            continue
        if not handle_external_organizer(event):
            print(f"Skipping external event without valid participant: {summary}")
            continue

        # Only process if organizer or accepted attendee
        organizer_email = event.get("organizer", {}).get("email", "").lower()
        if self_email:
            if organizer_email != self_email.lower():
                attendees = event.get("attendees", [])
                found = False
                for att in attendees:
                    if att.get("email", "").lower() == self_email.lower():
                        if att.get("responseStatus") == "accepted":
                            found = True
                        break
                if not found:
                    print(f"Skipping event not accepted by self: {summary}")
                    continue

        try:
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
                # Limitation: duplicate/conflict detection compares ISO datetime
                # strings exactly. Clockify may store the same instant as UTC
                # (Z) while Google Calendar uses an offset (+03:00), so a true
                # duplicate can be missed and a second entry created.
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
        except Exception as e:
            log_error(f"[ERROR] Failed to process event '{summary}': {e}")
            continue
    


def main():
    try:
        args = parse_args()
        config = load_config()
    except ConfigError as e:
        print(e)
        return
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

    try:
        tag_map = clockify.get_tag_map()
    except Exception as e:
        print(f"[ERROR] Failed to fetch Clockify tags: {e}")
        return
    calendar_bot_tag_id = next((tid for tid, name in tag_map.items() if name == TAG_CALENDAR_BOT), None)

    if args.purge and calendar_bot_tag_id is None:
        print(f"[ERROR] Tag '{TAG_CALENDAR_BOT}' not found in Clockify. Cannot safely purge.")
        return

    current_day = start_date
    while current_day <= end_date:
        print(f"[INFO] Processing date: {current_day.date()}")
        # Limitation: --start/--end are treated as UTC midnight–23:59:59, not
        # the user's local calendar day. For UTC+3, events before ~03:00 local
        # can be missed on that date, and late-evening events can land on the
        # wrong processing day (logging and purge both use these bounds).
        start_range = current_day.replace(hour=0, minute=0, second=0, microsecond=0)
        end_range = current_day.replace(hour=23, minute=59, second=59, microsecond=0)
        try:
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
            print(f"[INFO] Finished processing date: {current_day.date()}\n")
        except Exception as e:
            print(f"[ERROR] Failed processing date {current_day.date()}: {e}. Continuing with the next day.")
        current_day += timedelta(days=1)
        

if __name__ == "__main__":
    main()
# This script is the main entry point for the calendar to Clockify integration.
# It handles command-line arguments, loads configuration, initializes clients, 