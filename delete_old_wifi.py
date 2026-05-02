"""
Script to delete old WiFi networks from Windows that haven't been connected to in the last year.

This script:
1. Lists all WiFi profiles stored on Windows
2. Checks the last connection time for each profile
3. Deletes profiles that haven't been connected to in the last year

Requires administrator privileges to delete WiFi profiles.
"""

import subprocess
import re
import argparse
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple


def run_command(command: List[str]) -> Tuple[str, int]:
    """Run a command and return stdout and return code."""
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            shell=True,
            encoding='utf-8',
            errors='ignore'
        )
        return result.stdout, result.returncode
    except Exception as e:
        print(f"Error running command: {e}")
        return "", 1


def get_wifi_profiles() -> List[str]:
    """Get list of all WiFi profile names."""
    output, return_code = run_command(['netsh', 'wlan', 'show', 'profiles'])
    if return_code != 0:
        print("Error: Failed to list WiFi profiles. Make sure you're running as administrator.")
        return []
    
    profiles = []
    # Parse output to extract profile names
    # Format: "All User Profile     : ProfileName"
    pattern = r'All User Profile\s+:\s+(.+)'
    for line in output.split('\n'):
        match = re.search(pattern, line)
        if match:
            profile_name = match.group(1).strip()
            profiles.append(profile_name)
    
    return profiles


def get_last_connection_time(profile_name: str) -> Optional[datetime]:
    """
    Get the last connection time for a WiFi profile using PowerShell.
    Queries Windows Event Logs for WiFi connection events.
    """
    # Escape profile name for PowerShell (replace single quotes with double single quotes)
    escaped_name = profile_name.replace("'", "''")
    
    # PowerShell command to get last WiFi connection time from event logs
    # Event ID 8001 = WLAN connection success
    ps_command = (
        f"$profileName = '{escaped_name}'; "
        "$events = Get-WinEvent -FilterHashtable @{LogName='Microsoft-Windows-WLAN-AutoConfig/Operational'; ID=8001} -ErrorAction SilentlyContinue | "
        "Where-Object { $_.Message -like \"*$profileName*\" } | "
        "Sort-Object TimeCreated -Descending | "
        "Select-Object -First 1 -Property TimeCreated; "
        "if ($events) { $events.TimeCreated.ToString('yyyy-MM-dd HH:mm:ss') }"
    )
    
    # Run PowerShell command
    output, return_code = run_command(['powershell', '-Command', ps_command])
    
    if output.strip():
        try:
            # Try to parse the datetime
            return datetime.strptime(output.strip(), "%Y-%m-%d %H:%M:%S")
        except ValueError:
            pass
    
    # Alternative method: Try to get connection history from registry or profile metadata
    # Check if profile has any connection info in netsh output
    profile_output, _ = run_command(['netsh', 'wlan', 'show', 'profile', 'name=' + profile_name])
    
    # Look for connection-related information in the profile output
    # If we can't find connection history, return None to indicate unknown
    return None


def get_profile_info(profile_name: str) -> Dict[str, str]:
    """Get detailed information about a WiFi profile."""
    output, return_code = run_command(['netsh', 'wlan', 'show', 'profile', 'name=' + profile_name])
    if return_code != 0:
        return {}
    
    info = {}
    for line in output.split('\n'):
        if ':' in line:
            key, value = line.split(':', 1)
            info[key.strip()] = value.strip()
    
    return info


def delete_wifi_profile(profile_name: str, simulate: bool = False) -> bool:
    """Delete a WiFi profile."""
    if simulate:
        print(f"  [SIMULATE] Would delete profile: {profile_name}")
        return True
    
    output, return_code = run_command(['netsh', 'wlan', 'delete', 'profile', 'name=' + profile_name])
    if return_code == 0:
        print(f"  [DELETED] Profile: {profile_name}")
        return True
    else:
        print(f"  [ERROR] Failed to delete profile: {profile_name}")
        print(f"          Output: {output}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Delete WiFi networks that haven\'t been connected to in the last year'
    )
    parser.add_argument(
        '--days',
        type=int,
        default=365,
        help='Number of days since last connection to consider a network "old" (default: 365)'
    )
    parser.add_argument(
        '--simulate',
        action='store_true',
        help='Simulate deletion without actually deleting profiles (RECOMMENDED: Run with this first to preview)'
    )
    parser.add_argument(
        '--force-unknown',
        action='store_true',
        help='Delete profiles with unknown connection history (use with caution)'
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("WiFi Profile Cleanup Script")
    print("=" * 60)
    if args.simulate:
        print("*** SIMULATION MODE ***")
        print("No profiles will actually be deleted. This is a preview.")
        print("=" * 60)
    print(f"Looking for profiles not connected to in the last {args.days} days")
    print()
    
    # Check if running as administrator
    output, return_code = run_command(['netsh', 'wlan', 'show', 'profiles'])
    if return_code != 0:
        print("ERROR: This script requires administrator privileges.")
        print("Please run as administrator to manage WiFi profiles.")
        return
    
    # Get all WiFi profiles
    print("Fetching WiFi profiles...")
    profiles = get_wifi_profiles()
    
    if not profiles:
        print("No WiFi profiles found.")
        return
    
    print(f"Found {len(profiles)} WiFi profile(s)")
    print()
    
    # Calculate cutoff date
    cutoff_date = datetime.now() - timedelta(days=args.days)
    print(f"Cutoff date: {cutoff_date.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Check each profile
    profiles_to_delete = []
    profiles_unknown = []
    profiles_recent = []
    
    for profile_name in profiles:
        print(f"Checking profile: {profile_name}")
        last_connection = get_last_connection_time(profile_name)
        
        if last_connection is None:
            print(f"  [UNKNOWN] Connection history not available")
            profiles_unknown.append(profile_name)
        elif last_connection < cutoff_date:
            days_ago = (datetime.now() - last_connection).days
            print(f"  [OLD] Last connected: {last_connection.strftime('%Y-%m-%d %H:%M:%S')} ({days_ago} days ago)")
            profiles_to_delete.append((profile_name, last_connection))
        else:
            days_ago = (datetime.now() - last_connection).days
            print(f"  [RECENT] Last connected: {last_connection.strftime('%Y-%m-%d %H:%M:%S')} ({days_ago} days ago)")
            profiles_recent.append(profile_name)
        print()
    
    # Summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    if args.simulate:
        print("[SIMULATION MODE - No profiles will actually be deleted]")
        print()
    print(f"Total profiles: {len(profiles)}")
    print(f"Recent profiles (kept): {len(profiles_recent)}")
    if args.simulate:
        print(f"Old profiles (would delete): {len(profiles_to_delete)}")
    else:
        print(f"Old profiles (to delete): {len(profiles_to_delete)}")
    print(f"Unknown history: {len(profiles_unknown)}")
    print()
    
    # Delete old profiles
    if profiles_to_delete:
        if args.simulate:
            print("SIMULATION: Would delete old profiles...")
        else:
            # Ask for confirmation before deleting
            print(f"\n⚠️  WARNING: About to delete {len(profiles_to_delete)} WiFi profile(s)")
            print("Profiles to be deleted:")
            for profile_name, last_connection in profiles_to_delete:
                days_ago = (datetime.now() - last_connection).days
                print(f"  - {profile_name} (last connected {days_ago} days ago)")
            response = input("\nType 'yes' to confirm deletion, or anything else to cancel: ")
            if response.lower() != 'yes':
                print("Deletion cancelled.")
                return
            print("\nDeleting old profiles...")
        deleted_count = 0
        for profile_name, last_connection in profiles_to_delete:
            if delete_wifi_profile(profile_name, simulate=args.simulate):
                deleted_count += 1
        if args.simulate:
            print(f"\n[SIMULATION] Would delete {deleted_count} profile(s)")
        else:
            print(f"\nDeleted {deleted_count} profile(s)")
    
    # Handle unknown profiles
    if profiles_unknown:
        print(f"\nFound {len(profiles_unknown)} profile(s) with unknown connection history:")
        for profile_name in profiles_unknown:
            print(f"  - {profile_name}")
        if args.force_unknown:
            if args.simulate:
                print("\n[SIMULATION] Would delete profiles with unknown history (--force-unknown enabled)...")
            else:
                print("\nDeleting profiles with unknown history (--force-unknown enabled)...")
            deleted_unknown_count = 0
            for profile_name in profiles_unknown:
                if delete_wifi_profile(profile_name, simulate=args.simulate):
                    deleted_unknown_count += 1
            if args.simulate:
                print(f"[SIMULATION] Would delete {deleted_unknown_count} profile(s) with unknown history")
            else:
                print(f"Deleted {deleted_unknown_count} profile(s) with unknown history")
        else:
            print("\nUse --force-unknown to delete these profiles (use with caution)")
    
    print("\nDone!")


if __name__ == "__main__":
    main()

