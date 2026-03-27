"""Steam user ID detection and mapping for STS2 save files."""

from __future__ import annotations

import re
from pathlib import Path

STS2_APP_ID = "2868840"

# Long Steam ID = Short Steam ID + this offset
STEAM_ID_OFFSET = 76561197960265728

# New save location (STS2 moved here from Steam userdata)
STS2_NEW_BASE_DIR = Path.home() / "Library/Application Support/SlayTheSpire2/steam"
STS2_NEW_SAVE_SUBPATH = Path("profile1") / "saves"

# Old save location (kept for reference / constants only)
STEAM_USERDATA_DIR = Path.home() / "Library/Application Support/Steam/userdata"
STS2_OLD_SAVE_SUBPATH = Path(STS2_APP_ID) / "remote" / "profile1" / "saves"

# Steam login users config (maps long IDs to persona names)
STEAM_LOGIN_USERS_VDF = (
    Path.home() / "Library/Application Support/Steam/config/loginusers.vdf"
)


def short_to_long_steam_id(short_id: str) -> str:
    """Convert a short Steam ID (account ID) to a long Steam ID (Steam64)."""
    return str(int(short_id) + STEAM_ID_OFFSET)


def long_to_short_steam_id(long_id: str) -> str:
    """Convert a long Steam ID (Steam64) to a short Steam ID (account ID)."""
    return str(int(long_id) - STEAM_ID_OFFSET)


def parse_login_users_vdf(
    vdf_path: Path | None = None,
) -> dict[str, str]:
    """Parse Steam's loginusers.vdf, returning {long_id: PersonaName}.

    The VDF format is a simple nested key-value structure. We extract the
    top-level user IDs and their PersonaName values.
    """
    path = vdf_path or STEAM_LOGIN_USERS_VDF
    if not path.is_file():
        return {}
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return {}

    result: dict[str, str] = {}
    current_id: str | None = None
    for line in text.splitlines():
        stripped = line.strip().strip('"')
        # Match a top-level Steam ID (all digits, 17 digits for Steam64)
        if stripped.isdigit() and len(stripped) >= 10:
            current_id = stripped
        # Match PersonaName within a user block
        elif current_id:
            m = re.match(r'"PersonaName"\s+"(.+)"', line.strip())
            if m:
                result[current_id] = m.group(1)
                current_id = None
    return result


def get_steam_display_names(
    vdf_path: Path | None = None,
) -> dict[str, str]:
    """Return {short_id: PersonaName} for all known Steam users."""
    long_map = parse_login_users_vdf(vdf_path)
    return {long_to_short_steam_id(lid): name for lid, name in long_map.items()}


def detect_steam_users(
    new_base_dir: Path | None = None,
) -> list[str]:
    """Return short Steam user IDs that have STS2 save directories, sorted.

    Scans the new STS2 save location for directories named with long Steam IDs,
    converts them to short IDs for the UI.
    """
    base = new_base_dir or STS2_NEW_BASE_DIR
    if not base.is_dir():
        return []
    users = []
    for entry in base.iterdir():
        if not entry.is_dir() or not entry.name.isdigit():
            continue
        saves_dir = entry / STS2_NEW_SAVE_SUBPATH
        if saves_dir.is_dir():
            users.append(long_to_short_steam_id(entry.name))
    return sorted(users)


def sts2_save_dir(
    steam_user_id: str, new_base_dir: Path | None = None
) -> Path:
    """Return the STS2 saves directory for a given short Steam user ID."""
    base = new_base_dir or STS2_NEW_BASE_DIR
    long_id = short_to_long_steam_id(steam_user_id)
    return base / long_id / STS2_NEW_SAVE_SUBPATH


def sts2_old_save_dir(
    steam_user_id: str, userdata_dir: Path | None = None
) -> Path:
    """Return the old Steam Cloud save directory for a given short Steam user ID."""
    base = userdata_dir or STEAM_USERDATA_DIR
    return base / steam_user_id / STS2_OLD_SAVE_SUBPATH


def remotecache_vdf_path(
    steam_user_id: str, userdata_dir: Path | None = None
) -> Path:
    """Return the path to remotecache.vdf for a given short Steam user ID."""
    base = userdata_dir or STEAM_USERDATA_DIR
    return base / steam_user_id / STS2_APP_ID / "remotecache.vdf"


def update_remotecache_sha(
    vdf_path: Path,
    file_key: str,
    sha: str,
    size: int,
    timestamp: int,
) -> bool:
    """Update an entry in remotecache.vdf with new SHA, size, and timestamps.

    Args:
        vdf_path: Path to the remotecache.vdf file.
        file_key: The file key in the VDF (e.g. "profile1/saves/current_run.save").
        sha: The SHA-1 hex digest of the file.
        size: The file size in bytes.
        timestamp: Unix timestamp for localtime and time fields.

    Returns:
        True if the entry was found and updated, False otherwise.
    """
    if not vdf_path.is_file():
        return False
    try:
        text = vdf_path.read_text(encoding="utf-8")
    except OSError:
        return False

    # Find the block for this file_key.
    # Pattern: "file_key"\n\t{\n\t\t"key"\t\t"value"\n...\n\t}
    escaped_key = re.escape(file_key)
    block_pattern = re.compile(
        rf'(\t"{escaped_key}"\s*\{{)(.*?)(\t\}})',
        re.DOTALL,
    )
    match = block_pattern.search(text)
    if not match:
        return False

    block = match.group(2)
    ts = str(timestamp)
    sz = str(size)

    def _replace_field(block_text: str, field: str, value: str) -> str:
        return re.sub(
            rf'("{field}"\s+")[^"]*(")',
            rf"\g<1>{value}\2",
            block_text,
        )

    block = _replace_field(block, "sha", sha)
    block = _replace_field(block, "size", sz)
    block = _replace_field(block, "localtime", ts)
    block = _replace_field(block, "time", ts)

    updated = text[: match.start(2)] + block + text[match.end(2) :]
    vdf_path.write_text(updated, encoding="utf-8")
    return True
