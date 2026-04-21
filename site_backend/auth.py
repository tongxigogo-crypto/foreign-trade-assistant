from __future__ import annotations

import hashlib
import hmac


COOKIE_NAME = "site_admin_session"


def build_session_value(password: str, session_secret: str) -> str:
    return hmac.new(
        session_secret.encode("utf-8"),
        password.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def _extract_cookie_value(cookie_header: str | None) -> str:
    if not cookie_header:
        return ""
    cookies = {}
    for item in cookie_header.split(";"):
        if "=" not in item:
            continue
        key, value = item.strip().split("=", 1)
        cookies[key] = value
    return cookies.get(COOKIE_NAME, "")


def is_authenticated(cookie_header: str | None, password: str, session_secret: str) -> bool:
    expected = build_session_value(password, session_secret)
    return hmac.compare_digest(_extract_cookie_value(cookie_header), expected)


def is_token_authenticated(token: str | None, password: str, session_secret: str) -> bool:
    if not token:
        return False
    expected = build_session_value(password, session_secret)
    return hmac.compare_digest(token, expected)
