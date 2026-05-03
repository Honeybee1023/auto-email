from auto_email.preview import (
    build_preview_entries,
    preview_signature,
    preview_state_values,
    profile_row_key,
)


def _base_cfg():
    return {
        "email_template": (
            "Hi {first_name},\n\n"
            "My name is {sender_name}, and {sender_intro} {personalized_sentence}\n\n"
            "Availability:\n{availability}\n\n"
            "All the best,\n{sender_first_name}"
        ),
        "email_subject": "MIT Consulting Group x {company}",
        "availability": "Mon 2-4pm ET",
        "sender_name": "Honjar Xing",
        "sender_intro": "I'm on the partnerships team and would love to connect.",
    }


def _base_profiles():
    return [
        {
            "First Name": "Sam",
            "Full Name": "Sam Lee",
            "Email": "sam@example.com",
            "Company": "Example Co",
            "Job Title": "Founder",
            "MIT Details": "SB '12, robotics club",
            "Personalized Sentence": "I appreciated your work on climate tech.",
        }
    ]


def test_preview_entries_include_personalization_and_availability():
    entries = build_preview_entries(_base_cfg(), _base_profiles())

    assert len(entries) == 1
    assert "I appreciated your work on climate tech." in entries[0]["body"]
    assert "Mon 2-4pm ET" in entries[0]["body"]
    assert entries[0]["subject"] == "MIT Consulting Group x Example Co"


def test_preview_signature_changes_when_availability_changes():
    cfg = _base_cfg()
    profiles = _base_profiles()

    sig1 = preview_signature(cfg, profiles)
    cfg["availability"] = "Tue 10-11am ET"
    sig2 = preview_signature(cfg, profiles)

    assert sig1 != sig2


def test_preview_state_values_reflect_current_source_data():
    cfg = _base_cfg()
    profiles = _base_profiles()

    values = preview_state_values(cfg, profiles)
    row_key = profile_row_key(profiles[0])

    assert values[f"email_subject_{row_key}"] == "MIT Consulting Group x Example Co"
    assert "Mon 2-4pm ET" in values[f"email_body_{row_key}"]

    cfg["availability"] = "Fri 1-2pm ET"
    cfg["email_template"] = cfg["email_template"].replace(
        "{personalized_sentence}", "and {personalized_sentence}"
    )
    profiles[0]["Personalized Sentence"] = "I'm excited to reconnect."
    updated_values = preview_state_values(cfg, profiles)

    assert "Fri 1-2pm ET" in updated_values[f"email_body_{row_key}"]
    assert "I'm excited to reconnect." in updated_values[f"email_body_{row_key}"]
