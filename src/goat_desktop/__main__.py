from __future__ import annotations

import sys

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication

from goat_desktop.tray import GoatTrayApp


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("GOAT Desktop")
    app.setQuitOnLastWindowClosed(False)

    tray_app = GoatTrayApp(app)
    app.tray_app = tray_app  # type: ignore[attr-defined]
    tray_app.show_popup()
    QTimer.singleShot(250, tray_app.show_popup)

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
