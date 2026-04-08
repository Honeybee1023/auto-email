from typing import Dict, Iterable, Tuple

from auto_email.gmail_oauth import load_creds, send_gmail_message
from auto_email.smtp_sender import send_batch as send_batch_smtp


def send_batch(
    cfg: Dict[str, str],
    messages: Iterable[Tuple[str, str, str]],
) -> Dict[str, str]:
    token_path = cfg.get("gmail_oauth_token_path", "")
    gmail_address = cfg.get("gmail_address", "")
    creds = load_creds(token_path) if token_path else None

    if creds:
        results: Dict[str, str] = {}
        for to_addr, subject, body in messages:
            try:
                send_gmail_message(creds, gmail_address, to_addr, subject, body)
                results[to_addr] = "sent"
            except Exception as exc:  # noqa: BLE001
                results[to_addr] = str(exc)
        return results

    return send_batch_smtp(cfg, messages)
