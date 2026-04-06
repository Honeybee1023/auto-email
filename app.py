import streamlit as st

from mcg.claude import parse_numbered_list
from mcg.config import load_config, save_config
from mcg.email import render_email
from mcg.models import Profile
from mcg.parser import parse_profiles
from mcg.prompt import generate_prompt
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
