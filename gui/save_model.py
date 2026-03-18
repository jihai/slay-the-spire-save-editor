"""SaveModel: QObject wrapper around the raw save JSON dict with change tracking."""

from __future__ import annotations

from PySide6.QtCore import QObject, Signal

# Starter relics used to detect the character
CHARACTER_RELICS = {
    "Burning Blood": "Ironclad",
    "Ring of the Snake": "Silent",
    "Cracked Core": "Defect",
    "PureWater": "Watcher",
}


class SaveModel(QObject):
    """Wraps the raw save file dict, exposing typed properties with change signals.

    Fields not exposed here pass through untouched when saving.
    """

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

    # -- Character detection --

    @property
    def character(self) -> str:
        for relic in self._data.get("relics", []):
            if relic in CHARACTER_RELICS:
                return CHARACTER_RELICS[relic]
        return "Unknown"

    # -- Typed property helpers --

    def _get_int(self, key: str, default: int = 0) -> int:
        return self._data.get(key, default)

    def _set_int(self, key: str, value: int) -> None:
        if self._data.get(key) != value:
            self._data[key] = value
            self._dirty = True
            self.data_changed.emit()

    # -- Exposed properties --

    @property
    def gold(self) -> int:
        return self._get_int("gold")

    @gold.setter
    def gold(self, value: int) -> None:
        self._set_int("gold", value)

    @property
    def current_health(self) -> int:
        return self._get_int("current_health")

    @current_health.setter
    def current_health(self, value: int) -> None:
        self._set_int("current_health", value)

    @property
    def max_health(self) -> int:
        return self._get_int("max_health")

    @max_health.setter
    def max_health(self, value: int) -> None:
        self._set_int("max_health", value)

    @property
    def act_num(self) -> int:
        return self._get_int("act_num")

    @act_num.setter
    def act_num(self, value: int) -> None:
        self._set_int("act_num", value)

    @property
    def floor_num(self) -> int:
        return self._get_int("floor_num")

    @floor_num.setter
    def floor_num(self, value: int) -> None:
        self._set_int("floor_num", value)

    @property
    def ascension_level(self) -> int:
        return self._get_int("ascension_level")

    @ascension_level.setter
    def ascension_level(self, value: int) -> None:
        self._set_int("ascension_level", value)

    @property
    def potion_slots(self) -> int:
        return self._get_int("potion_slots", 3)

    @potion_slots.setter
    def potion_slots(self, value: int) -> None:
        self._set_int("potion_slots", value)

    # -- List properties --

    @property
    def cards(self) -> list[dict]:
        return self._data.get("cards", [])

    @cards.setter
    def cards(self, value: list[dict]) -> None:
        self._data["cards"] = value
        self._dirty = True
        self.data_changed.emit()

    def add_card(self, card_id: str, upgrades: int = 0) -> None:
        self.cards.append({"id": card_id, "upgrades": upgrades, "misc": 0})
        self._dirty = True
        self.data_changed.emit()

    def remove_card(self, index: int) -> None:
        cards = self.cards
        if 0 <= index < len(cards):
            cards.pop(index)
            self._dirty = True
            self.data_changed.emit()

    def remove_cards(self, indices: list[int]) -> None:
        """Remove multiple cards by index in a single operation."""
        cards = self.cards
        for i in sorted(indices, reverse=True):
            if 0 <= i < len(cards):
                cards.pop(i)
        self._dirty = True
        self.data_changed.emit()

    def set_card_upgrades(self, index: int, upgrades: int) -> None:
        cards = self.cards
        if 0 <= index < len(cards):
            cards[index]["upgrades"] = upgrades
            self._dirty = True
            self.data_changed.emit()

    @property
    def potions(self) -> list[str]:
        return self._data.get("potions", [])

    @potions.setter
    def potions(self, value: list[str]) -> None:
        self._data["potions"] = value
        self._dirty = True
        self.data_changed.emit()

    def set_potion(self, index: int, potion_id: str) -> None:
        potions = self.potions
        if 0 <= index < len(potions):
            potions[index] = potion_id
            self._dirty = True
            self.data_changed.emit()

    @property
    def relics(self) -> list[str]:
        return self._data.get("relics", [])

    @relics.setter
    def relics(self, value: list[str]) -> None:
        self._data["relics"] = value
        self._dirty = True
        self.data_changed.emit()

    def add_relic(self, relic_name: str) -> None:
        self.relics.append(relic_name)
        self._dirty = True
        self.data_changed.emit()

    def remove_relic(self, index: int) -> None:
        relics = self.relics
        if 0 <= index < len(relics):
            relics.pop(index)
            self._dirty = True
            self.data_changed.emit()
