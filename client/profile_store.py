"""Local profile data with account/device abstraction."""

from __future__ import annotations

import json
import secrets
from pathlib import Path
from typing import Dict


class ProfileStore:
    def __init__(self, app_name: str = "securechat") -> None:
        self.base_dir = Path.home() / f".{app_name}"
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.profile_path = self.base_dir / "profile.json"

    def _load_profile(self) -> Dict[str, str]:
        if not self.profile_path.exists():
            return {}
        try:
            raw = self.profile_path.read_text(encoding="utf-8")
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                return {str(k): str(v) for k, v in parsed.items()}
        except (OSError, json.JSONDecodeError):
            pass
        return {}

    def _save_profile(self, data: Dict[str, str]) -> None:
        self.profile_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def load_or_create_profile(self, username: str) -> Dict[str, str]:
        profile = self._load_profile()
        if not profile:
            profile = {
                "account_id": f"acct_{secrets.token_hex(8)}",
                "device_id": f"dev_{secrets.token_hex(8)}",
                "account_mode": "anonymous",
                "username": username,
                "linked_email": "",
                "linked_phone": "",
            }
            self._save_profile(profile)
            return profile

        # Keep user intent for current UI alias while preserving account/device IDs.
        profile["username"] = username
        if "account_mode" not in profile:
            profile["account_mode"] = "anonymous"
        if "linked_email" not in profile:
            profile["linked_email"] = ""
        if "linked_phone" not in profile:
            profile["linked_phone"] = ""
        self._save_profile(profile)
        return profile

    def export_profile(self) -> Dict[str, str]:
        return self._load_profile()

    def import_profile(self, profile: Dict[str, str]) -> None:
        expected = {
            "account_id",
            "device_id",
            "account_mode",
            "username",
            "linked_email",
            "linked_phone",
        }
        sanitized = {k: str(v) for k, v in profile.items() if k in expected}
        self._save_profile(sanitized)

    def update_account_link(self, account_id: str, account_mode: str = "linked") -> Dict[str, str]:
        profile = self._load_profile()
        if not profile:
            return {}
        profile["account_id"] = account_id
        profile["account_mode"] = account_mode
        self._save_profile(profile)
        return profile
