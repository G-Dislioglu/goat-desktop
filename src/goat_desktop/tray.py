from __future__ import annotations

import json
import os
import urllib.request
from importlib import resources
from threading import Thread

from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QAction, QIcon, QPainter, QPixmap
from PyQt6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from goat_desktop.builder_bridge import BuilderBridgeClient
from goat_desktop.bridge import CueDispatcher, LocalBridge
from goat_desktop.chat_hint import request_chat_response
from goat_desktop.hotkey import EmergencyHotkey, VK_G
from goat_desktop.livetalk import LiveTalkSession
from goat_desktop.overlay import BallOverlay
from goat_desktop.popup import GoatPopup
from goat_desktop.stt_hint import load_stt_config
from goat_desktop.tts_hint import load_tts_config
from goat_desktop.vision_config import load_vision_config, save_vision_config


class GoatTrayApp:
    def __init__(self, app: QApplication) -> None:
        if not QSystemTrayIcon.isSystemTrayAvailable():
            raise RuntimeError("Windows system tray is not available")

        self.app = app
        self.overlay = BallOverlay()
        self.popup = GoatPopup()
        self._ball_visible = True
        self.last_test_cue_response: dict | None = None
        self.last_test_cue_error: str | None = None
        self.pending_builder_cue: dict | None = None
        self.last_builder_cue_response: dict | None = None
        self.builder_bridge: BuilderBridgeClient | None = None
        self.livetalk = LiveTalkSession(
            status_callback=self._update_livetalk_status,
            response_callback=self._update_livetalk_response,
        )
        self.cue_dispatcher = CueDispatcher()
        self.cue_dispatcher.cue_requested.connect(self.move_ball_to_cue)
        self.bridge = LocalBridge(self.cue_dispatcher)
        self._connect_popup_controls()
        self.overlay.show_overlay()
        self.popup.place_near_tray()
        self.popup.show()
        self.hotkey = EmergencyHotkey(self.emergency_stop)
        self.show_hotkey = EmergencyHotkey(self.show_popup, hotkey_id=0x470B, virtual_key=VK_G)
        self.tray = QSystemTrayIcon(self._load_icon(), app)
        self.tray.setToolTip("GOAT Desktop")
        self.tray.activated.connect(self._on_activated)
        self.tray.setContextMenu(self._build_menu())
        self.tray.show()
        self.bridge.start()
        self._start_builder_bridge_if_configured()
        self._load_vision_config()
        self._refresh_audio_status()

    def show_popup(self) -> None:
        if not self.popup.isVisible():
            self.popup.place_near_tray()
        self.popup.showNormal()
        self.popup.restore_preferred_size()
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

    def hide_ball(self) -> None:
        self._ball_visible = False
        self.overlay.hide_ball()

    def move_ball_to_cue(self, x: int, y: int) -> None:
        self._ball_visible = True
        self.overlay.move_ball_to(x - self.overlay.width() // 2, y - self.overlay.height() // 2)
        self.popup.target_value.setText(f"Ziel markiert: x={x}, y={y}")

    def emergency_stop(self) -> None:
        self.hide_ball()
        self.popup.hide()

    def shutdown(self) -> None:
        if self.builder_bridge is not None:
            self.builder_bridge.stop()
        self.bridge.stop()
        self.hotkey.unregister()
        self.show_hotkey.unregister()
        self.overlay.hide()
        self.app.quit()

    def _connect_popup_controls(self) -> None:
        self.popup.cue_approve.clicked.connect(self.approve_pending_cue)
        self.popup.cue_reject.clicked.connect(self.reject_pending_cue)
        self.popup.talk_button.clicked.connect(self.run_livetalk_once)
        self.popup.exit_livetalk.clicked.connect(self.exit_livetalk_mode)
        self.popup.chat_send.clicked.connect(self.send_chat_message)
        self.popup.chat_input.returnPressed.connect(self.send_chat_message)
        self.popup.vision_provider.currentIndexChanged.connect(self._save_vision_config)
        self.popup.vision_reasoning.currentIndexChanged.connect(self._save_vision_config)

    def _load_vision_config(self) -> None:
        config = load_vision_config()
        provider_index = self.popup.vision_provider.findData(config["provider"])
        reasoning_index = self.popup.vision_reasoning.findData(config["reasoning_level"])
        if provider_index >= 0:
            self.popup.vision_provider.setCurrentIndex(provider_index)
        if reasoning_index >= 0:
            self.popup.vision_reasoning.setCurrentIndex(reasoning_index)

    def _save_vision_config(self, *_args) -> None:
        save_vision_config(
            str(self.popup.vision_provider.currentData()),
            str(self.popup.vision_reasoning.currentData()),
        )

    def run_livetalk_once(self) -> None:
        self.popup.set_livetalk_mode(True)
        self.popup.talk_button.setEnabled(False)
        self._refresh_audio_status()
        self.popup.screen_context_value.setText("LiveTalk bereit")
        self.popup.maya_value.setText("Half-Duplex")
        QApplication.processEvents()
        try:
            result = self.livetalk.run_once()
            self.popup.screen_context_value.setText(result.transcript)
            self.popup.maya_value.setText(result.response_text)
            self.popup.audio_value.setText(
                "STT {stt:.0f}ms / Chat {chat:.0f}ms / TTS {tts} / Aufnahme {rec:.1f}s".format(
                    stt=result.stt_time_ms,
                    chat=result.chat_time_ms,
                    tts=("aus" if result.audio_pending else f"{result.tts_time_ms:.0f}ms"),
                    rec=result.record_seconds,
                )
            )
        except Exception as exc:
            self.popup.screen_context_value.setText("LiveTalk Fehler")
            self.popup.maya_value.setText(str(exc))
        finally:
            self.popup.talk_button.setEnabled(True)

    def exit_livetalk_mode(self) -> None:
        self.popup.set_livetalk_mode(False)
        self.popup.screen_context_value.setText("-")
        self.popup.maya_value.setText("bereit, pausiert")

    def send_chat_message(self) -> None:
        text = self.popup.chat_input.text().strip()
        if not text:
            return
        self.popup.chat_input.clear()
        self.popup.screen_context_value.setText(text)
        self.popup.maya_value.setText("Maya wird angefragt...")
        QApplication.processEvents()
        result = request_chat_response(
            text,
            context={
                "screen_context": self.popup.screen_context_value.text(),
                "target": self.popup.target_value.text(),
                "safety_rule": "desktop actions require explicit user approval",
            },
        )
        self.popup.maya_value.setText(result.response_text)

    def _refresh_audio_status(self) -> None:
        stt = load_stt_config()
        tts = load_tts_config()
        stt_ready = stt.mode.value == "builder_proxy" and bool(stt.builder_url and stt.builder_token)
        auto_tts = os.environ.get("GOAT_LIVETALK_AUTO_TTS", "").strip().lower() in {"1", "true", "yes", "on"}
        tts_ready = auto_tts and tts.mode.value == "builder_proxy" and bool(tts.builder_url and tts.builder_token)
        stt_label = "STT Builder aktiv" if stt_ready else f"STT {stt.mode.value}"
        if tts_ready:
            tts_label = "TTS Builder aktiv"
        elif not auto_tts:
            tts_label = "Sprachausgabe aus"
        else:
            tts_label = f"TTS {tts.mode.value}"
        text = f"{stt_label} / {tts_label}"
        self.popup.audio_value.setText(text)
        self.popup.audio_chip.setText(f"Audio: {text}")

    def _update_livetalk_status(self, state: str) -> None:
        labels = {
            "prepare": ("Gleich sprechen", "Nach dem Ton sprechen"),
            "listening": ("Nimmt auf", "Jetzt sprechen"),
            "thinking": ("Verarbeite Sprache", "Builder-STT laeuft"),
            "speaking": ("Maya-Antwort steht", "Audio wird geladen"),
            "idle": ("bereit", "bereit, pausiert"),
        }
        screen_text, maya_text = labels.get(state, (state, "Half-Duplex"))
        self.popup.screen_context_value.setText(screen_text)
        self.popup.maya_value.setText(maya_text)
        QApplication.processEvents()

    def _update_livetalk_response(self, transcript: str, response_text: str) -> None:
        self.popup.screen_context_value.setText(transcript)
        self.popup.maya_value.setText(response_text)
        QApplication.processEvents()

    def request_test_cue(self) -> None:
        self.popup.hide()
        QTimer.singleShot(250, self._post_test_cue)

    def _post_test_cue(self) -> None:
        Thread(target=self._post_test_cue_worker, name="goat-test-cue", daemon=True).start()

    def _post_test_cue_worker(self) -> None:
        payload = json.dumps({"source": "active_window", "label": "Popup test cue"}).encode("utf-8")
        request = urllib.request.Request(
            "http://127.0.0.1:8765/screen-cue",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=5) as response:
                self.last_test_cue_response = json.loads(response.read().decode("utf-8"))
                self.last_test_cue_error = None
        except Exception as exc:
            self.last_test_cue_response = None
            self.last_test_cue_error = repr(exc)

    def _start_builder_bridge_if_configured(self) -> None:
        url = os.environ.get("GOAT_BUILDER_WS_URL")
        token = os.environ.get("GOAT_BUILDER_TOKEN")
        if not url or not token:
            self.popup.connection_value.setText("lokal")
            self.popup.connection_chip.setText("Verbindung: lokal")
            return
        self.builder_bridge = BuilderBridgeClient(url=url, token=token)
        self.builder_bridge.status_changed.connect(self._update_connection_status)
        self.builder_bridge.cue_received.connect(self.receive_builder_cue)
        self.builder_bridge.start()

    def _update_connection_status(self, text: str) -> None:
        self.popup.connection_value.setText(text)
        self.popup.connection_chip.setText(f"Verbindung: {text}")

    def receive_builder_cue(self, message: dict) -> None:
        self.pending_builder_cue = {
            "source": message.get("source", "active_window"),
            "label": message.get("label", "Builder test cue"),
            "bbox": message.get("bbox"),
            "confidence": message.get("confidence", 0.9),
        }
        if self.pending_builder_cue["bbox"] is None:
            self.pending_builder_cue.pop("bbox")
        label = str(self.pending_builder_cue.get("label") or "Builder-Cue")
        self.popup.target_value.setText(f"Zielvorschlag: {label}")
        self.popup.screen_context_value.setText("Builder-Cue wartet")
        self.popup.maya_value.setText("Freigabe erforderlich")
        self.popup.cue_approve.setEnabled(True)
        self.popup.cue_reject.setEnabled(True)
        self.show_popup()

    def approve_pending_cue(self) -> None:
        if self.pending_builder_cue is None:
            return
        payload = dict(self.pending_builder_cue)
        self.popup.cue_approve.setEnabled(False)
        self.popup.cue_reject.setEnabled(False)
        self.popup.hide()
        QTimer.singleShot(250, lambda: self._approve_pending_cue(payload))

    def _approve_pending_cue(self, payload: dict) -> None:
        Thread(target=self._approve_pending_cue_worker, args=(payload,), name="goat-builder-cue", daemon=True).start()

    def _approve_pending_cue_worker(self, payload: dict) -> None:
        request = urllib.request.Request(
            "http://127.0.0.1:8765/screen-cue",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=5) as response:
                self.last_builder_cue_response = json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            self.last_builder_cue_response = {"safety_state": "stop", "error": repr(exc)}

    def reject_pending_cue(self) -> None:
        self.pending_builder_cue = None
        self.popup.target_value.setText("Kein Ziel markiert")
        self.popup.screen_context_value.setText("Builder-Cue abgelehnt")
        self.popup.maya_value.setText("bereit, pausiert")
        self.popup.cue_approve.setEnabled(False)
        self.popup.cue_reject.setEnabled(False)

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
