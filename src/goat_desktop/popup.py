from __future__ import annotations

from PyQt6.QtCore import QPoint, Qt
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtWidgets import (
    QApplication,
    QFrame,
    QComboBox,
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
        self.setMinimumSize(760, 540)
        self._preferred_size = (920, 640)
        self.resize(*self._preferred_size)
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
        self.ensure_visible()

    def ensure_visible(self) -> None:
        screen = self.screen() or QApplication.primaryScreen()
        if screen is None:
            return
        area = screen.availableGeometry()
        margin = 18
        width = min(self.width(), max(self.minimumWidth(), area.width() - margin * 2))
        height = min(self.height(), max(self.minimumHeight(), area.height() - margin * 2))
        if width != self.width() or height != self.height():
            self.resize(width, height)
        x = min(max(self.x(), area.left() + margin), area.right() - self.width() - margin)
        y = min(max(self.y(), area.top() + margin), area.bottom() - self.height() - margin)
        self.move(x, y)

    def restore_preferred_size(self) -> None:
        width, height = self._preferred_size
        self.resize(width, height)
        self.ensure_visible()

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
        self.audio_value = QLabel("-")
        self.screen_context_value = QLabel("-")
        self.maya_value = QLabel("bereit, pausiert")
        for value_label in (self.connection_value, self.audio_value, self.screen_context_value, self.maya_value):
            value_label.setWordWrap(True)
            value_label.setMinimumWidth(260)

        grid.addWidget(QLabel("Verbindung"), 0, 0)
        grid.addWidget(self.connection_value, 0, 1)
        grid.addWidget(QLabel("Audio"), 1, 0)
        grid.addWidget(self.audio_value, 1, 1)
        grid.addWidget(QLabel("Screen-Kontext"), 2, 0)
        grid.addWidget(self.screen_context_value, 2, 1)
        grid.addWidget(QLabel("Maya"), 3, 0)
        grid.addWidget(self.maya_value, 3, 1)

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

        vision_panel = QFrame()
        vision_panel.setObjectName("panel")
        vision_grid = QGridLayout(vision_panel)
        vision_grid.setContentsMargins(12, 10, 12, 10)
        vision_grid.setHorizontalSpacing(12)
        vision_grid.setVerticalSpacing(8)
        vision_grid.addWidget(QLabel("Vision-Modell"), 0, 0)
        self.vision_provider = QComboBox()
        self.vision_provider.addItem("Gemini Flash Lite", "gemini_flash_lite")
        self.vision_provider.addItem("Grok 4.3", "grok_4_3")
        self.vision_provider.addItem("Gemini Flash", "gemini_flash")
        vision_grid.addWidget(self.vision_provider, 0, 1)
        vision_grid.addWidget(QLabel("Denk-Tiefe"), 1, 0)
        self.vision_reasoning = QComboBox()
        self.vision_reasoning.addItem("Minimal", "minimal")
        self.vision_reasoning.addItem("Niedrig", "low")
        self.vision_reasoning.addItem("Mittel", "medium")
        self.vision_reasoning.addItem("Hoch", "high")
        vision_grid.addWidget(self.vision_reasoning, 1, 1)
        root.addWidget(vision_panel)
        self._set_reasoning_tooltips()

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
            QComboBox {
                background: #2d3340;
                border: 1px solid #4a5364;
                border-radius: 5px;
                padding: 5px 8px;
                color: #d7dce6;
            }
            """
        )

    def _set_reasoning_tooltips(self) -> None:
        self.vision_reasoning.setItemData(0, "Schnellste Antwort (ca. 700ms), Standard", Qt.ItemDataRole.ToolTipRole)
        self.vision_reasoning.setItemData(1, "Mehr Nachdenken (1-2s)", Qt.ItemDataRole.ToolTipRole)
        self.vision_reasoning.setItemData(2, "Tiefes Verstaendnis (3-5s)", Qt.ItemDataRole.ToolTipRole)
        self.vision_reasoning.setItemData(3, "Maximale Praezision (5-10s), nur fuer komplexe Faelle", Qt.ItemDataRole.ToolTipRole)
