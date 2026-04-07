import os
import streamlit as st

from auto_email.claude import parse_numbered_list
from auto_email.config import load_config, save_config
from auto_email.email import render_email
from auto_email.smtp_sender import send_batch
from auto_email.sheets import append_rows, build_log_row
from auto_email.models import Profile
from auto_email.parser import parse_profiles
from auto_email.prompt import generate_prompt
from auto_email.sheets import fetch_existing_emails

st.set_page_config(page_title="Auto Email Sender", layout="wide")

st.title("Auto Email Sender")

with st.sidebar:
    st.header("Settings")
    cfg = load_config()
    cfg["gmail_address"] = st.text_input("Gmail Address", value=cfg["gmail_address"])
    cfg["gmail_app_password"] = st.text_input(
        "Gmail App Password", value=cfg["gmail_app_password"], type="password"
    )
    cfg["sender_name"] = st.text_input("Sender Name", value=cfg["sender_name"])
    cfg["sender_intro"] = st.text_area("Sender Intro", value=cfg["sender_intro"])
    cfg["email_subject"] = st.text_input("Email Subject", value=cfg["email_subject"])
    cfg["availability"] = st.text_area("Availability", value=cfg["availability"])
    cfg["email_template"] = st.text_area(
        "Email Template", value=cfg["email_template"], height=300
    )
    cfg["google_sheet_id"] = st.text_input(
        "Google Sheet ID", value=cfg["google_sheet_id"]
    )
    cfg["google_service_account_json"] = st.text_input(
        "Service Account JSON Path", value=cfg["google_service_account_json"]
    )
    st.subheader("Sheet Columns")
    cfg["sheet_col_sender_name"] = st.text_input(
        "Sender Name Column", value=cfg["sheet_col_sender_name"]
    )
    cfg["sheet_col_email"] = st.text_input(
        "Client Email Column", value=cfg["sheet_col_email"]
    )
    cfg["sheet_col_client_name"] = st.text_input(
        "Client Name Column", value=cfg["sheet_col_client_name"]
    )
    cfg["sheet_col_company"] = st.text_input(
        "Company Column", value=cfg["sheet_col_company"]
    )
    cfg["sheet_col_date"] = st.text_input(
        "Date Column", value=cfg["sheet_col_date"]
    )
    cfg["sheet_col_notes"] = st.text_input(
        "Notes Column", value=cfg["sheet_col_notes"]
    )
    st.caption("Do not share your Gmail App Password or service account key file.")

    with st.expander("Google Sheets One-Time Setup"):
        st.markdown(
            """
1. Create or select a Google Cloud project.
2. Enable the Google Sheets API.
3. Create a Service Account and download the JSON key file.
4. Share the Google Sheet with the service account email (Editor access).
5. Paste the Sheet ID and JSON key path above.
"""
        )

    st.subheader("Status")
    missing = []
    if not cfg.get("gmail_address"):
        missing.append("Gmail Address")
    if not cfg.get("gmail_app_password"):
        missing.append("Gmail App Password")
    if not cfg.get("sender_name"):
        missing.append("Sender Name")
    if not cfg.get("email_subject"):
        missing.append("Email Subject")
    if not cfg.get("email_template"):
        missing.append("Email Template")

    sheets_ready = True
    if not cfg.get("google_sheet_id"):
        sheets_ready = False
        missing.append("Google Sheet ID")
    json_path = cfg.get("google_service_account_json", "")
    if not json_path:
        sheets_ready = False
        missing.append("Service Account JSON Path")
    elif not os.path.exists(json_path):
        sheets_ready = False
        missing.append("Service Account JSON File (not found)")

    ready_to_send = len(missing) == 0
    if ready_to_send:
        st.success("Ready to send: all required settings are present.")
    else:
        st.error("Not ready to send. Missing:")
        st.write(", ".join(missing))

    if not sheets_ready:
        st.warning("Google Sheets is not fully configured. Dedup and logging will fail.")

    if st.button("Save Settings"):
        save_config(cfg)
        st.success("Settings saved.")

st.write("Workflow steps will appear here.")

if "profiles" not in st.session_state:
    st.session_state["profiles"] = []

st.subheader("1. Paste Profiles")
raw = st.text_area("Paste raw alumni profiles here", height=200, key="raw_profiles")
if st.button("Parse Profiles"):
    parsed = parse_profiles(raw)
    if not parsed and raw.strip():
        st.session_state["profiles"] = [
            {
                "First Name": "",
                "Full Name": "",
                "Email": "",
                "Company": "",
                "Job Title": "",
                "MIT Details": "",
                "Personalized Sentence": "",
            }
        ]
        st.session_state["parse_error_raw"] = raw
    else:
        st.session_state["profiles"] = [
            {
                "First Name": p.first_name,
                "Full Name": p.full_name,
                "Email": p.email,
                "Company": p.company,
                "Job Title": p.job_title,
                "MIT Details": p.mit_details,
                "Personalized Sentence": p.personalized_sentence,
            }
            for p in parsed
        ]
        st.session_state["parse_error_raw"] = ""

st.subheader("2. Review Parsed Data")
if st.session_state["profiles"]:
    st.session_state["profiles"] = st.data_editor(
        st.session_state["profiles"], num_rows="dynamic", use_container_width=True
    )
    if st.session_state.get("parse_error_raw"):
        st.text_area(
            "Raw text (parsing failed; please fill fields manually)",
            value=st.session_state["parse_error_raw"],
            height=150,
        )
else:
    st.info("No profiles parsed yet.")

st.subheader("3. Duplicate Check (Google Sheets)")
if st.session_state["profiles"]:
    if st.button("Check Duplicates"):
        try:
            existing = fetch_existing_emails(
                cfg.get("google_service_account_json", ""),
                cfg.get("google_sheet_id", ""),
                cfg.get("sheet_col_email", "Client Email"),
            )
            updated = []
            for row in st.session_state["profiles"]:
                email = str(row.get("Email", "")).strip().lower()
                hit = existing.get(email)
                if hit:
                    row["Duplicate"] = "YES"
                    sender_col = cfg.get("sheet_col_sender_name", "Sender Name")
                    date_col = cfg.get("sheet_col_date", "Date (MM/DD)")
                    sender = hit.get(sender_col, "")
                    date_val = hit.get(date_col, "")
                    row["Duplicate Info"] = f"{sender} on {date_val}"
                else:
                    row["Duplicate"] = ""
                    row["Duplicate Info"] = ""
                updated.append(row)
            st.session_state["profiles"] = updated
            st.success("Duplicate check complete.")
        except Exception as exc:  # noqa: BLE001
            st.warning(f"Could not read Google Sheet: {exc}")

st.subheader("4. Generate Personalization")
if st.session_state["profiles"]:
    if st.button("Generate Claude Prompt"):
        profiles = [
            Profile(
                first_name=row.get("First Name", ""),
                full_name=row.get("Full Name", ""),
                email=row.get("Email", ""),
                company=row.get("Company", ""),
                job_title=row.get("Job Title", ""),
                mit_details=row.get("MIT Details", ""),
                personalized_sentence=row.get("Personalized Sentence", ""),
            )
            for row in st.session_state["profiles"]
        ]
        st.session_state["claude_prompt"] = generate_prompt(profiles)

    prompt_value = st.session_state.get("claude_prompt", "")
    st.text_area("Claude Prompt (copy/paste)", value=prompt_value, height=200)
    response = st.text_area("Paste Claude Response Here", height=200, key="claude_response")
    if st.button("Apply Personalization"):
        parsed = parse_numbered_list(response, len(st.session_state["profiles"]))
        if not parsed:
            st.warning("Could not parse response. Please ensure the list matches the profile count.")
        else:
            updated = []
            for row, sentence in zip(st.session_state["profiles"], parsed):
                row["Personalized Sentence"] = sentence
                updated.append(row)
            st.session_state["profiles"] = updated
            st.success("Personalized sentences applied.")

st.subheader("5. Preview Emails")
if st.session_state["profiles"]:
    if not cfg.get("email_template"):
        st.info("Add an email template in Settings to preview emails.")
    else:
        for idx, row in enumerate(st.session_state["profiles"]):
            profile = Profile(
                first_name=row.get("First Name", ""),
                full_name=row.get("Full Name", ""),
                email=row.get("Email", ""),
                company=row.get("Company", ""),
                job_title=row.get("Job Title", ""),
                mit_details=row.get("MIT Details", ""),
                personalized_sentence=row.get("Personalized Sentence", ""),
            )
            body = render_email(cfg["email_template"], profile, cfg)
            label = f"{profile.full_name or profile.email}"
            with st.expander(label):
                st.text_area(
                    "Email Body",
                    value=body,
                    height=250,
                    key=f"email_body_{idx}",
                )

st.subheader("6. Send")
if st.session_state["profiles"]:
    confirm_send = st.checkbox(
        "I confirm all settings are correct and I want to send now."
    )
    send_disabled = not (confirm_send and ready_to_send)
    if st.button("Send All", disabled=send_disabled):
        messages = []
        email_to_profile = {}
        for idx, row in enumerate(st.session_state["profiles"]):
            to_addr = row.get("Email", "")
            body = st.session_state.get(f"email_body_{idx}", "")
            if to_addr and body:
                email_to_profile[to_addr] = Profile(
                    first_name=row.get("First Name", ""),
                    full_name=row.get("Full Name", ""),
                    email=row.get("Email", ""),
                    company=row.get("Company", ""),
                    job_title=row.get("Job Title", ""),
                    mit_details=row.get("MIT Details", ""),
                    personalized_sentence=row.get("Personalized Sentence", ""),
                )
                messages.append((to_addr, body))
        results = send_batch(
            cfg, messages, subject=cfg.get("email_subject", "Outreach")
        )
        st.session_state["send_results"] = results

        try:
            rows = [
                build_log_row(cfg.get("sender_name", ""), email_to_profile[email])
                for email, status in results.items()
                if status == "sent"
            ]
            if rows:
                append_rows(
                    cfg.get("google_service_account_json", ""),
                    cfg.get("google_sheet_id", ""),
                    rows,
                )
                st.success("Logged sent emails to Google Sheets.")
        except Exception as exc:  # noqa: BLE001
            st.warning(f"Could not write to Google Sheet: {exc}")
            if rows:
                st.text_area("Rows to add manually", value=str(rows), height=150)

    if st.session_state.get("send_results"):
        st.write("Send results:")
        st.json(st.session_state["send_results"])
