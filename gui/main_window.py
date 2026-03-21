"""Main application window with menu bar, tab widget, and status bar."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QStatusBar,
    QTabWidget,
    QWidget,
)

from gui.game_data import GameData
from gui.panels.cards_panel import CardsPanel
from gui.panels.potions_panel import PotionsPanel
from gui.panels.raw_json_panel import RawJsonPanel
from gui.panels.relics_panel import RelicsPanel
from gui.panels.stats_panel import StatsPanel
from gui.save_io import DEFAULT_SAVE_DIR, find_save_files, load_save, write_save
from gui.save_model import SaveModel

APP_TITLE = "Slay the Spire Save Editor"


class MainWindow(QMainWindow):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(APP_TITLE)
        self.resize(1000, 700)

        self._game_data = GameData()
        self._model = SaveModel(self)

        # -- Tab widget --
        self._tabs = QTabWidget()
        self._stats_panel = StatsPanel(self._model)
        self._cards_panel = CardsPanel(self._model, self._game_data)
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

    def _update_title(self) -> None:
        if not self._model.is_loaded:
            self.setWindowTitle(APP_TITLE)
            return
        parts = [APP_TITLE]
        if self._model.file_path:
            parts.append(f"— {Path(self._model.file_path).name}")
        parts.append(f"[{self._model.character}]")
        if self._model.dirty:
            parts.append("*")
        self.setWindowTitle(" ".join(parts))

    def _open_save_dir(self) -> None:
        saves = find_save_files()
        if not saves:
            # Fall back to file dialog if no saves found
            self._upload_file()
            return

        # Let user pick from found save files
        names = [p.name for p in saves]
        path_map = {p.name: p for p in saves}

        from PySide6.QtWidgets import QInputDialog

        name, ok = QInputDialog.getItem(
            self, "Select Save File", "Available saves:", names, 0, False
        )
        if ok and name:
            self._load_file(path_map[name])

    def _upload_file(self) -> None:
        start_dir = str(DEFAULT_SAVE_DIR) if DEFAULT_SAVE_DIR.is_dir() else ""
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Save File", start_dir, "Save Files (*.autosave);;All Files (*)"
        )
        if path:
            self._load_file(Path(path))

    def _load_file(self, path: Path) -> None:
        try:
            data = load_save(path)
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
        start_dir = self._model.file_path or str(DEFAULT_SAVE_DIR)
        path, _ = QFileDialog.getSaveFileName(
            self, "Save As", start_dir, "Save Files (*.autosave);;All Files (*)"
        )
        if path:
            self._model.file_path = path
            self._write_to(Path(path))

    def _write_to(self, path: Path) -> None:
        try:
            write_save(path, self._model.raw)
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
