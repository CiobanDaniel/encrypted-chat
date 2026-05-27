"""Encrypted backup helpers for profile, keys, trust, and chat archive."""

from __future__ import annotations

import base64
import json
import os
from typing import Any, Dict

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


def _derive_key(passphrase: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=200_000,
    )
    return kdf.derive(passphrase.encode("utf-8"))


def build_encrypted_backup(passphrase: str, payload: Dict[str, Any]) -> bytes:
    salt = os.urandom(16)
    nonce = os.urandom(12)
    key = _derive_key(passphrase, salt)
    plaintext = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    ciphertext = AESGCM(key).encrypt(nonce, plaintext, None)
    envelope = {
        "version": 1,
        "kdf": "PBKDF2-SHA256",
        "iterations": 200000,
        "salt_b64": base64.b64encode(salt).decode("ascii"),
        "nonce_b64": base64.b64encode(nonce).decode("ascii"),
        "ciphertext_b64": base64.b64encode(ciphertext).decode("ascii"),
    }
    return json.dumps(envelope, indent=2).encode("utf-8")


def load_encrypted_backup(passphrase: str, blob: bytes) -> Dict[str, Any]:
    parsed = json.loads(blob.decode("utf-8"))
    salt = base64.b64decode(parsed["salt_b64"])
    nonce = base64.b64decode(parsed["nonce_b64"])
    ciphertext = base64.b64decode(parsed["ciphertext_b64"])
    key = _derive_key(passphrase, salt)
    plaintext = AESGCM(key).decrypt(nonce, ciphertext, None)
    data = json.loads(plaintext.decode("utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Invalid backup content")
    return data
