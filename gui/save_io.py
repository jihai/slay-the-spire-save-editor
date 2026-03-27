"""Save file I/O: discovery, load, and save."""

from __future__ import annotations

import hashlib
import json
import shutil
import time
from pathlib import Path

from sts_save_editor import decode_save, encode_save

from gui.game_config import GameConfig, sts1_config

# Default Steam save directory on macOS
DEFAULT_SAVE_DIR = Path.home() / (
    "Library/Application Support/Steam/steamapps/common"
    "/SlayTheSpire/SlayTheSpire.app/Contents/Resources/saves"
)

AUTOSAVE_GLOB = "*.autosave"


def find_save_files(
    save_dir: Path | None = None, config: GameConfig | None = None
) -> list[Path]:
    """Return save files in the directory, sorted by name.

    Uses config.save_dir and config.file_glob when a config is provided.
    Falls back to STS1 defaults for backward compatibility.
    """
    if config is not None:
        directory = save_dir or config.save_dir
        glob = config.file_glob
    else:
        directory = save_dir or DEFAULT_SAVE_DIR
        glob = AUTOSAVE_GLOB
    if not directory.is_dir():
        return []
    return sorted(directory.glob(glob))


def load_save(path: Path, config: GameConfig | None = None) -> dict:
    """Read and decode a save file, returning the JSON dict.

    For STS1 (encrypted): XOR + Base64 decode.
    For STS2 (not encrypted): plain JSON read.
    """
    raw = path.read_text(encoding="utf-8")
    if config is not None and not config.encrypted:
        return json.loads(raw)
    return decode_save(raw)


def write_save(path: Path, data: dict, config: GameConfig | None = None) -> None:
    """Encode and write save data to a file.

    For STS1 (encrypted): XOR + Base64 encode.
    For STS2 (not encrypted): plain JSON write + sync to Steam cache.
    """
    if config is not None and not config.encrypted:
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        # Remove backup so the game respects our edited save
        # (STS2 checks backup first; if it exists, the game uses it over our edit)
        backup = path.with_name(path.name + ".backup")
        if backup.exists():
            backup.unlink()
        # Sync to old Steam location so the game picks up the edit immediately
        if config.steam_user_id:
            _sync_to_steam_cache(path, config.steam_user_id)
    else:
        encoded = encode_save(data)
        path.write_text(encoded, encoding="utf-8")


def _sync_to_steam_cache(path: Path, steam_user_id: str) -> None:
    """Copy the saved file to the old Steam location and update remotecache.vdf.

    The game loads from the short-id Steam location first. This ensures edits
    take effect immediately without a resume/save/reload cycle.

    Best-effort: failures here do not prevent the primary save from succeeding.
    """
    from gui.steam import (
        remotecache_vdf_path,
        sts2_old_save_dir,
        update_remotecache_sha,
    )

    try:
        # 1. Compute SHA-1 and size of the written file
        file_bytes = path.read_bytes()
        sha = hashlib.sha1(file_bytes).hexdigest()
        size = len(file_bytes)
        ts = int(time.time())

        # 2. Copy to old Steam location
        old_dir = sts2_old_save_dir(steam_user_id)
        if old_dir.is_dir():
            old_path = old_dir / path.name
            shutil.copy2(path, old_path)

            # 3. Update remotecache.vdf
            # The file key is relative to the "remote" dir,
            # e.g. "profile1/saves/current_run.save"
            file_key = f"profile1/saves/{path.name}"
            vdf = remotecache_vdf_path(steam_user_id)
            update_remotecache_sha(vdf, file_key, sha, size, ts)
    except Exception:
        # Best-effort: don't let sync failure block the primary save
        pass
