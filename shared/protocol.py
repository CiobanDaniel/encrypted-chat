"""Shared wire protocol helpers for client and server.

This keeps packet framing and parsing in one place so protocol changes
are easier and less error-prone.
"""

from __future__ import annotations

import json
from typing import Dict, Optional, Tuple

ENCODING = "utf-8"

REGISTER_PREFIX = "REGISTER:"
REGISTER_JSON_PREFIX = "REGISTER_JSON:"
SERVER_PREFIX = "SERVER:"
ROUTE_PREFIX = b"ROUTE:"
FROM_PREFIX = b"FROM:"

PAYLOAD_PUBKEY = b"PUBKEY:"
PAYLOAD_PUBKEY_REPLY = b"PUBKEY_REPLY:"
PAYLOAD_MSG = b"MSG:"


def build_register(username: str) -> bytes:
    return f"{REGISTER_PREFIX}{username}".encode(ENCODING)


def parse_register(data: bytes) -> Optional[str]:
    try:
        text = data.decode(ENCODING)
    except UnicodeDecodeError:
        return None
    if not text.startswith(REGISTER_PREFIX):
        return None
    username = text[len(REGISTER_PREFIX) :].strip()
    return username or None


def build_register_json(
    username: str,
    account_id: str,
    device_id: str,
    account_mode: str,
    identity_key_b64: str = "",
    linked_email: str = "",
    linked_phone: str = "",
) -> bytes:
    payload = {
        "username": username,
        "account_id": account_id,
        "device_id": device_id,
        "account_mode": account_mode,
        "identity_key_b64": identity_key_b64,
        "linked_email": linked_email,
        "linked_phone": linked_phone,
    }
    return f"{REGISTER_JSON_PREFIX}{json.dumps(payload, separators=(',', ':'))}".encode(ENCODING)


def parse_register_packet(data: bytes) -> Optional[Dict[str, str]]:
    try:
        text = data.decode(ENCODING)
    except UnicodeDecodeError:
        return None

    if text.startswith(REGISTER_JSON_PREFIX):
        raw_json = text[len(REGISTER_JSON_PREFIX) :]
        try:
            parsed = json.loads(raw_json)
        except json.JSONDecodeError:
            return None
        if not isinstance(parsed, dict):
            return None
        username = str(parsed.get("username", "")).strip()
        if not username:
            return None
        return {
            "username": username,
            "account_id": str(parsed.get("account_id", "")),
            "device_id": str(parsed.get("device_id", "")),
            "account_mode": str(parsed.get("account_mode", "anonymous")),
            "identity_key_b64": str(parsed.get("identity_key_b64", "")),
            "linked_email": str(parsed.get("linked_email", "")),
            "linked_phone": str(parsed.get("linked_phone", "")),
        }

    username = parse_register(data)
    if not username:
        return None
    return {
        "username": username,
        "account_id": "",
        "device_id": "",
        "account_mode": "legacy",
        "identity_key_b64": "",
        "linked_email": "",
        "linked_phone": "",
    }


def build_server_message(message: str) -> bytes:
    return f"{SERVER_PREFIX}{message}".encode(ENCODING)


def parse_server_message(data: bytes) -> Optional[str]:
    try:
        text = data.decode(ENCODING)
    except UnicodeDecodeError:
        return None
    if not text.startswith(SERVER_PREFIX):
        return None
    return text[len(SERVER_PREFIX) :]


def build_route(target_user: str, payload: bytes) -> bytes:
    return ROUTE_PREFIX + target_user.encode(ENCODING) + b":" + payload


def parse_route(data: bytes) -> Optional[Tuple[str, bytes]]:
    parts = data.split(b":", 2)
    if len(parts) != 3 or parts[0] != b"ROUTE":
        return None
    try:
        target_user = parts[1].decode(ENCODING)
    except UnicodeDecodeError:
        return None
    return target_user, parts[2]


def build_from(sender_user: str, payload: bytes) -> bytes:
    return FROM_PREFIX + sender_user.encode(ENCODING) + b":" + payload


def parse_from(data: bytes) -> Optional[Tuple[str, bytes]]:
    parts = data.split(b":", 2)
    if len(parts) != 3 or parts[0] != b"FROM":
        return None
    try:
        sender_user = parts[1].decode(ENCODING)
    except UnicodeDecodeError:
        return None
    return sender_user, parts[2]
