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
    existing = ws.get_all_values()
    last_filled = 0
    for i, row in enumerate(existing, start=1):
        if any(cell.strip() for cell in row):
            last_filled = i
    start_row = last_filled + 1
    if not rows:
        return
    num_cols = max(len(r) for r in rows)
    end_row = start_row + len(rows) - 1
    start_cell = gspread.utils.rowcol_to_a1(start_row, 1)
    end_cell = gspread.utils.rowcol_to_a1(end_row, num_cols)
    ws.update(f"{start_cell}:{end_cell}", rows, value_input_option="USER_ENTERED")
