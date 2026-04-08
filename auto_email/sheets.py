from datetime import datetime
from typing import Dict, List
import re

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
        raw = str(row.get(email_column, "")).strip().lower()
        if not raw:
            continue
        parts = [p.strip() for p in re.split(r"[;,]", raw)]
        for email in parts:
            if email:
                existing[email] = row
    return existing


def build_log_row(sender_name: str, profile: Profile) -> List[str]:
    date_str = ""
    notes_parts = [p for p in [profile.job_title, profile.mit_details] if p]
    notes = "; ".join(notes_parts)
    words = notes.split()
    if len(words) > 10:
        notes = " ".join(words[:10])
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
    start_row = None
    for i, row in enumerate(existing, start=1):
        name_cell = row[0].strip() if len(row) > 0 else ""
        if not name_cell:
            start_row = i
            break
    if start_row is None:
        start_row = len(existing) + 1
    if not rows:
        return
    required_rows = start_row + len(rows) - 1
    if required_rows > ws.row_count:
        ws.resize(rows=required_rows)
    num_cols = max(len(r) for r in rows)
    end_row = start_row + len(rows) - 1
    start_cell = gspread.utils.rowcol_to_a1(start_row, 1)
    end_cell = gspread.utils.rowcol_to_a1(end_row, num_cols)
    ws.update(f"{start_cell}:{end_cell}", rows, value_input_option="USER_ENTERED")
