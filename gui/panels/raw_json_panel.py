"""Raw JSON panel: view and manually edit the underlying save data."""

from __future__ import annotations

import json
import logging

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from gui.save_model import SaveModel

logger = logging.getLogger(__name__)

WARNING_TEXT = (
    "\u26a0\ufe0f  Warning: Editing raw JSON directly may produce an invalid save file. "
    "Changes made here bypass all validation. Use at your own risk."
)


class RawJsonPanel(QWidget):
    """Full JSON editor with an Apply button for the raw save dict."""

    def __init__(self, model: SaveModel, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._model = model
        self._updating = False

        layout = QVBoxLayout(self)

        # -- Warning banner --
        warning_label = QLabel(WARNING_TEXT)
        warning_label.setWordWrap(True)
        warning_label.setStyleSheet(
            "QLabel { background-color: #fff3cd; color: #664d03; "
            "border: 1px solid #ffecb5; border-radius: 4px; padding: 8px; }"
        )
        layout.addWidget(warning_label)

        # -- JSON text editor --
        self._editor = QTextEdit()
        self._editor.setFont(QFont("Menlo", 12))
        self._editor.setAcceptRichText(False)
        self._editor.setPlaceholderText("Load a save file to view its JSON here...")
        self._editor.setEnabled(False)
        layout.addWidget(self._editor)

        # -- Button row --
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self._refresh_btn = QPushButton("Revert")
        self._refresh_btn.setToolTip("Discard edits and reload JSON from the current model state")
        self._refresh_btn.setEnabled(False)
        self._refresh_btn.clicked.connect(self._on_revert)
        btn_layout.addWidget(self._refresh_btn)

        self._apply_btn = QPushButton("Apply")
        self._apply_btn.setToolTip("Parse the JSON and apply it to the save model")
        self._apply_btn.setEnabled(False)
        self._apply_btn.clicked.connect(self._on_apply)
        btn_layout.addWidget(self._apply_btn)

        layout.addLayout(btn_layout)

        # -- Model signal --
        self._model.data_changed.connect(self._refresh)

    def _refresh(self) -> None:
        self._updating = True
        enabled = self._model.is_loaded
        self._editor.setEnabled(enabled)
        self._apply_btn.setEnabled(enabled)
        self._refresh_btn.setEnabled(enabled)

        if enabled:
            text = json.dumps(self._model.raw, indent=2, ensure_ascii=False)
            self._editor.setPlainText(text)
        else:
            self._editor.clear()
        self._updating = False

    def _on_revert(self) -> None:
        """Reload the editor text from the current model state."""
        self._refresh()

    def _on_apply(self) -> None:
        """Parse the editor text as JSON and push it into the model."""
        if self._updating:
            return

        text = self._editor.toPlainText()
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            logger.warning("Invalid JSON: %s", exc)
            QMessageBox.warning(
                self,
                "Invalid JSON",
                f"Could not parse JSON:\n\n{exc}",
            )
            return

        if not isinstance(data, dict):
            QMessageBox.warning(
                self,
                "Invalid JSON",
                "Top-level value must be a JSON object (dict), not "
                f"{type(data).__name__}.",
            )
            return

        # Confirm before applying
        reply = QMessageBox.question(
            self,
            "Apply Raw JSON?",
            "This will overwrite the entire save data with your edits.\n\n"
            "Fields edited here bypass all validation and may corrupt\n"
            "your save file. Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        logger.info("Applying raw JSON edit (%d keys)", len(data))
        self._model.load(data, file_path=self._model.file_path)
        self._model._dirty = True
        self._model.data_changed.emit()
