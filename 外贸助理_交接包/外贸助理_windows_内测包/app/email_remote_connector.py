from __future__ import annotations

import imaplib
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from email import policy
from email.parser import BytesParser
from email.utils import parseaddr
from pathlib import Path
from typing import Callable


@dataclass
class MailPullConfig:
    provider: str
    account: str
    password: str
    folder: str = "INBOX"
    days: int = 30
    max_messages: int = 200
    host: str = ""
    port: int = 993


@dataclass
class MailPullStats:
    provider: str
    account: str
    scanned_messages: int = 0
    pulled_messages: int = 0
    exported_files: list[str] = field(default_factory=list)
    failed_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "provider": self.provider,
            "account": self.account,
            "scanned_messages": self.scanned_messages,
            "pulled_messages": self.pulled_messages,
            "exported_files": list(self.exported_files),
            "failed_ids": list(self.failed_ids),
        }


def resolve_imap_host(provider: str) -> str:
    key = provider.strip().lower()
    if key == "gmail":
        return "imap.gmail.com"
    if key in {"outlook", "microsoft"}:
        return "outlook.office365.com"
    raise ValueError(f"Unsupported provider: {provider}")


def pull_mail_threads_to_dir(
    *,
    config: MailPullConfig,
    output_dir: Path,
    progress_callback: Callable[[dict], None] | None = None,
) -> MailPullStats:
    provider = config.provider.strip().lower()
    host = config.host.strip() or resolve_imap_host(provider)
    folder = config.folder.strip() or "INBOX"
    account = config.account.strip()
    password = config.password
    if not account or not password:
        raise ValueError("account/password required")

    output_dir.mkdir(parents=True, exist_ok=True)
    port = int(config.port)
    if port == 993:
        conn = imaplib.IMAP4_SSL(host)
    else:
        conn = imaplib.IMAP4_SSL(host, port)
    stats = MailPullStats(provider=provider, account=account)
    try:
        login_status, _ = conn.login(account, password)
        if str(login_status).upper() != "OK":
            raise ValueError("mail login failed")
        select_status, _ = conn.select(folder, readonly=True)
        if str(select_status).upper() != "OK":
            raise ValueError(f"mail folder not found: {folder}")
        since = _imap_since(days=max(1, int(config.days)))
        search_status, rows = conn.search(None, "SINCE", since)
        if str(search_status).upper() != "OK":
            raise ValueError("mail search failed")
        ids = (rows[0] or b"").split() if rows else []
        if int(config.max_messages) > 0:
            ids = ids[-int(config.max_messages) :]
        stats.scanned_messages = len(ids)
        total = len(ids)
        for idx, msg_id in enumerate(ids, start=1):
            msg_text_id = msg_id.decode("utf-8", errors="ignore")
            try:
                fetch_status, payload = conn.fetch(msg_id, "(RFC822)")
                if str(fetch_status).upper() != "OK":
                    stats.failed_ids.append(msg_text_id)
                    continue
                raw = _extract_raw_message(payload)
                if not raw:
                    stats.failed_ids.append(msg_text_id)
                    continue
                text = _normalize_message_to_text(raw=raw)
                file_name = f"{idx:04d}_{msg_text_id}_{_safe_file_name(_subject_for_file(text))}.txt"
                path = output_dir / file_name
                path.write_text(text, encoding="utf-8")
                stats.exported_files.append(str(path))
                stats.pulled_messages += 1
            except OSError:
                stats.failed_ids.append(msg_text_id)
            finally:
                if progress_callback:
                    progress_callback(
                        {
                            "phase": "pull",
                            "current": idx,
                            "total": total,
                            "pulled_messages": stats.pulled_messages,
                            "failed_messages": len(stats.failed_ids),
                        }
                    )
    finally:
        try:
            conn.logout()
        except OSError:
            pass
    return stats


def _imap_since(*, days: int) -> str:
    dt = datetime.now(UTC) - timedelta(days=max(1, days))
    return dt.strftime("%d-%b-%Y")


def _extract_raw_message(payload: list | tuple | None) -> bytes:
    if not payload:
        return b""
    for item in payload:
        if isinstance(item, tuple) and len(item) >= 2:
            content = item[1]
            if isinstance(content, bytes):
                return content
    return b""


def _normalize_message_to_text(*, raw: bytes) -> str:
    msg = BytesParser(policy=policy.default).parsebytes(raw)
    from_header = str(msg.get("From", "")).strip()
    sender_name, sender_email = parseaddr(from_header)
    from_line = from_header
    if sender_email:
        display = sender_name or sender_email.split("@", 1)[0]
        from_line = f"{display} <{sender_email}>"
    subject = str(msg.get("Subject", "")).strip()
    date_line = str(msg.get("Date", "")).strip()
    body = _extract_body_text(msg)
    lines = [f"From: {from_line}", f"Subject: {subject}", f"Date: {date_line}", "", body.strip(), ""]
    return "\n".join(lines)


def _extract_body_text(msg) -> str:
    if msg.is_multipart():
        chunks: list[str] = []
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type == "text/plain":
                try:
                    chunks.append(part.get_content())
                except (LookupError, UnicodeError):
                    payload = part.get_payload(decode=True) or b""
                    chunks.append(payload.decode("utf-8", errors="ignore"))
        if chunks:
            return "\n".join(chunks)
        for part in msg.walk():
            if part.get_content_type() == "text/html":
                try:
                    html = part.get_content()
                except (LookupError, UnicodeError):
                    payload = part.get_payload(decode=True) or b""
                    html = payload.decode("utf-8", errors="ignore")
                return _strip_html_tags(html)
        return ""
    try:
        content = msg.get_content()
    except (LookupError, UnicodeError):
        payload = msg.get_payload(decode=True) or b""
        content = payload.decode("utf-8", errors="ignore")
    if msg.get_content_type() == "text/html":
        return _strip_html_tags(content)
    return str(content)


def _strip_html_tags(value: str) -> str:
    text = re.sub(r"<\s*br\s*/?\s*>", "\n", value, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _safe_file_name(value: str) -> str:
    clean = re.sub(r"[^A-Za-z0-9_-]+", "_", value).strip("_")
    return clean[:48] or "mail"


def _subject_for_file(text: str) -> str:
    for line in text.splitlines():
        if line.lower().startswith("subject:"):
            return line.split(":", 1)[1].strip()
    return "mail"
