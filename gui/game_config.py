"""Game version configuration for STS1 and STS2."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from gui.steam import sts2_save_dir

_PROJECT_ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class GameConfig:
    """Version-specific constants for a Slay the Spire game."""

    game_version: int  # 1 or 2
    app_title: str
    save_dir: Path
    file_glob: str  # "*.autosave" or "*.save"
    file_filter: str  # for QFileDialog
    game_resources_dir: Path
    encrypted: bool  # True for STS1 (XOR+Base64), False for STS2
    has_card_upgrades: bool  # True for STS1, False for STS2


def sts1_config() -> GameConfig:
    return GameConfig(
        game_version=1,
        app_title="Slay the Spire Save Editor",
        save_dir=Path.home()
        / (
            "Library/Application Support/Steam/steamapps/common"
            "/SlayTheSpire/SlayTheSpire.app/Contents/Resources/saves"
        ),
        file_glob="*.autosave",
        file_filter="Save Files (*.autosave);;All Files (*)",
        game_resources_dir=_PROJECT_ROOT / "game_resources",
        encrypted=True,
        has_card_upgrades=True,
    )


def sts2_config(steam_user_id: str | None = None) -> GameConfig:
    if steam_user_id:
        save_dir = sts2_save_dir(steam_user_id)
    else:
        save_dir = Path.home() / "Library/Application Support/Steam/userdata"
    return GameConfig(
        game_version=2,
        app_title="Slay the Spire 2 Save Editor",
        save_dir=save_dir,
        file_glob="*.save",
        file_filter="Save Files (*.save);;All Files (*)",
        game_resources_dir=_PROJECT_ROOT / "game_resources_sts2",
        encrypted=False,
        has_card_upgrades=True,
    )
