import re

# Compiled once at import time rather than on every match_project() call.
# IGNORECASE keeps this consistent with is_noproject_tagged()'s
# case-insensitive "#noproject" check elsewhere in the pipeline.
_PROJ_TAG_RE = re.compile(r"#proj\s+(.+)", re.IGNORECASE)

def match_project(event, rules):
    # Priority 1: Explicit project hint in description
    # This regex looks for "#proj" followed by whitespace and captures everything after it
    # r"#proj\s+(.+)" means:
    #   "#proj" - literal text "#proj" (case-insensitive)
    #   "\s+" - one or more whitespace characters (spaces, tabs, etc.)
    #   "(.+)" - capture group containing one or more of any character
    description = event.get("description", "")
    match = _PROJ_TAG_RE.search(description)
    if match:
        return match.group(1).strip()

    # Domain lookup is case-insensitive: rules.yaml keys and attendee email
    # domains aren't guaranteed to agree on casing (e.g. "Pango.co.il" vs.
    # "pango.co.il"), so compare everything lowercased. Built once per call
    # (not once per attendee) to keep the per-attendee lookups O(1).
    rules_by_domain = {str(domain).lower(): project for domain, project in rules.items()}

    # Priority 2: Rules based on external actor's email. If that specific
    # domain isn't mapped, fall through to Priority 3 instead of giving up —
    # another attendee may still have a mapped domain.
    override_email = event.get("external_actor_email")
    if override_email:
        domain = override_email.split('@')[-1].lower()
        if domain in rules_by_domain:
            return rules_by_domain[domain]

    # Priority 3: Fallback to attendees' domains
    for att in event.get('attendees', []):
        domain = att.get('email', '').split('@')[-1].lower()
        if domain in rules_by_domain:
            return rules_by_domain[domain]

    # No match → default to None (for projectless entry)
    return None
