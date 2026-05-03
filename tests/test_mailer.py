from google.auth.exceptions import RefreshError

from auto_email import mailer


def test_create_draft_batch_reports_expired_token(monkeypatch):
    def fake_load_creds(_token_path):
        raise RefreshError("invalid_grant")

    monkeypatch.setattr(mailer, "load_creds", fake_load_creds)

    result = mailer.create_draft_batch(
        {
            "gmail_oauth_token_path": "/tmp/token.json",
            "gmail_address": "sender@example.com",
            "reply_to_email": "",
            "archive_bcc_email": "",
        },
        [("to@example.com", "Subject", "Body")],
    )

    assert result == {
        "__error__": "Gmail OAuth token expired or was revoked. Reconnect Gmail for drafts."
    }


def test_send_batch_falls_back_to_smtp_when_oauth_missing(monkeypatch):
    called = {}

    def fake_send_batch_smtp(cfg, messages):
        called["cfg"] = cfg
        called["messages"] = list(messages)
        return {"to@example.com": "sent via smtp"}

    monkeypatch.setattr(mailer, "send_batch_smtp", fake_send_batch_smtp)

    result = mailer.send_batch(
        {
            "gmail_oauth_token_path": "",
            "gmail_address": "sender@example.com",
            "reply_to_email": "",
            "archive_bcc_email": "",
        },
        [("to@example.com", "Subject", "Body")],
    )

    assert result == {"to@example.com": "sent via smtp"}
    assert called["messages"] == [("to@example.com", "Subject", "Body")]
