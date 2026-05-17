from __future__ import annotations

from PyQt6.QtCore import QPoint, Qt
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtWidgets import (
    QApplication,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class GoatPopup(QWidget):
    """Small native status popup for Run A."""

    def __init__(self) -> None:
        super().__init__()
        self._drag_start: QPoint | None = None

        self.setWindowTitle("GOAT Desktop")
        self.setMinimumSize(560, 340)
        self.resize(580, 360)
        self.setWindowFlag(Qt.WindowType.Window, True)

        self._build_ui()

    def place_near_tray(self) -> None:
        screen = self.screen() or QApplication.primaryScreen()
        if screen is None:
            return
        area = screen.availableGeometry()
        margin = 18
        self.move(
            area.right() - self.width() - margin,
            area.bottom() - self.height() - margin,
        )

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._drag_start is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_start)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self._drag_start = None
        super().mouseReleaseEvent(event)

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 14, 16, 14)
        root.setSpacing(12)

        title = QLabel("GOAT Desktop")
        title.setObjectName("title")
        root.addWidget(title)

        panel = QFrame()
        panel.setObjectName("panel")
        grid = QGridLayout(panel)
        grid.setContentsMargins(12, 10, 12, 10)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)

        self.connection_value = QLabel("offline")
        self.screen_context_value = QLabel("-")
        self.maya_value = QLabel("bereit, pausiert")
        for value_label in (self.connection_value, self.screen_context_value, self.maya_value):
            value_label.setWordWrap(True)
            value_label.setMinimumWidth(260)

        grid.addWidget(QLabel("Verbindung"), 0, 0)
        grid.addWidget(self.connection_value, 0, 1)
        grid.addWidget(QLabel("Screen-Kontext"), 1, 0)
        grid.addWidget(self.screen_context_value, 1, 1)
        grid.addWidget(QLabel("Maya"), 2, 0)
        grid.addWidget(self.maya_value, 2, 1)

        root.addWidget(panel)

        actions = QGridLayout()
        actions.setHorizontalSpacing(10)

        stop_button = QPushButton("Pause / Stop")
        stop_button.setEnabled(False)
        self.talk_button = QPushButton("LiveTalk")
        self.cue_test = QPushButton("Cue testen")
        self.cue_approve = QPushButton("Cue freigeben")
        self.cue_reject = QPushButton("Cue ablehnen")
        self.cue_approve.setEnabled(False)
        self.cue_reject.setEnabled(False)

        actions.addWidget(stop_button, 0, 0)
        actions.addWidget(self.talk_button, 0, 1)
        actions.addWidget(self.cue_test, 1, 0, 1, 2)
        actions.addWidget(self.cue_approve, 2, 0)
        actions.addWidget(self.cue_reject, 2, 1)
        root.addLayout(actions)

        overlay_controls = QHBoxLayout()
        overlay_controls.setSpacing(8)
        self.ball_left = QPushButton("Ball <")
        self.ball_right = QPushButton("Ball >")
        self.ball_up = QPushButton("Ball ^")
        self.ball_down = QPushButton("Ball v")
        self.ball_toggle = QPushButton("Ball aus")
        for button in (self.ball_left, self.ball_right, self.ball_up, self.ball_down, self.ball_toggle):
            overlay_controls.addWidget(button)
        root.addLayout(overlay_controls)

        self.setStyleSheet(
            """
            QWidget {
                background: #17191f;
                color: #f2f4f8;
                font-family: Segoe UI;
                font-size: 12px;
            }
            QLabel#title {
                font-size: 16px;
                font-weight: 600;
            }
            QFrame#panel {
                border: 1px solid #3a3f4b;
                border-radius: 6px;
                background: #20232b;
            }
            QPushButton {
                background: #2d3340;
                border: 1px solid #4a5364;
                border-radius: 5px;
                padding: 7px 10px;
                color: #d7dce6;
            }
            QPushButton:disabled {
                color: #8d95a3;
            }
            """
        )
