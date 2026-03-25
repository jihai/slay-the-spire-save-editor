"""Application entry point for the Slay the Spire Save Editor GUI."""

import sys

from PySide6.QtWidgets import QApplication, QInputDialog

from gui.game_config import sts1_config, sts2_config
from gui.main_window import MainWindow
from gui.settings import get_steam_user_id, set_steam_user_id
from gui.steam import detect_steam_users


def _resolve_steam_user(app: QApplication) -> str | None:
    """Determine the Steam user ID for STS2 mode.

    Priority: saved setting → single detected user → user prompt → None.
    """
    saved = get_steam_user_id()
    users = detect_steam_users()

    # Saved user is still valid
    if saved and saved in users:
        return saved

    if len(users) == 1:
        set_steam_user_id(users[0])
        return users[0]

    if len(users) > 1:
        chosen, ok = QInputDialog.getItem(
            None,
            "Select Steam User",
            "Multiple Steam accounts have STS2 saves.\nChoose one:",
            users,
            0,
            False,
        )
        if ok and chosen:
            set_steam_user_id(chosen)
            return chosen

    # No users detected — will fall back to manual file upload
    return None


def main(game_version: int = 1) -> None:
    app = QApplication(sys.argv)

    steam_user_id = None
    if game_version == 2:
        steam_user_id = _resolve_steam_user(app)
        config = sts2_config(steam_user_id=steam_user_id)
    else:
        config = sts1_config()

    app.setApplicationName(config.app_title)

    window = MainWindow(config=config, steam_user_id=steam_user_id)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
