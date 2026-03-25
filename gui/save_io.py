"""Save file I/O: discovery, load, and save."""

from __future__ import annotations

import json
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
    For STS2 (not encrypted): plain JSON write.
    """
    if config is not None and not config.encrypted:
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    else:
        encoded = encode_save(data)
        path.write_text(encoded, encoding="utf-8")
