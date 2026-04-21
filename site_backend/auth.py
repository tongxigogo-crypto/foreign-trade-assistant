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


def is_authenticated(cookie_header: str | None, password: str, session_secret: str) -> bool:
    if not cookie_header:
        return False
    expected = build_session_value(password, session_secret)
    cookies = {}
    for item in cookie_header.split(";"):
        if "=" not in item:
            continue
        key, value = item.strip().split("=", 1)
        cookies[key] = value
    return hmac.compare_digest(cookies.get(COOKIE_NAME, ""), expected)
