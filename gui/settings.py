"""Persistent application settings (JSON-backed)."""

from __future__ import annotations

import json
from pathlib import Path

_SETTINGS_DIR = Path.home() / ".config" / "sts-save-editor"
_SETTINGS_FILE = _SETTINGS_DIR / "settings.json"


def _load() -> dict:
    if _SETTINGS_FILE.is_file():
        try:
            return json.loads(_SETTINGS_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def _save(data: dict) -> None:
    _SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
    _SETTINGS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def get_steam_user_id() -> str | None:
    """Return the saved Steam user ID, or None if not set."""
    return _load().get("steam_user_id")


def set_steam_user_id(user_id: str) -> None:
    """Persist the chosen Steam user ID."""
    data = _load()
    data["steam_user_id"] = user_id
    _save(data)
