from __future__ import annotations

from importlib import resources

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QIcon, QPainter, QPixmap
from PyQt6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from goat_desktop.hotkey import EmergencyHotkey
from goat_desktop.overlay import BallOverlay
from goat_desktop.popup import GoatPopup


class GoatTrayApp:
    def __init__(self, app: QApplication) -> None:
        if not QSystemTrayIcon.isSystemTrayAvailable():
            raise RuntimeError("Windows system tray is not available")

        self.app = app
        self.overlay = BallOverlay()
        self.popup = GoatPopup()
        self._ball_visible = True
        self._connect_popup_controls()
        self.overlay.show_overlay()
        self.popup.place_near_tray()
        self.popup.show()
        self.hotkey = EmergencyHotkey(self.emergency_stop)
        self.tray = QSystemTrayIcon(self._load_icon(), app)
        self.tray.setToolTip("GOAT Desktop")
        self.tray.activated.connect(self._on_activated)
        self.tray.setContextMenu(self._build_menu())
        self.tray.show()

    def show_popup(self) -> None:
        if not self.popup.isVisible():
            self.popup.place_near_tray()
        self.popup.show()
        self.popup.raise_()
        self.popup.activateWindow()

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason in (
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        ):
            self.show_popup()

    def _build_menu(self) -> QMenu:
        menu = QMenu()
        show_action = QAction("Popup anzeigen", menu)
        show_action.triggered.connect(self.show_popup)
        quit_action = QAction("Beenden", menu)
        quit_action.triggered.connect(self.shutdown)
        menu.addAction(show_action)
        overlay_action = QAction("Ball anzeigen", menu)
        overlay_action.triggered.connect(self.show_ball)
        hide_overlay_action = QAction("Ball ausblenden", menu)
        hide_overlay_action.triggered.connect(self.hide_ball)
        menu.addSeparator()
        menu.addAction(overlay_action)
        menu.addAction(hide_overlay_action)
        menu.addSeparator()
        menu.addAction(quit_action)
        return menu

    def show_ball(self) -> None:
        self._ball_visible = True
        self.overlay.show_overlay()
        self.overlay.show_ball()
        self.popup.ball_toggle.setText("Ball aus")

    def hide_ball(self) -> None:
        self._ball_visible = False
        self.overlay.hide_ball()
        self.popup.ball_toggle.setText("Ball an")

    def emergency_stop(self) -> None:
        self.hide_ball()
        self.popup.hide()

    def shutdown(self) -> None:
        self.hotkey.unregister()
        self.overlay.hide()
        self.app.quit()

    def _connect_popup_controls(self) -> None:
        self.popup.ball_left.clicked.connect(lambda: self.overlay.move_ball_by(-80, 0))
        self.popup.ball_right.clicked.connect(lambda: self.overlay.move_ball_by(80, 0))
        self.popup.ball_up.clicked.connect(lambda: self.overlay.move_ball_by(0, -80))
        self.popup.ball_down.clicked.connect(lambda: self.overlay.move_ball_by(0, 80))
        self.popup.ball_toggle.clicked.connect(self._toggle_ball)

    def _toggle_ball(self) -> None:
        if self._ball_visible:
            self.hide_ball()
        else:
            self.show_ball()

    def _load_icon(self) -> QIcon:
        try:
            icon_path = resources.files("goat_desktop").joinpath("assets/goat-icon.svg")
            icon = QIcon(str(icon_path))
            if not icon.isNull():
                return icon
        except Exception:
            pass
        return self._fallback_icon()

    def _fallback_icon(self) -> QIcon:
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(Qt.GlobalColor.yellow)
        painter.setPen(Qt.GlobalColor.black)
        painter.drawEllipse(4, 4, 56, 56)
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "G")
        painter.end()
        return QIcon(pixmap)
