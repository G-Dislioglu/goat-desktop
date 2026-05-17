from __future__ import annotations

from ctypes import windll

from PyQt6.QtCore import QPoint, Qt
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtWidgets import QApplication, QWidget


GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x00080000
WS_EX_TRANSPARENT = 0x00000020
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_TOPMOST = 0x00000008


class BallOverlay(QWidget):
    """Small click-through topmost cue window.

    Run B intentionally avoids a fullscreen transparent window because a bad
    overlay can block the desktop. The safe MVP surface is only the cue ball.
    """

    def __init__(self) -> None:
        super().__init__()
        self._diameter = 54
        self._margin = 4

        self.setWindowTitle("GOAT Overlay")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.setAutoFillBackground(False)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.WindowTransparentForInput
        )
        self.resize(self._diameter + self._margin * 2, self._diameter + self._margin * 2)
        self.move(220, 220)

    def show_overlay(self) -> None:
        self.show()
        self.raise_()
        self._apply_click_through_styles()

    def hide_ball(self) -> None:
        self.hide()

    def show_ball(self) -> None:
        self.show_overlay()

    def move_ball_by(self, dx: int, dy: int) -> None:
        screen_rect = self._virtual_desktop_rect()
        next_point = self.pos() + QPoint(dx, dy)
        max_x = screen_rect.right() - self.width()
        max_y = screen_rect.bottom() - self.height()
        next_point.setX(max(screen_rect.left(), min(max_x, next_point.x())))
        next_point.setY(max(screen_rect.top(), min(max_y, next_point.y())))
        self.move(next_point)
        self.show_overlay()

    def move_ball_to(self, x: int, y: int) -> None:
        self.move(QPoint(x, y))
        self.move_ball_by(0, 0)

    def is_click_through_enabled(self) -> bool:
        hwnd = int(self.winId())
        styles = windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        return bool(styles & WS_EX_TRANSPARENT)

    def paintEvent(self, event) -> None:  # type: ignore[override]
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        center = self.rect().center()
        radius = self._diameter // 2
        painter.setBrush(QColor("#ffd84d"))
        painter.setPen(QPen(QColor("#151515"), 2))
        painter.drawEllipse(center, radius, radius)
        painter.setPen(QPen(QColor("#fff4b8"), 3))
        painter.drawEllipse(center, radius - 10, radius - 10)

    def _virtual_desktop_rect(self):
        screens = QApplication.screens()
        geometry = screens[0].geometry()
        for screen in screens[1:]:
            geometry = geometry.united(screen.geometry())
        return geometry

    def _apply_click_through_styles(self) -> None:
        hwnd = int(self.winId())
        styles = windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        styles |= WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_TOOLWINDOW | WS_EX_TOPMOST
        windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, styles)

