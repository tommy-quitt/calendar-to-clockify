# Calendar to Clockify

This tool synchronizes events from a Google Calendar to Clockify as time entries, with advanced filtering, project matching, and robust duplicate/conflict handling. It is designed for automation and can be run in simulation or purge mode.

## Features

- **Google Calendar Integration:** Fetches events from a specified Google Calendar.
- **Clockify Integration:** Creates time entries in Clockify, matching events to projects.
- **Project Matching:** Uses rules to map calendar events to Clockify projects.
- **Tagging:** All entries created by the bot are tagged with `calendar-bot`.
- **Duplicate/Conflict Handling:** Skips duplicate entries and warns about conflicting entries for the same time but different projects.
- **Simulation Mode:** Preview what would be logged without making changes.
- **Purge Mode:** Delete all Clockify entries created by the bot within a date range.
- **Customer Filter:** Restrict logging (and purging) to a single customer/project with `--customer`.
- **Configurable Ignored Attendees:** Skips events where every attendee other than you is on the ignore list — not just strict 1-on-1s.
- **Solo Event Filtering:** Skips self-organized events with no other attendees and no project match (e.g. personal reminders), unless explicitly tagged with `#proj <ProjectName>`.
- **Long-Duration Event Filtering:** Skips away/OOO-style events longer than 10 hours.
- **All-day and External Event Filtering:** Skips all-day events and can filter based on organizer/attendee domains.
- **UI Date Defaults:** The Tk parameter dialog defaults its date range to a full month — the previous month during the first week of a new month, otherwise the current month to date.
- **Logging:** Warnings and unmatched events are logged to `unmatched_events.log`.

## Requirements

- Python 3.7+
- Google Calendar API credentials
- Clockify API key
- Required Python packages (see `requirements.txt`)

## Installation

1. Clone the repository.
2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
3. Set up your `.env` file or environment variables for:
   - `GOOGLE_CREDENTIALS_FILE`
   - `GOOGLE_CALENDAR_ID`
   - `CLOCKIFY_API_KEY`
   - `CLOCKIFY_WORKSPACE_ID`

4. Prepare your `rules.yaml` for project matching and (optionally) `ignored_attendees.yaml` for ignored emails.

## Usage

Run the script from the command line:

```sh
python main.py --start YYYY-MM-DD --end YYYY-MM-DD [--simulate] [--purge] [--customer NAME]
```

Running with no arguments opens a Tk dialog to pick the parameters instead (it defaults the date range to a full month, as described above).

### Parameters

- `--start`: Start date (inclusive) in `YYYY-MM-DD` format (required)
- `--end`: End date (inclusive) in `YYYY-MM-DD` format (required)
- `--simulate`: (Optional) If set, the script will only print what would be logged, without making any changes to Clockify.
- `--purge`: (Optional) If set, the script will delete all Clockify entries created by the bot (tagged with `calendar-bot`) in the specified date range.
- `--customer`: (Optional) Restrict processing to events matching this project/customer name (as resolved from `rules.yaml`). Combined with `--purge`, only that customer's bot-created entries are deleted; if the customer name doesn't resolve to a Clockify project, the purge is aborted rather than deleting everything.

### Example

Simulate logging for June 2025:
```sh
python main.py --start 2025-06-01 --end 2025-06-30 --simulate
```

Purge all bot-created entries for a single day:
```sh
python main.py --start 2025-06-30 --end 2025-06-30 --purge
```

Simulate logging for a single customer only:
```sh
python main.py --start 2025-06-01 --end 2025-06-30 --simulate --customer Ingenio
```

## Configuration Files

- `rules.yaml`: Maps event summaries or other criteria to Clockify project names.
- `ignored_attendees.yaml`: (Optional) Lists emails to ignore when every other attendee on the event is on the list, plus your own email.

Example `ignored_attendees.yaml`:
```yaml
ignored_emails:
  - someone@example.com
self_email: your.email@domain.com
```

## Notes

- The script will not log all-day events, events without invitees, or away/OOO-style events longer than 10 hours.
- Events with the `#noproject` tag in their description are skipped.
- An event is skipped if every attendee other than you is on the ignore list (not just strict 1-on-1s).
- Self-organized events with no other attendees are skipped unless they resolve to a project — either via attendee domain or an explicit `#proj <ProjectName>` tag in the description, which takes priority over all other project-matching rules.
- Only events with valid project matches are logged.
- Purge mode only deletes entries tagged with `calendar-bot` to avoid accidental data loss.

## Logging

Warnings and unmatched events are appended to `unmatched_events.log`.

## License

See [LICENSE](LICENSE) for details.
