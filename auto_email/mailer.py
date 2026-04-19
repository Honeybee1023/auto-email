from typing import Dict, Iterable, Tuple

from auto_email.gmail_oauth import create_gmail_draft, load_creds, send_gmail_message
from auto_email.smtp_sender import send_batch as send_batch_smtp


def send_batch(
    cfg: Dict[str, str],
    messages: Iterable[Tuple[str, str, str]],
) -> Dict[str, str]:
    token_path = cfg.get("gmail_oauth_token_path", "")
    gmail_address = cfg.get("gmail_address", "")
    reply_to = cfg.get("reply_to_email", "").strip()
    archive_bcc = cfg.get("archive_bcc_email", "").strip()
    creds = load_creds(token_path) if token_path else None

    if creds:
        results: Dict[str, str] = {}
        for to_addr, subject, body in messages:
            try:
                send_gmail_message(
                    creds,
                    gmail_address,
                    to_addr,
                    subject,
                    body,
                    reply_to=reply_to,
                    archive_bcc=archive_bcc,
                )
                results[to_addr] = "sent"
            except Exception as exc:  # noqa: BLE001
                results[to_addr] = str(exc)
        return results

    return send_batch_smtp(cfg, messages)


def create_draft_batch(
    cfg: Dict[str, str],
    messages: Iterable[Tuple[str, str, str]],
) -> Dict[str, str]:
    token_path = cfg.get("gmail_oauth_token_path", "")
    gmail_address = cfg.get("gmail_address", "")
    reply_to = cfg.get("reply_to_email", "").strip()
    archive_bcc = cfg.get("archive_bcc_email", "").strip()
    creds = load_creds(token_path) if token_path else None

    if not creds:
        return {"__error__": "Gmail OAuth is not connected."}

    results: Dict[str, str] = {}
    for to_addr, subject, body in messages:
        try:
            draft_id = create_gmail_draft(
                creds,
                gmail_address,
                to_addr,
                subject,
                body,
                reply_to=reply_to,
                archive_bcc=archive_bcc,
            )
            results[to_addr] = f"draft:{draft_id}" if draft_id else "drafted"
        except Exception as exc:  # noqa: BLE001
            results[to_addr] = str(exc)
    return results
