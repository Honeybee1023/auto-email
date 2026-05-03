import json
from typing import Any, Dict, Iterable, List

from auto_email.email import render_email
from auto_email.models import Profile


def profile_row_key(row: Dict[str, Any]) -> str:
    email = str(row.get("Email", "")).strip().lower()
    if email:
        return email
    full_name = str(row.get("Full Name", "")).strip().lower()
    company = str(row.get("Company", "")).strip().lower()
    first_name = str(row.get("First Name", "")).strip().lower()
    return "|".join([full_name, first_name, company])


def preview_signature(cfg: Dict[str, Any], profiles: Iterable[Dict[str, Any]]) -> str:
    render_inputs = {
        "template": cfg.get("email_template", ""),
        "subject": cfg.get("email_subject", ""),
        "availability": cfg.get("availability", ""),
        "sender_name": cfg.get("sender_name", ""),
        "sender_intro": cfg.get("sender_intro", ""),
        "profiles": [
            {
                "first_name": str(row.get("First Name", "")),
                "full_name": str(row.get("Full Name", "")),
                "email": str(row.get("Email", "")).strip().lower(),
                "company": str(row.get("Company", "")),
                "job_title": str(row.get("Job Title", "")),
                "mit_details": str(row.get("MIT Details", "")),
                "personalized_sentence": str(row.get("Personalized Sentence", "")),
            }
            for row in profiles
        ],
    }
    return json.dumps(render_inputs, sort_keys=True)


def build_preview_entries(
    cfg: Dict[str, Any],
    profiles: Iterable[Dict[str, Any]],
) -> List[Dict[str, str]]:
    entries: List[Dict[str, str]] = []
    for row in profiles:
        profile = Profile(
            first_name=str(row.get("First Name", "")),
            full_name=str(row.get("Full Name", "")),
            email=str(row.get("Email", "")),
            company=str(row.get("Company", "")),
            job_title=str(row.get("Job Title", "")),
            mit_details=str(row.get("MIT Details", "")),
            personalized_sentence=str(row.get("Personalized Sentence", "")),
        )
        body = render_email(cfg["email_template"], profile, cfg)
        subject_template = cfg.get("email_subject") or "MIT Consulting Group x {company}"
        subject = subject_template.format(company=profile.company)
        entries.append(
            {
                "row_key": profile_row_key(row),
                "label": profile.full_name or profile.email,
                "subject": subject,
                "body": body,
            }
        )
    return entries


def preview_state_values(
    cfg: Dict[str, Any],
    profiles: Iterable[Dict[str, Any]],
) -> Dict[str, str]:
    values: Dict[str, str] = {}
    for entry in build_preview_entries(cfg, profiles):
        values[f"email_subject_{entry['row_key']}"] = entry["subject"]
        values[f"email_body_{entry['row_key']}"] = entry["body"]
    return values
