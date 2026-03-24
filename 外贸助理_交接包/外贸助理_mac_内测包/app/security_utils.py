from __future__ import annotations

import base64
import ctypes
import hashlib
import json
import os
import platform
import subprocess
from typing import Any

ENVELOPE_KEY = "__ta_sec_v1__"
MAC_KEYCHAIN_SERVICE = "com.tradeassistant.localvault.v1"
DPAPI_UI_FORBIDDEN = 0x01

SENSITIVE_EXACT_KEYS = {
    "absolute_bottom_price",
    "api_key",
    "api_keys",
    "mail_password",
    "must_include",
    "pricing_rules",
    "price_floor",
    "refresh_token",
    "token",
    "access_token",
}


def encrypt_sensitive_fields(payload: Any, *, namespace: str) -> tuple[Any, bool]:
    return _walk_encrypt(payload, path=(), namespace=namespace)


def decrypt_sensitive_fields(payload: Any, *, namespace: str) -> Any:
    return _walk_decrypt(payload, path=(), namespace=namespace)


def _walk_encrypt(node: Any, *, path: tuple[str, ...], namespace: str) -> tuple[Any, bool]:
    if isinstance(node, dict):
        out: dict[str, Any] = {}
        changed = False
        for key, value in node.items():
            key_str = str(key)
            child_path = path + (key_str,)
            if _is_envelope(value):
                out[key_str] = value
                continue
            if _should_encrypt(child_path, value):
                field_ref = f"{namespace}:{'.'.join(child_path)}"
                encrypted = _encrypt_value(value, field_ref=field_ref)
                out[key_str] = encrypted
                changed = changed or encrypted is not value
                continue
            child_value, child_changed = _walk_encrypt(value, path=child_path, namespace=namespace)
            out[key_str] = child_value
            changed = changed or child_changed
        return out, changed
    if isinstance(node, list):
        out_list: list[Any] = []
        changed = False
        for idx, item in enumerate(node):
            child_value, child_changed = _walk_encrypt(item, path=path + (str(idx),), namespace=namespace)
            out_list.append(child_value)
            changed = changed or child_changed
        return out_list, changed
    return node, False


def _walk_decrypt(node: Any, *, path: tuple[str, ...], namespace: str) -> Any:
    if _is_envelope(node):
        field_ref = f"{namespace}:{'.'.join(path)}"
        try:
            return _decrypt_value(node, field_ref=field_ref)
        except Exception:
            return _default_for_kind(str(node.get(ENVELOPE_KEY, {}).get("kind", "")))
    if isinstance(node, dict):
        return {str(key): _walk_decrypt(value, path=path + (str(key),), namespace=namespace) for key, value in node.items()}
    if isinstance(node, list):
        return [_walk_decrypt(item, path=path + (str(idx),), namespace=namespace) for idx, item in enumerate(node)]
    return node


def _should_encrypt(path: tuple[str, ...], value: Any) -> bool:
    if not path:
        return False
    if isinstance(value, str) and value == "":
        return False
    if isinstance(value, (list, dict)) and not value:
        return False
    tail = path[-1].lower()
    if tail in SENSITIVE_EXACT_KEYS:
        return True
    if "api_key" in tail:
        return True
    if tail.endswith("_token") or tail.startswith("token_"):
        return True
    if len(path) >= 2:
        parent = path[-2].lower()
        if parent == "preference" and tail in {"must_include", "pricing_rules"}:
            return True
    return False


def _is_envelope(value: Any) -> bool:
    return isinstance(value, dict) and ENVELOPE_KEY in value and isinstance(value[ENVELOPE_KEY], dict)


def _encrypt_value(value: Any, *, field_ref: str) -> Any:
    provider = _resolved_provider()
    if provider == "none":
        return value
    plain_text = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    kind = _kind_name(value)
    if provider == "dpapi":
        encrypted = _dpapi_encrypt(plain_text.encode("utf-8"))
        return {
            ENVELOPE_KEY: {
                "provider": "dpapi",
                "kind": kind,
                "ciphertext": base64.b64encode(encrypted).decode("ascii"),
            }
        }
    if provider == "keychain":
        ref = _keychain_ref(field_ref)
        _keychain_store(ref, plain_text)
        return {
            ENVELOPE_KEY: {
                "provider": "keychain",
                "kind": kind,
                "ref": ref,
            }
        }
    return value


def _decrypt_value(envelope: dict[str, Any], *, field_ref: str) -> Any:
    meta = envelope.get(ENVELOPE_KEY, {})
    provider = str(meta.get("provider", "")).strip().lower()
    if provider == "dpapi":
        cipher_b64 = str(meta.get("ciphertext", ""))
        raw = base64.b64decode(cipher_b64.encode("ascii"))
        plain = _dpapi_decrypt(raw).decode("utf-8")
        return json.loads(plain)
    if provider == "keychain":
        ref = str(meta.get("ref", "")).strip() or _keychain_ref(field_ref)
        plain = _keychain_read(ref)
        return json.loads(plain)
    raise ValueError(f"unsupported encrypted provider: {provider}")


def _kind_name(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int):
        return "int"
    if isinstance(value, float):
        return "float"
    if isinstance(value, str):
        return "str"
    if isinstance(value, list):
        return "list"
    if isinstance(value, dict):
        return "dict"
    return "str"


def _default_for_kind(kind: str) -> Any:
    if kind == "list":
        return []
    if kind == "dict":
        return {}
    if kind in {"int", "float"}:
        return 0
    if kind == "bool":
        return False
    if kind == "null":
        return None
    return ""


def _resolved_provider() -> str:
    forced = os.getenv("TRADE_ASSISTANT_SECURITY_BACKEND", "").strip().lower()
    if forced in {"none", "dpapi", "keychain"}:
        return forced
    system_name = platform.system().lower()
    if system_name == "windows":
        return "dpapi"
    if system_name == "darwin":
        return "keychain"
    return "none"


def _keychain_ref(field_ref: str) -> str:
    digest = hashlib.sha256(field_ref.encode("utf-8")).hexdigest()
    return f"v1-{digest[:48]}"


def _keychain_store(ref: str, secret: str) -> None:
    cmd = [
        "security",
        "add-generic-password",
        "-U",
        "-a",
        ref,
        "-s",
        MAC_KEYCHAIN_SERVICE,
        "-w",
        secret,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(f"keychain write failed: {proc.stderr.strip() or proc.stdout.strip()}")


def _keychain_read(ref: str) -> str:
    cmd = [
        "security",
        "find-generic-password",
        "-a",
        ref,
        "-s",
        MAC_KEYCHAIN_SERVICE,
        "-w",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(f"keychain read failed: {proc.stderr.strip() or proc.stdout.strip()}")
    return proc.stdout.rstrip("\r\n")


def _dpapi_encrypt(data: bytes) -> bytes:
    if not data:
        return b""
    crypt32 = ctypes.windll.crypt32
    kernel32 = ctypes.windll.kernel32
    data_in, buffer_in = _blob_from_bytes(data)
    _ = buffer_in  # Keep input buffer alive until API call completes.
    data_out = _DATA_BLOB()
    ok = crypt32.CryptProtectData(
        ctypes.byref(data_in),
        None,
        None,
        None,
        None,
        DPAPI_UI_FORBIDDEN,
        ctypes.byref(data_out),
    )
    if not ok:
        raise OSError("CryptProtectData failed")
    try:
        return ctypes.string_at(data_out.pbData, data_out.cbData)
    finally:
        if data_out.pbData:
            kernel32.LocalFree(data_out.pbData)


def _dpapi_decrypt(data: bytes) -> bytes:
    if not data:
        return b""
    crypt32 = ctypes.windll.crypt32
    kernel32 = ctypes.windll.kernel32
    data_in, buffer_in = _blob_from_bytes(data)
    _ = buffer_in  # Keep input buffer alive until API call completes.
    data_out = _DATA_BLOB()
    ok = crypt32.CryptUnprotectData(
        ctypes.byref(data_in),
        None,
        None,
        None,
        None,
        DPAPI_UI_FORBIDDEN,
        ctypes.byref(data_out),
    )
    if not ok:
        raise OSError("CryptUnprotectData failed")
    try:
        return ctypes.string_at(data_out.pbData, data_out.cbData)
    finally:
        if data_out.pbData:
            kernel32.LocalFree(data_out.pbData)


class _DATA_BLOB(ctypes.Structure):
    _fields_ = [("cbData", ctypes.c_uint32), ("pbData", ctypes.POINTER(ctypes.c_ubyte))]


def _blob_from_bytes(data: bytes) -> tuple[_DATA_BLOB, ctypes.Array[Any]]:
    buffer_obj = ctypes.create_string_buffer(data, len(data))
    blob = _DATA_BLOB(
        cbData=len(data),
        pbData=ctypes.cast(buffer_obj, ctypes.POINTER(ctypes.c_ubyte)),
    )
    return blob, buffer_obj
