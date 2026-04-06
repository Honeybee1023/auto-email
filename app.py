import streamlit as st

from mcg.config import load_config, save_config
from mcg.parser import parse_profiles
from mcg.sheets import fetch_existing_emails

st.set_page_config(page_title="MCG Email Sender", layout="wide")

st.title("MCG Email Sender")

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

st.subheader("2. Review Parsed Data")
if st.session_state["profiles"]:
    st.session_state["profiles"] = st.data_editor(
        st.session_state["profiles"], num_rows="dynamic", use_container_width=True
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
            )
            updated = []
            for row in st.session_state["profiles"]:
                email = str(row.get("Email", "")).strip().lower()
                hit = existing.get(email)
                if hit:
                    row["Duplicate"] = "YES"
                    row["Duplicate Info"] = f"{hit.get('Name (MCG)', '')} on {hit.get('Date (MM/DD)', '')}"
                else:
                    row["Duplicate"] = ""
                    row["Duplicate Info"] = ""
                updated.append(row)
            st.session_state["profiles"] = updated
            st.success("Duplicate check complete.")
        except Exception as exc:  # noqa: BLE001
            st.warning(f"Could not read Google Sheet: {exc}")
