def match_project(event, rules):
    participants = [att.get('email', '') for att in event.get('attendees', [])]
    summary = event.get('summary', '').lower()
    for email in participants:
        domain = email.split('@')[-1]
        if domain in rules:
            return rules[domain]
    return rules.get('default')
