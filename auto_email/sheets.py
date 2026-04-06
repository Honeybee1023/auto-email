from datetime import datetime
from typing import Dict, List

import gspread

from auto_email.models import Profile


def _open_sheet(service_account_json: str, sheet_id: str):
    client = gspread.service_account(filename=service_account_json)
    sheet = client.open_by_key(sheet_id)
    return sheet.get_worksheet(0)


def fetch_existing_emails(
    service_account_json: str, sheet_id: str, email_column: str
) -> Dict[str, Dict[str, str]]:
    ws = _open_sheet(service_account_json, sheet_id)
    rows = ws.get_all_records()
    existing: Dict[str, Dict[str, str]] = {}
    for row in rows:
        email = str(row.get(email_column, "")).strip().lower()
        if email:
            existing[email] = row
    return existing


def build_log_row(sender_name: str, profile: Profile) -> List[str]:
    date_str = datetime.now().strftime("%m/%d")
    notes_parts = [p for p in [profile.job_title, profile.mit_details] if p]
    notes = "; ".join(notes_parts)
    return [
        sender_name,
        profile.email,
        profile.full_name,
        profile.company,
        date_str,
        notes,
    ]


def append_rows(
    service_account_json: str, sheet_id: str, rows: List[List[str]]
) -> None:
    ws = _open_sheet(service_account_json, sheet_id)
    ws.append_rows(rows, value_input_option="USER_ENTERED")
