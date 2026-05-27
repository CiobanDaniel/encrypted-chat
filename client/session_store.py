"""In-memory chat/session state isolated from UI concerns."""

from __future__ import annotations

from typing import Dict, List, Optional


class SessionStore:
    def __init__(self) -> None:
        self._active_sessions: Dict[str, bytes] = {}
        self._messages: Dict[str, List[str]] = {}
        self._peer_public_keys: Dict[str, bytes] = {}

    def ensure_contact(self, username: str) -> None:
        if username not in self._messages:
            self._messages[username] = []

    def has_session(self, username: str) -> bool:
        return username in self._active_sessions

    def set_session_key(self, username: str, aes_key: bytes) -> None:
        self._active_sessions[username] = aes_key

    def get_session_key(self, username: str) -> Optional[bytes]:
        return self._active_sessions.get(username)

    def add_message(self, username: str, message: str) -> None:
        self.ensure_contact(username)
        self._messages[username].append(message)

    def get_messages(self, username: str) -> List[str]:
        self.ensure_contact(username)
        return list(self._messages[username])

    def set_peer_public_key(self, username: str, public_key: bytes) -> None:
        self._peer_public_keys[username] = public_key

    def get_peer_public_key(self, username: str) -> Optional[bytes]:
        return self._peer_public_keys.get(username)

    def export_messages(self) -> Dict[str, List[str]]:
        return {user: list(messages) for user, messages in self._messages.items()}

    def import_messages(self, archive: Dict[str, List[str]]) -> None:
        self._messages = {}
        for user, messages in archive.items():
            if isinstance(user, str) and isinstance(messages, list):
                self._messages[user] = [str(m) for m in messages]

    def clear_sessions(self) -> None:
        self._active_sessions = {}
        self._peer_public_keys = {}
