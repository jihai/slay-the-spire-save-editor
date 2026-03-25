"""SaveModelSTS2: QObject wrapper for Slay the Spire 2 save files.

STS2 saves are nested: player data lives under players[0], unlike STS1's flat dict.
This model exposes the same property API as SaveModel so panels work with either.
"""

from __future__ import annotations

from PySide6.QtCore import QObject, Signal


class SaveModelSTS2(QObject):
    """Wraps an STS2 save dict, exposing typed properties compatible with panels."""

    data_changed = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._data: dict = {}
        self._dirty = False
        self._file_path: str | None = None

    # -- Loading / raw access --

    def load(self, data: dict, file_path: str | None = None) -> None:
        self._data = data
        self._file_path = file_path
        self._dirty = False
        self.data_changed.emit()

    @property
    def raw(self) -> dict:
        return self._data

    @property
    def is_loaded(self) -> bool:
        return bool(self._data)

    @property
    def file_path(self) -> str | None:
        return self._file_path

    @file_path.setter
    def file_path(self, value: str | None) -> None:
        self._file_path = value

    @property
    def dirty(self) -> bool:
        return self._dirty

    def mark_clean(self) -> None:
        self._dirty = False
        self.data_changed.emit()

    # -- Player accessor --

    @property
    def _player(self) -> dict:
        """Shortcut to players[0]."""
        return self._data.get("players", [{}])[0]

    # -- Character detection --

    @property
    def character(self) -> str:
        raw_id = self._player.get("character_id", "")
        # Strip "CHARACTER." prefix: "CHARACTER.SILENT" -> "Silent"
        if raw_id.startswith("CHARACTER."):
            name = raw_id[len("CHARACTER."):]
            return name.replace("_", " ").title()
        return raw_id or "Unknown"

    # -- Typed property helpers --

    def _get_player_int(self, key: str, default: int = 0) -> int:
        return self._player.get(key, default)

    def _set_player_int(self, key: str, value: int) -> None:
        if self._player.get(key) != value:
            self._player[key] = value
            self._dirty = True
            self.data_changed.emit()

    def _get_root_int(self, key: str, default: int = 0) -> int:
        return self._data.get(key, default)

    def _set_root_int(self, key: str, value: int) -> None:
        if self._data.get(key) != value:
            self._data[key] = value
            self._dirty = True
            self.data_changed.emit()

    # -- Exposed properties (same names as SaveModel for panel compatibility) --

    @property
    def gold(self) -> int:
        return self._get_player_int("gold")

    @gold.setter
    def gold(self, value: int) -> None:
        self._set_player_int("gold", value)

    @property
    def current_health(self) -> int:
        return self._get_player_int("current_hp")

    @current_health.setter
    def current_health(self, value: int) -> None:
        self._set_player_int("current_hp", value)

    @property
    def max_health(self) -> int:
        return self._get_player_int("max_hp")

    @max_health.setter
    def max_health(self, value: int) -> None:
        self._set_player_int("max_hp", value)

    @property
    def act_num(self) -> int:
        return self._get_root_int("current_act_index")

    @act_num.setter
    def act_num(self, value: int) -> None:
        self._set_root_int("current_act_index", value)

    @property
    def floor_num(self) -> int:
        # STS2 doesn't have a direct floor_num; use 0 as default
        return self._get_root_int("floor_num", 0)

    @floor_num.setter
    def floor_num(self, value: int) -> None:
        self._set_root_int("floor_num", value)

    @property
    def ascension_level(self) -> int:
        return self._get_root_int("ascension")

    @ascension_level.setter
    def ascension_level(self, value: int) -> None:
        self._set_root_int("ascension", value)

    @property
    def potion_slots(self) -> int:
        return self._get_player_int("max_potion_slot_count", 3)

    @potion_slots.setter
    def potion_slots(self, value: int) -> None:
        self._set_player_int("max_potion_slot_count", value)

    # -- List properties --

    @property
    def cards(self) -> list[dict]:
        """Return deck as list of dicts: {"id": ..., "floor_added_to_deck": ...}."""
        return self._player.get("deck", [])

    @cards.setter
    def cards(self, value: list[dict]) -> None:
        self._player["deck"] = value
        self._dirty = True
        self.data_changed.emit()

    def add_card(self, card_id: str, upgrades: int = 0) -> None:
        """Add a card. The upgrades param is accepted for API compat but ignored."""
        self.cards.append({"id": card_id, "floor_added_to_deck": 0})
        self._dirty = True
        self.data_changed.emit()

    def remove_card(self, index: int) -> None:
        cards = self.cards
        if 0 <= index < len(cards):
            cards.pop(index)
            self._dirty = True
            self.data_changed.emit()

    def remove_cards(self, indices: list[int]) -> None:
        cards = self.cards
        for i in sorted(indices, reverse=True):
            if 0 <= i < len(cards):
                cards.pop(i)
        self._dirty = True
        self.data_changed.emit()

    def set_card_upgrades(self, index: int, upgrades: int) -> None:
        """No-op for STS2 — cards don't have an upgrades field."""
        pass

    @property
    def potions(self) -> list[str]:
        """Return potion IDs as flat list (panels expect list[str])."""
        raw = self._player.get("potions", [])
        return [p["id"] for p in raw]

    @potions.setter
    def potions(self, value: list[str]) -> None:
        self._player["potions"] = [
            {"id": pid, "slot_index": i} for i, pid in enumerate(value)
        ]
        self._dirty = True
        self.data_changed.emit()

    def set_potion(self, index: int, potion_id: str) -> None:
        raw = self._player.get("potions", [])
        if 0 <= index < len(raw):
            raw[index]["id"] = potion_id
            self._dirty = True
            self.data_changed.emit()

    @property
    def relics(self) -> list[str]:
        """Return relic IDs as flat list (panels expect list[str])."""
        raw = self._player.get("relics", [])
        return [r["id"] for r in raw]

    @relics.setter
    def relics(self, value: list[str]) -> None:
        self._player["relics"] = [
            {"id": rid, "floor_added_to_deck": 0} for rid in value
        ]
        self._dirty = True
        self.data_changed.emit()

    def add_relic(self, relic_id: str) -> None:
        self._player.get("relics", []).append(
            {"id": relic_id, "floor_added_to_deck": 0}
        )
        self._dirty = True
        self.data_changed.emit()

    def remove_relic(self, index: int) -> None:
        raw = self._player.get("relics", [])
        if 0 <= index < len(raw):
            raw.pop(index)
            self._dirty = True
            self.data_changed.emit()
