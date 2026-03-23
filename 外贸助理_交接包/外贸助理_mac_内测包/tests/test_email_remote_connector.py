from pathlib import Path

from app.email_remote_connector import MailPullConfig, pull_mail_threads_to_dir, resolve_imap_host


class _FakeImap:
    def __init__(self, host: str) -> None:
        self.host = host
        self.logged_out = False

    def login(self, account: str, password: str):
        if account != "user@example.com" or password != "app-password":
            return "NO", [b"auth failed"]
        return "OK", [b"logged in"]

    def select(self, folder: str, readonly: bool = True):
        if folder != "INBOX":
            return "NO", [b"missing folder"]
        return "OK", [b"2"]

    def search(self, _charset, *criteria):
        _ = criteria
        return "OK", [b"1 2"]

    def fetch(self, message_id: bytes, _query: str):
        body = (
            "From: Buyer <buyer@example.com>\r\n"
            f"Subject: Quote Request {message_id.decode('utf-8')}\r\n"
            "Date: Fri, 20 Mar 2026 10:00:00 +0000\r\n"
            "Content-Type: text/plain; charset=utf-8\r\n"
            "\r\n"
            "Need A100 quote. CIF Dubai.\r\n"
        ).encode("utf-8")
        return "OK", [(b"RFC822", body)]

    def logout(self):
        self.logged_out = True
        return "BYE", [b"logout"]


def test_resolve_imap_host_supports_gmail_outlook() -> None:
    assert resolve_imap_host("gmail") == "imap.gmail.com"
    assert resolve_imap_host("outlook") == "outlook.office365.com"


def test_pull_mail_threads_to_dir_exports_text_files(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("app.email_remote_connector.imaplib.IMAP4_SSL", lambda host: _FakeImap(host))
    target = tmp_path / "mail-pull"
    config = MailPullConfig(
        provider="gmail",
        account="user@example.com",
        password="app-password",
        folder="INBOX",
        days=30,
        max_messages=10,
    )
    stats = pull_mail_threads_to_dir(config=config, output_dir=target)
    assert stats.pulled_messages == 2
    assert stats.exported_files
    for path in stats.exported_files:
        p = Path(path)
        assert p.exists()
        text = p.read_text(encoding="utf-8")
        assert "From:" in text
        assert "Need A100 quote" in text


def test_pull_mail_threads_to_dir_invalid_provider_raises(tmp_path: Path) -> None:
    config = MailPullConfig(
        provider="unknown",
        account="user@example.com",
        password="app-password",
    )
    try:
        pull_mail_threads_to_dir(config=config, output_dir=tmp_path / "mail")
    except ValueError as exc:
        assert "Unsupported provider" in str(exc)
    else:
        raise AssertionError("Expected ValueError for unsupported provider")
