"""Cards panel: current deck editor + available cards browser."""

from __future__ import annotations

from PySide6.QtCore import QSortFilterProxyModel, Qt
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from gui.game_data import GameData
from gui.save_model import SaveModel


class CardsPanel(QWidget):
    """Deck editor with card browser, search, and filters."""

    def __init__(
        self, model: SaveModel, game_data: GameData, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self._model = model
        self._game_data = game_data
        self._updating = False

        layout = QHBoxLayout(self)

        # -- Left side: Current deck --
        left = QVBoxLayout()
        left_group = QGroupBox("Current Deck")
        left_inner = QVBoxLayout(left_group)

        self._deck_table_model = QStandardItemModel()
        self._deck_table_model.setHorizontalHeaderLabels(["Card", "Upgrades"])

        self._deck_table = QTableView()
        self._deck_table.setModel(self._deck_table_model)
        self._deck_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._deck_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._deck_table.horizontalHeader().setStretchLastSection(True)
        left_inner.addWidget(self._deck_table)

        # Upgrade controls
        upgrade_row = QHBoxLayout()
        upgrade_row.addWidget(QLabel("Upgrades:"))
        self._upgrade_spin = QSpinBox()
        self._upgrade_spin.setMinimum(0)
        self._upgrade_spin.setMaximum(100)
        upgrade_row.addWidget(self._upgrade_spin)
        self._set_upgrade_btn = QPushButton("Set")
        upgrade_row.addWidget(self._set_upgrade_btn)
        left_inner.addLayout(upgrade_row)

        self._remove_btn = QPushButton("Remove Selected")
        left_inner.addWidget(self._remove_btn)

        left.addWidget(left_group)
        layout.addLayout(left, stretch=1)

        # -- Right side: Available cards browser --
        right = QVBoxLayout()
        right_group = QGroupBox("Available Cards")
        right_inner = QVBoxLayout(right_group)

        # Search bar
        search_row = QHBoxLayout()
        search_row.addWidget(QLabel("Search:"))
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Type to filter...")
        search_row.addWidget(self._search_input)
        right_inner.addLayout(search_row)

        # Filter dropdowns
        filter_row = QHBoxLayout()
        filter_row.addWidget(QLabel("Color:"))
        self._color_combo = QComboBox()
        self._color_combo.addItem("All", None)
        for color in game_data.card_colors():
            self._color_combo.addItem(color, color)
        filter_row.addWidget(self._color_combo)

        filter_row.addWidget(QLabel("Type:"))
        self._type_combo = QComboBox()
        self._type_combo.addItem("All", None)
        for t in game_data.card_types():
            self._type_combo.addItem(t, t)
        filter_row.addWidget(self._type_combo)
        right_inner.addLayout(filter_row)

        # Available cards table
        self._avail_model = QStandardItemModel()
        self._avail_model.setHorizontalHeaderLabels(["Name", "Color", "Type", "Rarity"])

        self._proxy_model = QSortFilterProxyModel()
        self._proxy_model.setSourceModel(self._avail_model)
        self._proxy_model.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._proxy_model.setFilterKeyColumn(0)

        self._avail_table = QTableView()
        self._avail_table.setModel(self._proxy_model)
        self._avail_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._avail_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._avail_table.setSortingEnabled(True)
        self._avail_table.horizontalHeader().setStretchLastSection(True)
        right_inner.addWidget(self._avail_table)

        self._add_btn = QPushButton("Add to Deck")
        right_inner.addWidget(self._add_btn)

        right.addWidget(right_group)
        layout.addLayout(right, stretch=1)

        # Populate available cards
        self._populate_available()

        # Connect signals
        self._search_input.textChanged.connect(self._proxy_model.setFilterFixedString)
        self._color_combo.currentIndexChanged.connect(self._apply_filters)
        self._type_combo.currentIndexChanged.connect(self._apply_filters)
        self._add_btn.clicked.connect(self._on_add_card)
        self._remove_btn.clicked.connect(self._on_remove_card)
        self._set_upgrade_btn.clicked.connect(self._on_set_upgrade)
        self._model.data_changed.connect(self._refresh_deck)

    def _populate_available(self) -> None:
        self._avail_model.removeRows(0, self._avail_model.rowCount())
        for card in self._game_data.cards:
            row = [
                QStandardItem(card.name),
                QStandardItem(card.color),
                QStandardItem(card.card_type),
                QStandardItem(card.rarity),
            ]
            for item in row:
                item.setEditable(False)
            self._avail_model.appendRow(row)

    def _apply_filters(self) -> None:
        color = self._color_combo.currentData()
        card_type = self._type_combo.currentData()
        filtered = self._game_data.filter_cards(color=color, card_type=card_type)
        names = {c.name for c in filtered}

        for row in range(self._avail_model.rowCount()):
            name = self._avail_model.item(row, 0).text()
            source_index = self._avail_model.index(row, 0)
            proxy_index = self._proxy_model.mapFromSource(source_index)
            # Show/hide by checking if name is in filtered set
            # We rebuild the model for simplicity
        # Rebuild with filtered data
        self._avail_model.removeRows(0, self._avail_model.rowCount())
        for card in filtered:
            row = [
                QStandardItem(card.name),
                QStandardItem(card.color),
                QStandardItem(card.card_type),
                QStandardItem(card.rarity),
            ]
            for item in row:
                item.setEditable(False)
            self._avail_model.appendRow(row)

    def _refresh_deck(self) -> None:
        self._updating = True
        self._deck_table_model.removeRows(0, self._deck_table_model.rowCount())
        if self._model.is_loaded:
            for card in self._model.cards:
                name_item = QStandardItem(card.get("id", "?"))
                upgrades_item = QStandardItem(str(card.get("upgrades", 0)))
                name_item.setEditable(False)
                upgrades_item.setEditable(False)
                self._deck_table_model.appendRow([name_item, upgrades_item])
        self._updating = False

    def _on_add_card(self) -> None:
        indexes = self._avail_table.selectionModel().selectedRows()
        if not indexes:
            return
        proxy_index = indexes[0]
        source_index = self._proxy_model.mapToSource(proxy_index)
        card_name = self._avail_model.item(source_index.row(), 0).text()
        self._model.add_card(card_name)

    def _on_remove_card(self) -> None:
        indexes = self._deck_table.selectionModel().selectedRows()
        if not indexes:
            return
        row = indexes[0].row()
        self._model.remove_card(row)

    def _on_set_upgrade(self) -> None:
        indexes = self._deck_table.selectionModel().selectedRows()
        if not indexes:
            return
        row = indexes[0].row()
        self._model.set_card_upgrades(row, self._upgrade_spin.value())
