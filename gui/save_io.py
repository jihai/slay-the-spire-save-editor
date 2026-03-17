"""Save file I/O: discovery, load, save, and backup."""

from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

from sts_save_editor import decode_save, encode_save

# Default Steam save directory on macOS
DEFAULT_SAVE_DIR = Path.home() / (
    "Library/Application Support/Steam/steamapps/common"
    "/SlayTheSpire/SlayTheSpire.app/Contents/Resources/saves"
)

AUTOSAVE_GLOB = "*.autosave"


def find_save_files(save_dir: Path | None = None) -> list[Path]:
    """Return all .autosave files in the save directory, sorted by name."""
    directory = save_dir or DEFAULT_SAVE_DIR
    if not directory.is_dir():
        return []
    return sorted(directory.glob(AUTOSAVE_GLOB))


def load_save(path: Path) -> dict:
    """Read and decode a save file, returning the JSON dict."""
    raw = path.read_text(encoding="utf-8")
    return decode_save(raw)


def write_save(path: Path, data: dict) -> None:
    """Encode and write save data to a file."""
    encoded = encode_save(data)
    path.write_text(encoded, encoding="utf-8")


def create_backup(path: Path) -> Path:
    """Create a timestamped backup of a save file. Returns the backup path."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = path.with_suffix(f".bak.{timestamp}")
    shutil.copy2(path, backup_path)
    return backup_path
