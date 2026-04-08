import smtplib
import time
from email.message import EmailMessage
from typing import Dict, Iterable, Tuple


def send_email(
    cfg: Dict[str, str], to_addr: str, subject: str, body: str
) -> Tuple[bool, str]:
    msg = EmailMessage()
    msg["From"] = cfg.get("gmail_address", "")
    msg["To"] = to_addr
    msg["Subject"] = subject
    msg.set_content(body)

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(cfg.get("gmail_address", ""), cfg.get("gmail_app_password", ""))
            server.send_message(msg)
        return True, ""
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)


def send_batch(
    cfg: Dict[str, str],
    messages: Iterable[Tuple[str, str, str]],
    delay_seconds: float = 2.0,
) -> Dict[str, str]:
    results: Dict[str, str] = {}
    for to_addr, subject, body in messages:
        ok, err = send_email(cfg, to_addr, subject, body)
        results[to_addr] = "sent" if ok else err
        time.sleep(delay_seconds)
    return results
