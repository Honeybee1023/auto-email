# MCG Email Sender

Local Streamlit app for parsing MIT alumni profiles, generating personalization prompts, sending outreach emails via Gmail SMTP, and logging activity to Google Sheets.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
streamlit run app.py
```

## Notes
- This repo contains no personal data. Configure your own settings locally.
- Settings are stored at `~/.mcg-email-sender/config.json`.
- See `config.example.json` for placeholder values.
