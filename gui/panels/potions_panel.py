"""Potions panel: edit potion slots with combo box selectors."""

from __future__ import annotations

import logging

from PySide6.QtCore import QSize, Qt, QTimer
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QVBoxLayout,
    QWidget,
)

from gui.game_data import GameData, PotionInfo
from gui.save_model import SaveModel

logger = logging.getLogger(__name__)

EMPTY_POTION = "Potion Slot"
ICON_SIZE = QSize(24, 24)


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

        # Build sorted potion list for combo boxes
        self._sorted_potions: list[PotionInfo] = sorted(
            game_data.potions, key=lambda p: p.name
        )

        self._layout = QVBoxLayout(self)
        self._group = QGroupBox("Potions")
        self._form = QFormLayout(self._group)
        self._layout.addWidget(self._group)
        self._layout.addStretch()

        self._model.data_changed.connect(self._schedule_refresh)

    def _schedule_refresh(self) -> None:
        """Defer refresh to next event-loop iteration to avoid destroying
        a combo box while its signal handler is still on the call stack."""
        QTimer.singleShot(0, self._refresh)

    def _build_combo(self) -> QComboBox:
        combo = QComboBox()
        combo.setIconSize(ICON_SIZE)

        # Add empty slot first, storing its ID as UserRole
        combo.addItem(EMPTY_POTION)
        combo.setItemData(0, EMPTY_POTION, Qt.ItemDataRole.UserRole)

        # Add all potions with icons, tooltips, and IDs
        for potion in self._sorted_potions:
            icon = QIcon(potion.image_path) if potion.image_path else QIcon()
            combo.addItem(icon, potion.name)
            idx = combo.count() - 1
            combo.setItemData(idx, potion.id, Qt.ItemDataRole.UserRole)
            if potion.description:
                combo.setItemData(idx, potion.description, Qt.ItemDataRole.ToolTipRole)

        return combo

    def _find_combo_index_by_id(self, combo: QComboBox, potion_id: str) -> int:
        """Find combo item index whose UserRole data matches *potion_id*."""
        for j in range(combo.count()):
            if combo.itemData(j, Qt.ItemDataRole.UserRole) == potion_id:
                return j
        return -1

    def _refresh(self) -> None:
        self._updating = True
        try:
            # Remove old combos
            for combo in self._combos:
                combo.deleteLater()
            self._combos.clear()
            # Clear form layout
            while self._form.rowCount() > 0:
                self._form.removeRow(0)

            if not self._model.is_loaded:
                return

            potions = self._model.potions
            num_slots = max(len(potions), self._model.potion_slots)
            logger.debug("_refresh: %d slots, potions=%s", num_slots, potions)

            for i in range(num_slots):
                combo = self._build_combo()

                # Set current value by matching potion ID (UserRole data)
                current = potions[i] if i < len(potions) else EMPTY_POTION
                idx = self._find_combo_index_by_id(combo, current)
                if idx >= 0:
                    combo.setCurrentIndex(idx)
                else:
                    # Potion not in our list — add it as-is so it's preserved
                    logger.debug("Unknown potion ID %r in slot %d, adding as-is", current, i)
                    combo.addItem(current)
                    combo.setItemData(combo.count() - 1, current, Qt.ItemDataRole.UserRole)
                    combo.setCurrentIndex(combo.count() - 1)

                # Connect AFTER setting value to avoid spurious handler calls
                combo.currentIndexChanged.connect(
                    lambda _idx, si=i, cb=combo: self._on_potion_changed(si, cb)
                )
                self._form.addRow(f"Slot {i + 1}:", combo)
                self._combos.append(combo)
        finally:
            self._updating = False

    def _on_potion_changed(self, slot_index: int, combo: QComboBox) -> None:
        if self._updating:
            return
        potion_id = combo.currentData(Qt.ItemDataRole.UserRole)
        logger.debug("_on_potion_changed: slot=%d, potion_id=%r", slot_index, potion_id)
        self._model.set_potion(slot_index, potion_id)
