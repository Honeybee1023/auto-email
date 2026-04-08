import json
import os
from typing import Any, Dict

CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".auto-email-sender")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")

DEFAULT_CONFIG: Dict[str, Any] = {
    "gmail_address": "",
    "gmail_app_password": "",
    "sender_name": "",
    "sender_intro": "",
    "email_subject": "MIT Consulting Group x {company}",
    "availability": "",
    "email_template": "",
    "google_sheet_id": "",
    "google_service_account_json": "",
    "sheet_col_sender_name": "Name (MCG)",
    "sheet_col_email": "Email of Client",
    "sheet_col_client_name": "Client Name",
    "sheet_col_company": "Company",
    "sheet_col_date": "Date (MM/DD)",
    "sheet_col_notes": "Notes",
    "gmail_oauth_client_json": "",
    "gmail_oauth_token_path": "",
    "saved_templates": [],
}


def ensure_config_dir() -> None:
    os.makedirs(CONFIG_DIR, exist_ok=True)


def load_config() -> Dict[str, Any]:
    if not os.path.exists(CONFIG_PATH):
        return dict(DEFAULT_CONFIG)
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    merged = dict(DEFAULT_CONFIG)
    merged.update({k: v for k, v in data.items() if k in DEFAULT_CONFIG})
    return merged


def save_config(cfg: Dict[str, Any]) -> None:
    ensure_config_dir()
    safe = dict(DEFAULT_CONFIG)
    safe.update({k: cfg.get(k, "") for k in DEFAULT_CONFIG})
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(safe, f, indent=2)
