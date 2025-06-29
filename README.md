# Calendar to Clockify

This Python tool syncs your Google Calendar events to Clockify as time entries, using project-matching logic based on event participants and custom rules.

## Features
- Syncs Google Calendar events to Clockify as time entries.
- Matches events to Clockify projects using rules defined in `rules.yaml`.
- Skips all-day events, events without invitees, and Reclaim tasks.
- Optionally purges (deletes) previously created Clockify entries tagged as `calendar-bot`.
- Supports simulation mode (dry run).

## Requirements
- Python 3.8+
- Google Calendar API credentials (see `credentials.json`)
- Clockify API key
- `rules.yaml` for project matching
- `requirements.txt` dependencies

## Usage

Run the script from the command line:

```sh
python main.py --start YYYY-MM-DD --end YYYY-MM-DD [--simulate] [--purge]
```

### Parameters
- `--start` (required): Start date in `YYYY-MM-DD` format.
- `--end` (required): End date in `YYYY-MM-DD` format.
- `--simulate`: If set, the script will only print what would be logged, without creating or deleting any entries.
- `--purge`: If set, the script will delete all Clockify entries tagged as `calendar-bot` for each day in the range before syncing new events.

### Example

```sh
python main.py --start 2025-06-01 --end 2025-06-07 --purge
```

This will sync events from June 1 to June 7, 2025, and purge all previously created `calendar-bot` entries for each day before syncing.

## Configuration
- Set up your Google Calendar API credentials and place the file path in your environment variables.
- Set your Clockify API key and workspace ID in your environment variables.
- Define your project matching rules in `rules.yaml`.

## Notes
- The script will not sync events longer than 31 days at a time.
- Only events with invitees and not marked as all-day or Reclaim tasks are considered.
- Purge only deletes entries with the `calendar-bot` tag.

---

For more details, see the code and comments in `main.py`.