from matcher import match_project

def test_match_project_explicit_proj():
    event = {"description": "#proj MyProject"}
    rules = {"domain.com": "DomainProject"}
    assert match_project(event, rules) == "MyProject"

def test_match_project_external_actor():
    event = {"external_actor_email": "user@domain.com"}
    rules = {"domain.com": "DomainProject"}
    assert match_project(event, rules) == "DomainProject"

def test_match_project_attendee_domain():
    event = {"attendees": [ {"email": "someone@domain.com"} ]}
    rules = {"domain.com": "DomainProject"}
    assert match_project(event, rules) == "DomainProject"

def test_match_project_no_match():
    event = {"attendees": [ {"email": "someone@other.com"} ]}
    rules = {"domain.com": "DomainProject"}
    assert match_project(event, rules) is None

def test_match_project_attendee_domain_case_insensitive():
    # rules.yaml keys and attendee email domains aren't guaranteed to share
    # casing (e.g. "Pango.co.il" vs. "pango.co.il"); the lookup must not be
    # case-sensitive.
    event = {"attendees": [ {"email": "someone@DOMAIN.com"} ]}
    rules = {"Domain.com": "DomainProject"}
    assert match_project(event, rules) == "DomainProject"

def test_match_project_external_actor_case_insensitive():
    event = {"external_actor_email": "User@DOMAIN.com"}
    rules = {"Domain.com": "DomainProject"}
    assert match_project(event, rules) == "DomainProject"

def test_match_project_external_actor_falls_back_to_attendee_domain():
    # If the external actor's own domain has no rule, other attendees'
    # domains should still be checked instead of giving up immediately.
    event = {
        "external_actor_email": "user@unmapped.com",
        "attendees": [
            {"email": "user@unmapped.com"},
            {"email": "someone@other.com"},
        ],
    }
    rules = {"other.com": "OtherProject"}
    assert match_project(event, rules) == "OtherProject"

def test_match_project_proj_tag_case_insensitive():
    event = {"description": "#PROJ SomeProject"}
    assert match_project(event, {}) == "SomeProject" 