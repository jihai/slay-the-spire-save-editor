"""Inline preview strip showing image + text for a selected card or relic."""

from __future__ import annotations

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QFont, QPixmap
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from gui.game_data import CardInfo, RelicInfo

PLACEHOLDER_TEXT = "Select an item to see details"


class DetailStrip(QWidget):
    """Compact preview widget: image thumbnail + name + description."""

    def __init__(
        self,
        image_size: QSize = QSize(60, 77),
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._image_size = image_size
        self.setFixedHeight(85)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        # Image label
        self._img_label = QLabel()
        self._img_label.setFixedSize(image_size)
        self._img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._img_label)

        # Text area
        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(2)

        self._name_label = QLabel()
        name_font = QFont()
        name_font.setBold(True)
        self._name_label.setFont(name_font)
        text_layout.addWidget(self._name_label)

        self._desc_label = QLabel()
        self._desc_label.setWordWrap(True)
        text_layout.addWidget(self._desc_label)

        self._flavor_label = QLabel()
        flavor_font = QFont()
        flavor_font.setItalic(True)
        self._flavor_label.setFont(flavor_font)
        self._flavor_label.setStyleSheet("color: #666;")
        self._flavor_label.setWordWrap(True)
        self._flavor_label.hide()
        text_layout.addWidget(self._flavor_label)

        text_layout.addStretch()
        layout.addLayout(text_layout, stretch=1)

        # Start with placeholder
        self.clear()

    def set_card(self, card: CardInfo) -> None:
        self._set_image(card.image_path)
        self._name_label.setText(card.name)
        self._desc_label.setText(card.description or "")
        self._flavor_label.hide()

    def set_relic(self, relic: RelicInfo) -> None:
        self._set_image(relic.image_path)
        self._name_label.setText(relic.name)
        self._desc_label.setText(relic.description or "")
        if relic.flavor:
            self._flavor_label.setText(f'"{relic.flavor}"')
            self._flavor_label.show()
        else:
            self._flavor_label.hide()

    def clear(self) -> None:
        self._img_label.clear()
        self._name_label.setText(PLACEHOLDER_TEXT)
        self._desc_label.clear()
        self._flavor_label.hide()

    def _set_image(self, image_path: str) -> None:
        if image_path:
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                pixmap = pixmap.scaled(
                    self._image_size,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                self._img_label.setPixmap(pixmap)
                return
        self._img_label.clear()
