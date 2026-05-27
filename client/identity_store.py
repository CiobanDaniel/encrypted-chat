"""Persistent identity/trust storage for the chat client."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, Optional, Tuple

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec


class IdentityStore:
    def __init__(self, app_name: str = "securechat") -> None:
        self.base_dir = Path.home() / f".{app_name}"
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.identity_key_path = self.base_dir / "identity_key.pem"
        self.trust_path = self.base_dir / "trust_store.json"

    def load_or_create_identity_keypair(self) -> Tuple[ec.EllipticCurvePrivateKey, bytes]:
        if self.identity_key_path.exists():
            private_bytes = self.identity_key_path.read_bytes()
            private_key = serialization.load_pem_private_key(private_bytes, password=None)
        else:
            private_key = ec.generate_private_key(ec.SECP384R1())
            private_bytes = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            )
            self.identity_key_path.write_bytes(private_bytes)
            # Best-effort on POSIX; harmless on Windows.
            try:
                os.chmod(self.identity_key_path, 0o600)
            except OSError:
                pass

        public_bytes = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        return private_key, public_bytes

    def _load_trust_store(self) -> Dict[str, str]:
        if not self.trust_path.exists():
            return {}
        try:
            raw = self.trust_path.read_text(encoding="utf-8")
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                return {str(k): str(v) for k, v in parsed.items()}
        except (OSError, json.JSONDecodeError):
            pass
        return {}

    def _save_trust_store(self, data: Dict[str, str]) -> None:
        self.trust_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def get_trusted_fingerprint(self, contact: str) -> Optional[str]:
        return self._load_trust_store().get(contact)

    def set_trusted_fingerprint(self, contact: str, fingerprint: str) -> None:
        data = self._load_trust_store()
        data[contact] = fingerprint
        self._save_trust_store(data)

    def clear_trusted_fingerprint(self, contact: str) -> bool:
        data = self._load_trust_store()
        if contact not in data:
            return False
        del data[contact]
        self._save_trust_store(data)
        return True

    def export_state(self) -> Dict[str, object]:
        private_pem = ""
        if self.identity_key_path.exists():
            private_pem = self.identity_key_path.read_text(encoding="utf-8")
        return {
            "identity_private_key_pem": private_pem,
            "trust_store": self._load_trust_store(),
        }

    def import_state(self, state: Dict[str, object]) -> None:
        private_pem = str(state.get("identity_private_key_pem", ""))
        if private_pem.strip():
            self.identity_key_path.write_text(private_pem, encoding="utf-8")
        trust_store = state.get("trust_store", {})
        if isinstance(trust_store, dict):
            sanitized = {str(k): str(v) for k, v in trust_store.items()}
            self._save_trust_store(sanitized)
