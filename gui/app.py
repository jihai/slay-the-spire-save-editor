"""Application entry point for the Slay the Spire Save Editor GUI."""

import sys

from PySide6.QtWidgets import QApplication

from gui.game_config import sts1_config, sts2_config
from gui.main_window import MainWindow


def main(game_version: int = 1) -> None:
    config = sts2_config() if game_version == 2 else sts1_config()

    app = QApplication(sys.argv)
    app.setApplicationName(config.app_title)

    window = MainWindow(config=config)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
