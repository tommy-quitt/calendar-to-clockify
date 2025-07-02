import re

def match_project(event, rules):
    # Priority 1: Explicit project hint in description
    description = event.get("description", "")
    # This regex looks for "#proj" followed by whitespace and captures everything after it
    # r"#proj\s+(.+)" means:
    #   "#proj" - literal text "#proj"
    #   "\s+" - one or more whitespace characters (spaces, tabs, etc.)
    #   "(.+)" - capture group containing one or more of any character
    match = re.search(r"#proj\s+(.+)", description)
    if match:
        return match.group(1).strip()

    # Priority 2: Rules based on external actor's email
    override_email = event.get("external_actor_email")
    if override_email:
        domain = override_email.split('@')[-1]
        return rules.get(domain)

    # Priority 3: Fallback to attendees’ domains
    participants = [att.get('email', '') for att in event.get('attendees', [])]
    for email in participants:
        domain = email.split('@')[-1]
        if domain in rules:
            return rules[domain]

    # No match → default to None (for projectless entry)
    return None
