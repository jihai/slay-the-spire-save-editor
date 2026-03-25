"""Steam user ID detection for STS2 save files."""

from __future__ import annotations

from pathlib import Path

STS2_APP_ID = "2868840"
STEAM_USERDATA_DIR = Path.home() / "Library/Application Support/Steam/userdata"
STS2_SAVE_SUBPATH = Path(STS2_APP_ID) / "remote" / "profile1" / "saves"


def detect_steam_users(
    userdata_dir: Path | None = None,
) -> list[str]:
    """Return Steam user IDs that have STS2 save directories, sorted."""
    base = userdata_dir or STEAM_USERDATA_DIR
    if not base.is_dir():
        return []
    users = []
    for entry in base.iterdir():
        if not entry.is_dir() or not entry.name.isdigit():
            continue
        saves_dir = entry / STS2_SAVE_SUBPATH
        if saves_dir.is_dir():
            users.append(entry.name)
    return sorted(users)


def sts2_save_dir(steam_user_id: str, userdata_dir: Path | None = None) -> Path:
    """Return the STS2 saves directory for a given Steam user ID."""
    base = userdata_dir or STEAM_USERDATA_DIR
    return base / steam_user_id / STS2_SAVE_SUBPATH
