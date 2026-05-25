from __future__ import annotations

from PyQt6.QtCore import QPoint, Qt, pyqtSignal
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class GoatPopup(QWidget):
    """Small native status popup for Run A."""

    read_aloud_finished = pyqtSignal(dict)
    push_to_talk_finished = pyqtSignal(dict)
    screen_context_finished = pyqtSignal(dict)
    chat_finished = pyqtSignal(dict)

    def __init__(self) -> None:
        super().__init__()
        self._drag_start: QPoint | None = None

        self.setWindowTitle("GOAT Desktop")
        self.setMinimumSize(500, 360)
        self._preferred_size = (620, 450)
        self._livetalk_size = (430, 320)
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
        root.setContentsMargins(14, 12, 14, 12)
        root.setSpacing(10)

        title = QLabel("GOAT Desktop")
        title.setObjectName("title")
        root.addWidget(title)

        self.connection_value = QLabel("offline")
        self.audio_value = QLabel("-")
        self.screen_context_value = QLabel("-")
        self.maya_value = QLabel("bereit, pausiert")
        self.target_value = QLabel("Kein Ziel markiert")
        for value_label in (
            self.connection_value,
            self.audio_value,
            self.screen_context_value,
            self.maya_value,
            self.target_value,
        ):
            value_label.setWordWrap(True)

        status_row = QHBoxLayout()
        status_row.setSpacing(8)
        self.connection_chip = self._chip("Verbindung: offline")
        self.audio_chip = self._chip("Audio: -")
        status_row.addWidget(self.connection_chip, 1)
        status_row.addWidget(self.audio_chip, 2)
        root.addLayout(status_row)

        output_panel = QFrame()
        output_panel.setObjectName("panel")
        output_layout = QVBoxLayout(output_panel)
        output_layout.setContentsMargins(10, 8, 10, 8)
        output_layout.setSpacing(8)
        self.target_value.setObjectName("target")
        self.screen_context_value.setObjectName("output")
        self.maya_value.setObjectName("output")
        output_layout.addWidget(self.target_value)
        output_layout.addWidget(self.screen_context_value)
        output_layout.addWidget(self.maya_value)
        root.addWidget(output_panel, 1)

        self.chat_row = QHBoxLayout()
        self.chat_row.setSpacing(8)
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Nachricht schreiben...")
        self.chat_send = QPushButton("Senden")
        self.read_aloud = QPushButton("Vorlesen")
        self.chat_row.addWidget(self.chat_input, 1)
        self.chat_row.addWidget(self.chat_send)
        self.chat_row.addWidget(self.read_aloud)
        self.chat_input.setVisible(True)
        self.chat_send.setVisible(True)
        self.read_aloud.setVisible(False)
        root.addLayout(self.chat_row)

        actions = QGridLayout()
        actions.setHorizontalSpacing(10)
        actions.setVerticalSpacing(8)

        self.talk_button = QPushButton("LiveTalk")
        self.video_frames_toggle = QCheckBox("Maya sieht Bildschirm")
        self.exit_livetalk = QPushButton("LiveTalk beenden")
        self.cue_approve = QPushButton("Cue freigeben")
        self.cue_reject = QPushButton("Cue ablehnen")
        self.exit_livetalk.setVisible(False)
        self.video_frames_toggle.setVisible(False)
        self.cue_approve.setEnabled(False)
        self.cue_reject.setEnabled(False)

        actions.addWidget(self.talk_button, 0, 0)
        actions.addWidget(self.exit_livetalk, 0, 1)
        actions.addWidget(self.video_frames_toggle, 1, 0, 1, 2)
        actions.addWidget(self.cue_approve, 2, 0)
        actions.addWidget(self.cue_reject, 2, 1)
        self.actions_layout = actions
        root.addLayout(self.actions_layout)

        self.vision_panel = QFrame(self)
        self.vision_panel.setObjectName("panel")
        vision_grid = QGridLayout(self.vision_panel)
        vision_grid.setContentsMargins(10, 8, 10, 8)
        vision_grid.setHorizontalSpacing(8)
        vision_grid.setVerticalSpacing(6)
        self.vision_provider = QComboBox()
        self.vision_provider.addItem("Gemini Flash Lite", "gemini_flash_lite")
        self.vision_provider.addItem("Grok 4.3", "grok_4_3")
        self.vision_provider.addItem("Gemini Flash", "gemini_flash")
        self.vision_reasoning = QComboBox()
        self.vision_reasoning.addItem("Denkmodus: schnell", "minimal")
        self.vision_reasoning.addItem("Denkmodus: niedrig", "low")
        self.vision_reasoning.addItem("Denkmodus: mittel", "medium")
        self.vision_reasoning.addItem("Denkmodus: hoch", "high")
        self.screen_context_button = QPushButton("Bildschirm pruefen")
        vision_grid.addWidget(self.vision_provider, 0, 0)
        vision_grid.addWidget(self.vision_reasoning, 0, 1)
        vision_grid.addWidget(self.screen_context_button, 1, 0, 1, 2)
        self.vision_panel.setVisible(False)
        self._set_reasoning_tooltips()

        self.setStyleSheet(
            """
            QWidget {
                background: #17191f;
                color: #f2f4f8;
                font-family: Segoe UI;
                font-size: 13px;
            }
            QLabel#title {
                font-size: 18px;
                font-weight: 600;
            }
            QFrame#panel {
                border: 1px solid #3a3f4b;
                border-radius: 10px;
                background: #20232b;
            }
            QLabel#chip {
                border: 1px solid #3a3f4b;
                border-radius: 10px;
                background: #20232b;
                padding: 7px 9px;
                color: #d7dce6;
            }
            QLabel#target {
                color: #ffd94a;
                font-weight: 600;
                padding: 4px 6px;
            }
            QLabel#output {
                background: #17191f;
                border: 1px solid #2f3542;
                border-radius: 10px;
                padding: 8px 9px;
                min-height: 44px;
            }
            QPushButton {
                background: #2d3340;
                border: 1px solid #4a5364;
                border-radius: 10px;
                padding: 8px 10px;
                color: #d7dce6;
            }
            QPushButton:hover {
                background: #394254;
                border-color: #6c7890;
            }
            QPushButton:pressed {
                background: #242a35;
            }
            QPushButton:disabled {
                color: #8d95a3;
                background: #252b36;
            }
            QCheckBox {
                color: #d7dce6;
                padding: 3px 2px;
            }
            QComboBox, QLineEdit {
                background: #2d3340;
                border: 1px solid #4a5364;
                border-radius: 10px;
                padding: 5px 8px;
                color: #d7dce6;
            }
            QComboBox:hover, QLineEdit:hover {
                border-color: #6c7890;
            }
            QLineEdit:focus {
                border-color: #ffd94a;
            }
            """
        )

    def _chip(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("chip")
        label.setWordWrap(True)
        return label

    def set_livetalk_mode(self, active: bool, focus_chat: bool = True) -> None:
        self.connection_chip.setVisible(not active)
        self.cue_approve.setVisible(not active)
        self.cue_reject.setVisible(not active)
        self.exit_livetalk.setVisible(active)
        self.video_frames_toggle.setVisible(active)
        self.target_value.setVisible(not active)
        self.chat_input.setVisible(True)
        self.chat_send.setVisible(True)
        if not active:
            self.read_aloud.setVisible(False)
            self.read_aloud.setEnabled(True)
            self.read_aloud.setText("Vorlesen")
        self.talk_button.setText("Halten zum Sprechen" if active else "LiveTalk")
        width, height = self._livetalk_size if active else self._preferred_size
        self.resize(width, height)
        self.ensure_visible()
        if active and focus_chat:
            self.chat_input.setFocus()

    def _set_reasoning_tooltips(self) -> None:
        self.vision_reasoning.setItemData(0, "Schnellste Antwort (ca. 700ms), Standard", Qt.ItemDataRole.ToolTipRole)
        self.vision_reasoning.setItemData(1, "Mehr Nachdenken (1-2s)", Qt.ItemDataRole.ToolTipRole)
        self.vision_reasoning.setItemData(2, "Tiefes Verstaendnis (3-5s)", Qt.ItemDataRole.ToolTipRole)
        self.vision_reasoning.setItemData(3, "Maximale Praezision (5-10s), nur fuer komplexe Faelle", Qt.ItemDataRole.ToolTipRole)
