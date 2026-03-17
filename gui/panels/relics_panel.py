"""Relics panel: current relics editor + available relics browser."""

from __future__ import annotations

from PySide6.QtCore import QSize, QSortFilterProxyModel, Qt
from PySide6.QtGui import QIcon, QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from gui.game_data import GameData, RelicInfo
from gui.save_model import SaveModel

ICON_SIZE = QSize(28, 28)


def _relic_icon(relic: RelicInfo) -> QIcon:
    if relic.image_path:
        return QIcon(relic.image_path)
    return QIcon()


def _relic_tooltip(relic: RelicInfo) -> str:
    parts = []
    if relic.description:
        parts.append(relic.description)
    if relic.flavor:
        parts.append(f"\n\"{relic.flavor}\"")
    return "".join(parts)


class RelicsPanel(QWidget):
    """Relic editor with available relics browser, search, and tier filter."""

    def __init__(
        self, model: SaveModel, game_data: GameData, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self._model = model
        self._game_data = game_data
        self._updating = False

        layout = QHBoxLayout(self)

        # -- Left side: Current relics --
        left = QVBoxLayout()
        left_group = QGroupBox("Current Relics")
        left_inner = QVBoxLayout(left_group)

        self._relic_list = QListWidget()
        self._relic_list.setIconSize(ICON_SIZE)
        left_inner.addWidget(self._relic_list)

        self._remove_btn = QPushButton("Remove Selected")
        left_inner.addWidget(self._remove_btn)

        left.addWidget(left_group)
        layout.addLayout(left, stretch=1)

        # -- Right side: Available relics browser --
        right = QVBoxLayout()
        right_group = QGroupBox("Available Relics")
        right_inner = QVBoxLayout(right_group)

        # Search bar
        search_row = QHBoxLayout()
        search_row.addWidget(QLabel("Search:"))
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Type to filter...")
        search_row.addWidget(self._search_input)
        right_inner.addLayout(search_row)

        # Tier filter
        filter_row = QHBoxLayout()
        filter_row.addWidget(QLabel("Tier:"))
        self._tier_combo = QComboBox()
        self._tier_combo.addItem("All", None)
        for tier in game_data.relic_tiers():
            self._tier_combo.addItem(tier, tier)
        filter_row.addWidget(self._tier_combo)
        right_inner.addLayout(filter_row)

        # Available relics table
        self._avail_model = QStandardItemModel()
        self._avail_model.setHorizontalHeaderLabels(["Name", "Tier"])

        self._proxy_model = QSortFilterProxyModel()
        self._proxy_model.setSourceModel(self._avail_model)
        self._proxy_model.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._proxy_model.setFilterKeyColumn(0)

        self._avail_table = QTableView()
        self._avail_table.setModel(self._proxy_model)
        self._avail_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._avail_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._avail_table.setSortingEnabled(True)
        self._avail_table.setIconSize(ICON_SIZE)
        self._avail_table.horizontalHeader().setStretchLastSection(True)
        right_inner.addWidget(self._avail_table)

        self._add_btn = QPushButton("Add Relic")
        right_inner.addWidget(self._add_btn)

        right.addWidget(right_group)
        layout.addLayout(right, stretch=1)

        # Populate available relics
        self._populate_available()

        # Connect signals
        self._search_input.textChanged.connect(self._proxy_model.setFilterFixedString)
        self._tier_combo.currentIndexChanged.connect(self._apply_tier_filter)
        self._add_btn.clicked.connect(self._on_add_relic)
        self._remove_btn.clicked.connect(self._on_remove_relic)
        self._model.data_changed.connect(self._refresh_relics)

    def _populate_available(self, relics=None) -> None:
        self._avail_model.removeRows(0, self._avail_model.rowCount())
        items = relics if relics is not None else self._game_data.relics
        for relic in items:
            name_item = QStandardItem(_relic_icon(relic), relic.name)
            tooltip = _relic_tooltip(relic)
            if tooltip:
                name_item.setToolTip(tooltip)
            tier_item = QStandardItem(relic.tier)
            name_item.setEditable(False)
            tier_item.setEditable(False)
            self._avail_model.appendRow([name_item, tier_item])

    def _apply_tier_filter(self) -> None:
        tier = self._tier_combo.currentData()
        filtered = self._game_data.filter_relics(tier=tier)
        self._populate_available(filtered)

    def _refresh_relics(self) -> None:
        self._updating = True
        self._relic_list.clear()
        if self._model.is_loaded:
            for relic_name in self._model.relics:
                relic_info = (
                    self._game_data.relics_by_name.get(relic_name)
                    or self._game_data.relics_by_id.get(relic_name)
                )
                if relic_info:
                    icon = _relic_icon(relic_info)
                    item = QListWidgetItem(icon, relic_name)
                    tooltip = _relic_tooltip(relic_info)
                    if tooltip:
                        item.setToolTip(tooltip)
                else:
                    item = QListWidgetItem(relic_name)
                self._relic_list.addItem(item)
        self._updating = False

    def _on_add_relic(self) -> None:
        indexes = self._avail_table.selectionModel().selectedRows()
        if not indexes:
            return
        proxy_index = indexes[0]
        source_index = self._proxy_model.mapToSource(proxy_index)
        relic_name = self._avail_model.item(source_index.row(), 0).text()
        self._model.add_relic(relic_name)

    def _on_remove_relic(self) -> None:
        row = self._relic_list.currentRow()
        if row >= 0:
            self._model.remove_relic(row)
