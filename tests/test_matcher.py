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