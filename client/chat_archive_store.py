"""Persistent chat archive used for local restore/backup."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List


class ChatArchiveStore:
    def __init__(self, app_name: str = "securechat") -> None:
        self.base_dir = Path.home() / f".{app_name}"
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.archive_path = self.base_dir / "chat_archive.json"

    def load_archive(self) -> Dict[str, List[str]]:
        if not self.archive_path.exists():
            return {}
        try:
            raw = self.archive_path.read_text(encoding="utf-8")
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                result: Dict[str, List[str]] = {}
                for user, messages in parsed.items():
                    if isinstance(user, str) and isinstance(messages, list):
                        result[user] = [str(m) for m in messages]
                return result
        except (OSError, json.JSONDecodeError):
            pass
        return {}

    def save_archive(self, messages: Dict[str, List[str]]) -> None:
        self.archive_path.write_text(json.dumps(messages, indent=2), encoding="utf-8")
