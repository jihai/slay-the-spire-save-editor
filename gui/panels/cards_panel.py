"""Cards panel: current deck editor + available cards browser."""

from __future__ import annotations

from PySide6.QtCore import QSize, QSortFilterProxyModel, Qt
from PySide6.QtGui import QIcon, QStandardItem, QStandardItemModel
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

from gui.game_config import GameConfig
from gui.game_data import CardInfo, GameData
from gui.widgets.detail_strip import DetailStrip
from gui.widgets.image_preview_dialog import ImagePreviewDialog

ICON_SIZE = QSize(40, 40)


def _card_icon(card: CardInfo) -> QIcon:
    if card.image_path:
        return QIcon(card.image_path)
    return QIcon()


class CardsPanel(QWidget):
    """Deck editor with card browser, search, and filters."""

    def __init__(
        self,
        model,
        game_data: GameData,
        config: GameConfig | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._model = model
        self._game_data = game_data
        self._config = config
        self._has_upgrades = config.has_card_upgrades if config else True
        self._updating = False

        layout = QHBoxLayout(self)

        # -- Left side: Current deck --
        left = QVBoxLayout()
        left_group = QGroupBox("Current Deck")
        left_inner = QVBoxLayout(left_group)

        self._deck_table_model = QStandardItemModel()
        if self._has_upgrades:
            self._deck_table_model.setHorizontalHeaderLabels(["Card", "Upgrades"])
        else:
            self._deck_table_model.setHorizontalHeaderLabels(["Card"])

        self._deck_table = QTableView()
        self._deck_table.setModel(self._deck_table_model)
        self._deck_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._deck_table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self._deck_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._deck_table.setIconSize(ICON_SIZE)
        self._deck_table.horizontalHeader().setStretchLastSection(True)
        self._deck_table.verticalHeader().setDefaultSectionSize(46)
        left_inner.addWidget(self._deck_table)

        # Deck detail strip
        self._deck_detail = DetailStrip(image_size=QSize(60, 77))
        left_inner.addWidget(self._deck_detail)

        # Upgrade controls (STS1 only)
        if self._has_upgrades:
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
        color_label = "Character:" if config and config.game_version == 2 else "Color:"
        filter_row.addWidget(QLabel(color_label))
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
        avail_color_header = "Character" if config and config.game_version == 2 else "Color"
        self._avail_model.setHorizontalHeaderLabels(
            ["Name", avail_color_header, "Type", "Rarity"]
        )

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
        self._avail_table.verticalHeader().setDefaultSectionSize(46)
        right_inner.addWidget(self._avail_table)

        # Available cards detail strip
        self._avail_detail = DetailStrip(image_size=QSize(60, 77))
        right_inner.addWidget(self._avail_detail)

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
        if self._has_upgrades:
            self._set_upgrade_btn.clicked.connect(self._on_set_upgrade)
        self._model.data_changed.connect(self._refresh_deck)
        self._avail_table.selectionModel().currentRowChanged.connect(
            self._on_avail_selected
        )
        self._avail_table.doubleClicked.connect(self._on_avail_double_click)
        self._deck_table.selectionModel().currentRowChanged.connect(
            self._on_deck_selected
        )
        self._deck_table.doubleClicked.connect(self._on_deck_double_click)

    def _make_card_row(self, card: CardInfo) -> list[QStandardItem]:
        name_item = QStandardItem(_card_icon(card), card.name)
        if card.description:
            name_item.setToolTip(card.description)
        color_item = QStandardItem(card.color)
        type_item = QStandardItem(card.card_type)
        rarity_item = QStandardItem(card.rarity)
        for item in (name_item, color_item, type_item, rarity_item):
            item.setEditable(False)
        return [name_item, color_item, type_item, rarity_item]

    def _populate_available(self) -> None:
        self._avail_model.removeRows(0, self._avail_model.rowCount())
        for card in self._game_data.cards:
            self._avail_model.appendRow(self._make_card_row(card))

    def _apply_filters(self) -> None:
        color = self._color_combo.currentData()
        card_type = self._type_combo.currentData()
        filtered = self._game_data.filter_cards(color=color, card_type=card_type)
        self._avail_model.removeRows(0, self._avail_model.rowCount())
        for card in filtered:
            self._avail_model.appendRow(self._make_card_row(card))
        self._avail_detail.clear()

    def _refresh_deck(self) -> None:
        self._updating = True
        self._deck_table_model.removeRows(0, self._deck_table_model.rowCount())
        if self._model.is_loaded:
            for card in self._model.cards:
                card_id = card.get("id", "?")
                card_info = (
                    self._game_data.cards_by_name.get(card_id)
                    or self._game_data.cards_by_id.get(card_id)
                )
                icon = _card_icon(card_info) if card_info else QIcon()
                tooltip = card_info.description if card_info else ""
                display_name = card_info.name if card_info else card_id

                name_item = QStandardItem(icon, display_name)
                if tooltip:
                    name_item.setToolTip(tooltip)
                name_item.setEditable(False)

                if self._has_upgrades:
                    # STS1 uses "upgrades", STS2 uses "current_upgrade_level"
                    upg = card.get("upgrades") or card.get("current_upgrade_level", 0)
                    upgrades_item = QStandardItem(str(upg))
                    upgrades_item.setEditable(False)
                    self._deck_table_model.appendRow([name_item, upgrades_item])
                else:
                    self._deck_table_model.appendRow([name_item])
        self._updating = False
        self._deck_detail.clear()

    def _lookup_avail_card(self, proxy_index):
        """Look up CardInfo from a proxy model index in the available table."""
        source_index = self._proxy_model.mapToSource(proxy_index)
        card_name = self._avail_model.item(source_index.row(), 0).text()
        return (
            self._game_data.cards_by_name.get(card_name)
            or self._game_data.cards_by_id.get(card_name)
        )

    def _lookup_deck_card(self, row: int):
        """Look up CardInfo from a row in the deck table."""
        display_name = self._deck_table_model.item(row, 0).text()
        return (
            self._game_data.cards_by_name.get(display_name)
            or self._game_data.cards_by_id.get(display_name)
        )

    def _on_avail_selected(self, current, _previous) -> None:
        if not current.isValid():
            self._avail_detail.clear()
            return
        card_info = self._lookup_avail_card(current)
        if card_info:
            self._avail_detail.set_card(card_info)
        else:
            self._avail_detail.clear()

    def _on_deck_selected(self, current, _previous) -> None:
        if not current.isValid():
            self._deck_detail.clear()
            return
        card_info = self._lookup_deck_card(current.row())
        if card_info:
            self._deck_detail.set_card(card_info)
        else:
            self._deck_detail.clear()

    def _on_avail_double_click(self, proxy_index) -> None:
        card_info = self._lookup_avail_card(proxy_index)
        if card_info:
            self._show_card_preview(card_info)

    def _on_deck_double_click(self, index) -> None:
        card_info = self._lookup_deck_card(index.row())
        if card_info:
            self._show_card_preview(card_info)

    def _show_card_preview(self, card: CardInfo) -> None:
        dlg = ImagePreviewDialog(
            image_path=card.image_path,
            title=card.name,
            subtitle=f"{card.color}  |  {card.card_type}  |  {card.rarity}",
            description=card.description,
            parent=self,
        )
        dlg.exec()

    def _on_add_card(self) -> None:
        indexes = self._avail_table.selectionModel().selectedRows()
        if not indexes:
            return
        proxy_index = indexes[0]
        card_info = self._lookup_avail_card(proxy_index)
        if not card_info:
            return
        # Use the card's internal ID for the save file
        self._model.add_card(card_info.id, upgrades=1 if self._has_upgrades else 0)

    def _on_remove_card(self) -> None:
        indexes = self._deck_table.selectionModel().selectedRows()
        if not indexes:
            return
        rows = [idx.row() for idx in indexes]
        self._model.remove_cards(rows)

    def _on_set_upgrade(self) -> None:
        indexes = self._deck_table.selectionModel().selectedRows()
        if not indexes:
            return
        row = indexes[0].row()
        self._model.set_card_upgrades(row, self._upgrade_spin.value())
