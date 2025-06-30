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
- **Configurable Ignored Attendees:** Skips events with only ignored attendees.
- **All-day and External Event Filtering:** Skips all-day events and can filter based on organizer/attendee domains.
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
python main.py --start YYYY-MM-DD --end YYYY-MM-DD [--simulate] [--purge]
```

### Parameters

- `--start`: Start date (inclusive) in `YYYY-MM-DD` format (required)
- `--end`: End date (inclusive) in `YYYY-MM-DD` format (required)
- `--simulate`: (Optional) If set, the script will only print what would be logged, without making any changes to Clockify.
- `--purge`: (Optional) If set, the script will delete all Clockify entries created by the bot (tagged with `calendar-bot`) in the specified date range.

### Example

Simulate logging for June 2025:
```sh
python main.py --start 2025-06-01 --end 2025-06-30 --simulate
```

Purge all bot-created entries for a single day:
```sh
python main.py --start 2025-06-30 --end 2025-06-30 --purge
```

## Configuration Files

- `rules.yaml`: Maps event summaries or other criteria to Clockify project names.
- `ignored_attendees.yaml`: (Optional) Lists emails to ignore for 1-on-1 meetings and your own email.

Example `ignored_attendees.yaml`:
```yaml
ignored_emails:
  - someone@example.com
self_email: your.email@domain.com
```

## Notes

- The script will not log all-day events or events without invitees.
- Events with the `#noproject` tag in their description are skipped.
- Only events with valid project matches are logged.
- Purge mode only deletes entries tagged with `calendar-bot` to avoid accidental data loss.

## Logging

Warnings and unmatched events are appended to `unmatched_events.log`.

## License

See [LICENSE](LICENSE) for details.