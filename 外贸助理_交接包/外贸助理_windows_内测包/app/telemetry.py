from __future__ import annotations

import os
from typing import Any

_sentry_sdk = None
_initialized = False
_capture_enabled = False


def _sanitize_event(event: dict[str, Any], _hint: dict[str, Any]) -> dict[str, Any] | None:
    # Keep only crash diagnostics. Do not send request/user payloads.
    event.pop("request", None)
    event.pop("user", None)
    if isinstance(event.get("breadcrumbs"), dict):
        values = event["breadcrumbs"].get("values")
        if isinstance(values, list):
            for item in values:
                if isinstance(item, dict):
                    item.pop("data", None)
    return event


def init_error_reporting(*, enabled: bool, app_version: str, surface: str) -> bool:
    global _sentry_sdk, _initialized, _capture_enabled
    _capture_enabled = bool(enabled)
    if _initialized:
        return _capture_enabled and _sentry_sdk is not None

    dsn = os.getenv("TRADE_ASSISTANT_SENTRY_DSN", "").strip()
    if not dsn:
        _initialized = True
        return False

    try:
        import sentry_sdk  # type: ignore
    except Exception:
        _initialized = True
        return False

    sentry_sdk.init(
        dsn=dsn,
        release=app_version,
        traces_sample_rate=0.0,
        send_default_pii=False,
        before_send=_sanitize_event,
    )
    sentry_sdk.set_tag("surface", surface)
    _sentry_sdk = sentry_sdk
    _initialized = True
    return _capture_enabled


def set_error_reporting_enabled(enabled: bool) -> None:
    global _capture_enabled
    _capture_enabled = bool(enabled)


def capture_exception(exc: BaseException, context: dict[str, Any] | None = None) -> None:
    if not _capture_enabled or _sentry_sdk is None:
        return
    try:
        if context:
            with _sentry_sdk.push_scope() as scope:
                for key, value in context.items():
                    scope.set_tag(str(key), str(value))
                _sentry_sdk.capture_exception(exc)
        else:
            _sentry_sdk.capture_exception(exc)
    except Exception:
        # Never break app flow because of telemetry failures.
        return

