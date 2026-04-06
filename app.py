import streamlit as st

from mcg.config import load_config, save_config

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
