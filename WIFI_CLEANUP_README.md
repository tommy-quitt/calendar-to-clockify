# WiFi Profile Cleanup Script

A Python script to automatically delete old WiFi networks from Windows that haven't been connected to in the last year (or custom time period).

## Features

- Lists all WiFi profiles stored on Windows
- Checks last connection time for each profile using Windows Event Logs
- Deletes profiles that haven't been connected to within the specified time period
- Simulation mode to preview what would be deleted
- Handles profiles with unknown connection history

## Requirements

- Windows 10/11
- Python 3.7+
- Administrator privileges (required to delete WiFi profiles)

## Usage

### ⚠️ IMPORTANT: Always Run in Simulation Mode First!

**Always run in simulation mode first** to preview what will be deleted:

```bash
python delete_old_wifi.py --simulate
```

This will show you all profiles that would be deleted **without actually deleting them**. The output clearly shows:
- Which profiles would be deleted
- When they were last connected
- A summary of what actions would be taken

### Delete Old Profiles (Default: 365 days)

After reviewing the simulation results, you can run the script for real:

```bash
python delete_old_wifi.py
```

**Note:** 
- This requires administrator privileges. Right-click PowerShell/Command Prompt and select "Run as administrator", then navigate to the script directory.
- The script will ask for confirmation before deleting profiles (type 'yes' to confirm)

### Custom Time Period

Delete profiles not connected to in the last 180 days:

```bash
python delete_old_wifi.py --days 180
```

### Delete Profiles with Unknown History

Some profiles may not have connection history available. To delete these as well (use with caution):

```bash
python delete_old_wifi.py --force-unknown
```

### Combine Options

```bash
python delete_old_wifi.py --days 180 --simulate --force-unknown
```

## Command Line Arguments

- `--days N`: Number of days since last connection to consider a network "old" (default: 365)
- `--simulate`: Run in simulation mode - shows what would be deleted without actually deleting
- `--force-unknown`: Delete profiles with unknown connection history (use with caution)

## How It Works

1. The script uses `netsh wlan show profiles` to list all WiFi profiles
2. For each profile, it queries Windows Event Logs (Microsoft-Windows-WLAN-AutoConfig/Operational) to find the last connection time
3. Profiles with last connection older than the specified threshold are deleted
4. Profiles with unknown connection history are reported separately (not deleted unless `--force-unknown` is used)

## Important Notes

- **⚠️ ALWAYS run in simulation mode first** (`--simulate`) to review what will be deleted
- **Requires administrator privileges** to delete WiFi profiles
- When not in simulation mode, the script will ask for confirmation before deleting
- Profiles with unknown connection history are not deleted by default (use `--force-unknown` with caution)
- The script uses Windows Event Logs, which may not have complete history for very old connections
- Deleted profiles can be re-added by connecting to the network again

## Example Output (Simulation Mode)

```
============================================================
WiFi Profile Cleanup Script
============================================================
*** SIMULATION MODE ***
No profiles will actually be deleted. This is a preview.
============================================================
Looking for profiles not connected to in the last 365 days

Fetching WiFi profiles...
Found 15 WiFi profile(s)

Cutoff date: 2023-12-01 10:30:45

Checking profile: OldCoffeeShop
  [OLD] Last connected: 2022-05-15 14:22:10 (567 days ago)

Checking profile: HomeNetwork
  [RECENT] Last connected: 2024-11-20 08:15:30 (15 days ago)

...

============================================================
SUMMARY
============================================================
[SIMULATION MODE - No profiles will actually be deleted]

Total profiles: 15
Recent profiles (kept): 8
Old profiles (would delete): 5
Unknown history: 2

SIMULATION: Would delete old profiles...
  [SIMULATE] Would delete profile: OldCoffeeShop
  [SIMULATE] Would delete profile: OldAirportWiFi
  ...

[SIMULATION] Would delete 5 profile(s)
```

## Troubleshooting

### "This script requires administrator privileges"

Run PowerShell or Command Prompt as administrator:
1. Right-click PowerShell/Command Prompt
2. Select "Run as administrator"
3. Navigate to the script directory
4. Run the script

### No connection history found

Some profiles may not have connection history in Windows Event Logs. This can happen if:
- The profile was created but never connected to
- Event logs were cleared
- The profile is very old

Use `--force-unknown` with caution to delete these profiles.

### Script can't find profiles

Make sure you're running on Windows and that WiFi is enabled. The script uses Windows `netsh` commands which are only available on Windows systems.

