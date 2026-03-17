"""Modal dialog showing a large image with name, description, and optional flavor text."""

from __future__ import annotations

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QFont, QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class ImagePreviewDialog(QDialog):
    """Click-to-zoom dialog for cards and relics."""

    def __init__(
        self,
        image_path: str,
        title: str,
        *,
        subtitle: str = "",
        description: str = "",
        flavor: str = "",
        image_display_size: QSize = QSize(300, 387),
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.WindowTitleHint
            | Qt.WindowType.WindowCloseButtonHint
        )

        main_layout = QHBoxLayout(self)

        # -- Image --
        img_label = QLabel()
        img_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        if image_path:
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                pixmap = pixmap.scaled(
                    image_display_size,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                img_label.setPixmap(pixmap)
        main_layout.addWidget(img_label)

        # -- Text area --
        text_layout = QVBoxLayout()
        text_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Title
        title_label = QLabel(title)
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(14)
        title_label.setFont(title_font)
        text_layout.addWidget(title_label)

        # Subtitle
        if subtitle:
            sub_label = QLabel(subtitle)
            sub_label.setStyleSheet("color: gray;")
            text_layout.addWidget(sub_label)

        # Description
        if description:
            desc_label = QLabel(description)
            desc_label.setWordWrap(True)
            desc_label.setMinimumWidth(250)
            text_layout.addWidget(desc_label)

        # Flavor text
        if flavor:
            flavor_label = QLabel(f'"{flavor}"')
            flavor_font = QFont()
            flavor_font.setItalic(True)
            flavor_label.setFont(flavor_font)
            flavor_label.setWordWrap(True)
            flavor_label.setStyleSheet("color: #666;")
            text_layout.addWidget(flavor_label)

        text_layout.addStretch()

        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        text_layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignRight)

        main_layout.addLayout(text_layout)
        self.setFixedSize(self.sizeHint())
