"""Main application window with menu bar, tab widget, and status bar."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QStatusBar,
    QTabWidget,
    QToolBar,
    QWidget,
)

from gui.game_config import GameConfig, sts1_config, sts2_config
from gui.game_data import GameData
from gui.panels.cards_panel import CardsPanel
from gui.panels.potions_panel import PotionsPanel
from gui.panels.raw_json_panel import RawJsonPanel
from gui.panels.relics_panel import RelicsPanel
from gui.panels.stats_panel import StatsPanel
from gui.save_io import find_save_files, load_save, write_save
from gui.save_model import SaveModel
from gui.save_model_sts2 import SaveModelSTS2
from gui.settings import set_steam_user_id
from gui.steam import detect_steam_users, get_steam_display_names


class MainWindow(QMainWindow):
    def __init__(
        self,
        config: GameConfig | None = None,
        steam_user_id: str | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._config = config or sts1_config()
        self._steam_user_id = steam_user_id
        self.setWindowTitle(self._config.app_title)
        self.resize(1000, 700)

        self._game_data = GameData(resources_dir=self._config.game_resources_dir)

        if self._config.game_version == 2:
            self._model = SaveModelSTS2(self)
        else:
            self._model = SaveModel(self)

        # -- Steam user toolbar (STS2 only) --
        if self._config.game_version == 2:
            self._build_steam_toolbar()

        # -- Tab widget --
        self._tabs = QTabWidget()
        self._stats_panel = StatsPanel(self._model)
        self._cards_panel = CardsPanel(
            self._model, self._game_data, config=self._config
        )
        self._potions_panel = PotionsPanel(self._model, self._game_data)
        self._relics_panel = RelicsPanel(self._model, self._game_data)
        self._raw_json_panel = RawJsonPanel(self._model)

        self._tabs.addTab(self._stats_panel, "Stats")
        self._tabs.addTab(self._cards_panel, "Cards")
        self._tabs.addTab(self._potions_panel, "Potions")
        self._tabs.addTab(self._relics_panel, "Relics")
        self._tabs.addTab(self._raw_json_panel, "Raw JSON")
        self.setCentralWidget(self._tabs)

        # -- Menu bar --
        menu = self.menuBar()
        file_menu = menu.addMenu("File")

        open_save_dir_action = file_menu.addAction("Open Save Directory...")
        open_save_dir_action.setShortcut("Ctrl+O")
        open_save_dir_action.triggered.connect(self._open_save_dir)

        upload_action = file_menu.addAction("Upload Save File...")
        upload_action.setShortcut("Ctrl+Shift+O")
        upload_action.triggered.connect(self._upload_file)

        file_menu.addSeparator()

        save_action = file_menu.addAction("Save")
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self._save)

        save_as_action = file_menu.addAction("Save As...")
        save_as_action.setShortcut("Ctrl+Shift+S")
        save_as_action.triggered.connect(self._save_as)

        file_menu.addSeparator()

        quit_action = file_menu.addAction("Quit")
        quit_action.setShortcut("Ctrl+Q")
        quit_action.triggered.connect(self.close)

        # -- Status bar --
        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)
        self._status_bar.showMessage("No file loaded")

        # -- Model signals --
        self._model.data_changed.connect(self._update_title)

    def _build_steam_toolbar(self) -> None:
        toolbar = QToolBar("Steam User")
        toolbar.setMovable(False)
        toolbar.addWidget(QLabel("  Steam User: "))
        self._steam_user_combo = QComboBox()
        self._steam_user_combo.setMinimumWidth(180)
        users = detect_steam_users()
        display_names = get_steam_display_names()
        for uid in users:
            name = display_names.get(uid)
            label = f"{name} ({uid})" if name else uid
            self._steam_user_combo.addItem(label, uid)
        if self._steam_user_id and self._steam_user_id in users:
            idx = users.index(self._steam_user_id)
            self._steam_user_combo.setCurrentIndex(idx)
        self._steam_user_combo.currentIndexChanged.connect(
            self._on_steam_user_index_changed
        )
        toolbar.addWidget(self._steam_user_combo)
        self.addToolBar(toolbar)

    def _on_steam_user_index_changed(self, index: int) -> None:
        user_id = self._steam_user_combo.itemData(index)
        if not user_id or user_id == self._steam_user_id:
            return
        self._steam_user_id = user_id
        set_steam_user_id(user_id)
        self._config = sts2_config(steam_user_id=user_id)
        label = self._steam_user_combo.itemText(index)
        self._status_bar.showMessage(f"Switched to Steam user {label}")

    def _update_title(self) -> None:
        title = self._config.app_title
        if not self._model.is_loaded:
            self.setWindowTitle(title)
            return
        parts = [title]
        if self._model.file_path:
            parts.append(f"— {Path(self._model.file_path).name}")
        parts.append(f"[{self._model.character}]")
        if self._model.dirty:
            parts.append("*")
        self.setWindowTitle(" ".join(parts))

    def _open_save_dir(self) -> None:
        saves = find_save_files(config=self._config)
        if not saves:
            self._upload_file()
            return

        names = [p.name for p in saves]
        path_map = {p.name: p for p in saves}

        from PySide6.QtWidgets import QInputDialog

        name, ok = QInputDialog.getItem(
            self, "Select Save File", "Available saves:", names, 0, False
        )
        if ok and name:
            self._load_file(path_map[name])

    def _upload_file(self) -> None:
        save_dir = self._config.save_dir
        start_dir = str(save_dir) if save_dir.is_dir() else ""
        # Use non-native dialog to avoid macOS greying out .save files
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Save File",
            start_dir,
            self._config.file_filter,
            options=QFileDialog.Option.DontUseNativeDialog,
        )
        if path:
            self._load_file(Path(path))

    def _load_file(self, path: Path) -> None:
        try:
            data = load_save(path, config=self._config)
            self._model.load(data, file_path=str(path))
            self._status_bar.showMessage(f"Loaded: {path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load save file:\n{e}")

    def _save(self) -> None:
        if not self._model.file_path:
            self._save_as()
            return
        self._write_to(Path(self._model.file_path))

    def _save_as(self) -> None:
        start_dir = self._model.file_path or str(self._config.save_dir)
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save As",
            start_dir,
            self._config.file_filter,
        )
        if path:
            self._model.file_path = path
            self._write_to(Path(path))

    def _write_to(self, path: Path) -> None:
        try:
            write_save(path, self._model.raw, config=self._config)
            self._model.mark_clean()
            self._status_bar.showMessage(f"Saved: {path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save:\n{e}")

    def closeEvent(self, event) -> None:
        if self._model.dirty:
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes. Save before closing?",
                QMessageBox.StandardButton.Save
                | QMessageBox.StandardButton.Discard
                | QMessageBox.StandardButton.Cancel,
            )
            if reply == QMessageBox.StandardButton.Save:
                self._save()
                event.accept()
            elif reply == QMessageBox.StandardButton.Discard:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()
