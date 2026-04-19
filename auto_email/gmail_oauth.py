import base64
import json
import os
from email.message import EmailMessage
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]


def load_creds(token_path: str) -> Optional[Credentials]:
    if not token_path or not os.path.exists(token_path):
        return None
    creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(token_path, "w", encoding="utf-8") as f:
            f.write(creds.to_json())
    return creds


def run_auth_flow(client_secret_path: str, token_path: str) -> Credentials:
    flow = InstalledAppFlow.from_client_secrets_file(client_secret_path, SCOPES)
    creds = flow.run_local_server(port=0)
    os.makedirs(os.path.dirname(token_path), exist_ok=True)
    with open(token_path, "w", encoding="utf-8") as f:
        f.write(creds.to_json())
    return creds


def send_gmail_message(
    creds: Credentials,
    sender: str,
    to_addr: str,
    subject: str,
    body: str,
    reply_to: str = "",
    archive_bcc: str = "",
) -> None:
    message = EmailMessage()
    message["From"] = sender
    message["To"] = to_addr
    message["Subject"] = subject
    if reply_to:
        message["Reply-To"] = reply_to
    if archive_bcc:
        message["Bcc"] = archive_bcc
    message.set_content(body)

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
    service = build("gmail", "v1", credentials=creds)
    service.users().messages().send(userId="me", body={"raw": raw}).execute()
