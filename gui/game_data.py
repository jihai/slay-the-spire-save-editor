"""Load and query game resource data (cards, potions, relics) from CSV files."""

from __future__ import annotations

import csv
from dataclasses import dataclass
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


@dataclass(frozen=True)
class CardInfo:
    id: str
    name: str
    color: str
    card_type: str
    rarity: str


@dataclass(frozen=True)
class PotionInfo:
    id: str
    name: str


@dataclass(frozen=True)
class RelicInfo:
    id: str
    name: str
    tier: str


def _load_csv(filename: str) -> list[dict[str, str]]:
    path = GAME_RESOURCES_DIR / filename
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_cards(path: Path | None = None) -> list[CardInfo]:
    rows = _load_csv("cards.csv") if path is None else _load_csv_path(path)
    return [
        CardInfo(
            id=row[CARD_ID_COL],
            name=row[CARD_NAME_COL],
            color=row[CARD_COLOR_COL],
            card_type=row[CARD_TYPE_COL],
            rarity=row[CARD_RARITY_COL],
        )
        for row in rows
    ]


def load_potions(path: Path | None = None) -> list[PotionInfo]:
    rows = _load_csv("potions.csv") if path is None else _load_csv_path(path)
    return [
        PotionInfo(
            id=row[POTION_ID_COL],
            name=row[POTION_NAME_COL],
        )
        for row in rows
    ]


def load_relics(path: Path | None = None) -> list[RelicInfo]:
    rows = _load_csv("relics.csv") if path is None else _load_csv_path(path)
    return [
        RelicInfo(
            id=row[RELIC_ID_COL],
            name=row[RELIC_NAME_COL],
            tier=row[RELIC_TIER_COL],
        )
        for row in rows
    ]


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
        self.potions_by_name: dict[str, PotionInfo] = {p.name: p for p in self.potions}
        self.relics_by_name: dict[str, RelicInfo] = {r.name: r for r in self.relics}

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
