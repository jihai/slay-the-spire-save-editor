"""Stats panel: edit gold, HP, act, floor, and potion slots."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from gui.save_model import SaveModel


class StatsPanel(QWidget):
    """Form-based editor for numeric save file fields."""

    def __init__(self, model: SaveModel, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._model = model
        self._updating = False  # guard against signal loops

        layout = QVBoxLayout(self)

        # -- Info section --
        info_group = QGroupBox("Character Info")
        info_layout = QFormLayout(info_group)
        self._character_label = QLabel("—")
        info_layout.addRow("Character:", self._character_label)
        layout.addWidget(info_group)

        # -- Stats section --
        stats_group = QGroupBox("Stats")
        stats_layout = QFormLayout(stats_group)

        self._gold_spin = self._make_spin(0, 99999)
        stats_layout.addRow("Gold:", self._gold_spin)

        hp_row = QHBoxLayout()
        self._hp_spin = self._make_spin(0, 999)
        self._max_hp_spin = self._make_spin(1, 999)
        hp_row.addWidget(self._hp_spin)
        hp_row.addWidget(QLabel("/"))
        hp_row.addWidget(self._max_hp_spin)
        stats_layout.addRow("HP:", hp_row)

        layout.addWidget(stats_group)

        # -- Progression section --
        prog_group = QGroupBox("Progression")
        prog_layout = QFormLayout(prog_group)

        self._ascension_spin = self._make_spin(0, 20)
        prog_layout.addRow("Ascension:", self._ascension_spin)

        self._act_spin = self._make_spin(1, 4)
        prog_layout.addRow("Act:", self._act_spin)

        self._floor_spin = self._make_spin(0, 99)
        prog_layout.addRow("Floor:", self._floor_spin)

        self._potion_slots_spin = self._make_spin(0, 10)
        prog_layout.addRow("Potion Slots:", self._potion_slots_spin)

        layout.addWidget(prog_group)
        layout.addStretch()

        # -- Connect signals --
        self._gold_spin.valueChanged.connect(self._on_gold_changed)
        self._hp_spin.valueChanged.connect(self._on_hp_changed)
        self._max_hp_spin.valueChanged.connect(self._on_max_hp_changed)
        self._ascension_spin.valueChanged.connect(self._on_ascension_changed)
        self._act_spin.valueChanged.connect(self._on_act_changed)
        self._floor_spin.valueChanged.connect(self._on_floor_changed)
        self._potion_slots_spin.valueChanged.connect(self._on_potion_slots_changed)

        self._model.data_changed.connect(self._refresh)

    def _make_spin(self, min_val: int, max_val: int) -> QSpinBox:
        spin = QSpinBox()
        spin.setMinimum(min_val)
        spin.setMaximum(max_val)
        spin.setEnabled(False)
        return spin

    def _refresh(self) -> None:
        self._updating = True
        enabled = self._model.is_loaded
        self._character_label.setText(self._model.character if enabled else "—")

        for spin in (
            self._gold_spin,
            self._hp_spin,
            self._max_hp_spin,
            self._ascension_spin,
            self._act_spin,
            self._floor_spin,
            self._potion_slots_spin,
        ):
            spin.setEnabled(enabled)

        if enabled:
            self._gold_spin.setValue(self._model.gold)
            self._hp_spin.setValue(self._model.current_health)
            self._max_hp_spin.setValue(self._model.max_health)
            self._ascension_spin.setValue(self._model.ascension_level)
            self._act_spin.setValue(self._model.act_num)
            self._floor_spin.setValue(self._model.floor_num)
            self._potion_slots_spin.setValue(self._model.potion_slots)
        self._updating = False

    # -- Spin box change handlers --

    def _on_gold_changed(self, value: int) -> None:
        if not self._updating:
            self._model.gold = value

    def _on_hp_changed(self, value: int) -> None:
        if not self._updating:
            self._model.current_health = value

    def _on_max_hp_changed(self, value: int) -> None:
        if not self._updating:
            self._model.max_health = value

    def _on_ascension_changed(self, value: int) -> None:
        if not self._updating:
            self._model.ascension_level = value

    def _on_act_changed(self, value: int) -> None:
        if not self._updating:
            self._model.act_num = value

    def _on_floor_changed(self, value: int) -> None:
        if not self._updating:
            self._model.floor_num = value

    def _on_potion_slots_changed(self, value: int) -> None:
        if not self._updating:
            self._model.potion_slots = value
