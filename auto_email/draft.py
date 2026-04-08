import json
import os
from typing import Any, Dict

DRAFT_PATH = os.path.join(os.path.expanduser("~"), ".auto-email-sender", "draft.json")


def load_draft() -> Dict[str, Any]:
    if not os.path.exists(DRAFT_PATH):
        return {}
    with open(DRAFT_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_draft(data: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(DRAFT_PATH), exist_ok=True)
    with open(DRAFT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def clear_draft() -> None:
    if os.path.exists(DRAFT_PATH):
        os.remove(DRAFT_PATH)
