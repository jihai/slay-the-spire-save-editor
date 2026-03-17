"""Load and query game resource data (cards, potions, relics) from CSV files."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from pathlib import Path

# Column names used to look up items. Change these if the CSV schema changes.
CARD_ID_COL = "name"
CARD_NAME_COL = "name"
CARD_COLOR_COL = "color"
CARD_TYPE_COL = "type"
CARD_RARITY_COL = "rarity"

POTION_ID_COL = "name"
POTION_NAME_COL = "name"

RELIC_ID_COL = "name"
RELIC_NAME_COL = "name"
RELIC_TIER_COL = "tier"

GAME_RESOURCES_DIR = Path(__file__).resolve().parent.parent / "game_resources"
IMAGES_DIR = GAME_RESOURCES_DIR / "images"
WIKI_DATA_PATH = GAME_RESOURCES_DIR / "wiki_data.json"


@dataclass(frozen=True)
class CardInfo:
    id: str
    name: str
    color: str
    card_type: str
    rarity: str
    description: str = ""
    image_path: str = ""


@dataclass(frozen=True)
class PotionInfo:
    id: str
    name: str
    description: str = ""
    image_path: str = ""


@dataclass(frozen=True)
class RelicInfo:
    id: str
    name: str
    tier: str
    description: str = ""
    flavor: str = ""
    image_path: str = ""


def _load_csv(filename: str) -> list[dict[str, str]]:
    path = GAME_RESOURCES_DIR / filename
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _load_wiki_data() -> dict:
    """Load wiki_data.json if available, returning empty dict on failure."""
    if not WIKI_DATA_PATH.exists():
        return {}
    try:
        return json.loads(WIKI_DATA_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _resolve_image(relative: str) -> str:
    """Resolve a relative image path to absolute, returning '' if not found."""
    if not relative:
        return ""
    full = IMAGES_DIR / relative
    return str(full) if full.exists() else ""


def load_cards(path: Path | None = None) -> list[CardInfo]:
    rows = _load_csv("cards.csv") if path is None else _load_csv_path(path)
    wiki = _load_wiki_data().get("cards", {})
    # Build case-insensitive lookup for wiki data
    wiki_lower = {k.lower(): v for k, v in wiki.items()}

    result = []
    for row in rows:
        name = row[CARD_NAME_COL]
        raw_id = row["id"]
        # Try matching wiki by display name first, then by CSV id
        w = wiki_lower.get(name.lower()) or wiki_lower.get(raw_id.lower(), {})
        result.append(
            CardInfo(
                id=raw_id,  # Always use raw CSV id for save-file lookups
                name=name,
                color=row[CARD_COLOR_COL],
                card_type=row[CARD_TYPE_COL],
                rarity=row[CARD_RARITY_COL],
                description=w.get("description", ""),
                image_path=_resolve_image(w.get("image", "")),
            )
        )
    return result


def load_potions(path: Path | None = None) -> list[PotionInfo]:
    rows = _load_csv("potions.csv") if path is None else _load_csv_path(path)
    wiki = _load_wiki_data().get("potions", {})
    wiki_lower = {k.lower(): v for k, v in wiki.items()}

    result = []
    for row in rows:
        name = row[POTION_NAME_COL]
        raw_id = row["id"]
        w = wiki_lower.get(name.lower()) or wiki_lower.get(raw_id.lower(), {})
        result.append(
            PotionInfo(
                id=raw_id,  # Always use raw CSV id for save-file lookups
                name=name,
                description=w.get("description", ""),
                image_path=_resolve_image(w.get("image", "")),
            )
        )
    return result


def load_relics(path: Path | None = None) -> list[RelicInfo]:
    rows = _load_csv("relics.csv") if path is None else _load_csv_path(path)
    wiki = _load_wiki_data().get("relics", {})
    wiki_lower = {k.lower(): v for k, v in wiki.items()}

    result = []
    for row in rows:
        name = row[RELIC_NAME_COL]
        raw_id = row["id"]
        w = wiki_lower.get(name.lower()) or wiki_lower.get(raw_id.lower(), {})
        result.append(
            RelicInfo(
                id=raw_id,  # Always use raw CSV id for save-file lookups
                name=name,
                tier=row[RELIC_TIER_COL],
                description=w.get("description", ""),
                flavor=w.get("flavor", ""),
                image_path=_resolve_image(w.get("image", "")),
            )
        )
    return result


def _load_csv_path(path: Path) -> list[dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


class GameData:
    """Singleton-style container for all game resource data."""

    def __init__(self) -> None:
        self.cards = load_cards()
        self.potions = load_potions()
        self.relics = load_relics()

        self.cards_by_name: dict[str, CardInfo] = {c.name: c for c in self.cards}
        # Also index by CSV id column for save-file ID lookups (save files may
        # use internal IDs that differ from display names, e.g. "Apparition" vs "Ghostly")
        self.cards_by_id: dict[str, CardInfo] = {c.id: c for c in self.cards}
        self.potions_by_name: dict[str, PotionInfo] = {p.name: p for p in self.potions}
        self.potions_by_id: dict[str, PotionInfo] = {p.id: p for p in self.potions}
        self.relics_by_name: dict[str, RelicInfo] = {r.name: r for r in self.relics}
        self.relics_by_id: dict[str, RelicInfo] = {r.id: r for r in self.relics}

    def filter_cards(
        self,
        color: str | None = None,
        card_type: str | None = None,
        rarity: str | None = None,
    ) -> list[CardInfo]:
        result = self.cards
        if color:
            result = [c for c in result if c.color == color]
        if card_type:
            result = [c for c in result if c.card_type == card_type]
        if rarity:
            result = [c for c in result if c.rarity == rarity]
        return result

    def filter_relics(self, tier: str | None = None) -> list[RelicInfo]:
        if tier is None:
            return self.relics
        return [r for r in self.relics if r.tier == tier]

    def card_colors(self) -> list[str]:
        return sorted({c.color for c in self.cards})

    def card_types(self) -> list[str]:
        return sorted({c.card_type for c in self.cards})

    def card_rarities(self) -> list[str]:
        return sorted({c.rarity for c in self.cards})

    def relic_tiers(self) -> list[str]:
        return sorted({r.tier for r in self.relics})
