"""Potions panel: edit potion slots with combo box selectors."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QVBoxLayout,
    QWidget,
)

from gui.game_data import GameData
from gui.save_model import SaveModel

EMPTY_POTION = "Potion Slot"


class PotionsPanel(QWidget):
    """One combo box per potion slot, populated from game data."""

    def __init__(
        self, model: SaveModel, game_data: GameData, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self._model = model
        self._game_data = game_data
        self._updating = False
        self._combos: list[QComboBox] = []

        # Build the potion name list: empty slot + all potions sorted by name
        self._potion_names = [EMPTY_POTION] + sorted(
            [p.name for p in game_data.potions]
        )

        self._layout = QVBoxLayout(self)
        self._group = QGroupBox("Potions")
        self._form = QFormLayout(self._group)
        self._layout.addWidget(self._group)
        self._layout.addStretch()

        self._model.data_changed.connect(self._refresh)

    def _refresh(self) -> None:
        self._updating = True

        # Remove old combos
        for combo in self._combos:
            combo.deleteLater()
        self._combos.clear()
        # Clear form layout
        while self._form.rowCount() > 0:
            self._form.removeRow(0)

        if not self._model.is_loaded:
            self._updating = False
            return

        potions = self._model.potions
        num_slots = max(len(potions), self._model.potion_slots)

        for i in range(num_slots):
            combo = QComboBox()
            combo.addItems(self._potion_names)

            # Set current value
            current = potions[i] if i < len(potions) else EMPTY_POTION
            idx = combo.findText(current)
            if idx >= 0:
                combo.setCurrentIndex(idx)
            else:
                # Potion not in our list — add it as-is
                combo.addItem(current)
                combo.setCurrentIndex(combo.count() - 1)

            slot_index = i  # capture for closure
            combo.currentTextChanged.connect(
                lambda text, si=slot_index: self._on_potion_changed(si, text)
            )
            self._form.addRow(f"Slot {i + 1}:", combo)
            self._combos.append(combo)

        self._updating = False

    def _on_potion_changed(self, slot_index: int, text: str) -> None:
        if self._updating:
            return
        self._model.set_potion(slot_index, text)
