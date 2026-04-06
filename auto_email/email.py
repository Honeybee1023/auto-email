from typing import Dict

from auto_email.models import Profile


def sender_first_name(sender_name: str) -> str:
    parts = [p for p in sender_name.split() if p]
    return parts[0] if parts else ""


def render_email(template: str, profile: Profile, cfg: Dict[str, str]) -> str:
    return template.format(
        first_name=profile.first_name,
        sender_name=cfg.get("sender_name", ""),
        sender_intro=cfg.get("sender_intro", ""),
        personalized_sentence=profile.personalized_sentence,
        company=profile.company,
        availability=cfg.get("availability", ""),
        sender_first_name=sender_first_name(cfg.get("sender_name", "")),
    )
