from __future__ import annotations

import json
import os
import tempfile
import threading
import urllib.request
from pathlib import Path
from importlib import resources
from threading import Thread
from time import perf_counter

from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QAction, QIcon, QPainter, QPixmap
from PyQt6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from goat_desktop.action_gate import ActionStage, classify_action_with_reason
from goat_desktop.action_preview import build_action_preview
from goat_desktop.builder_bridge import BuilderBridgeClient
from goat_desktop.bridge import CueDispatcher, LocalBridge
from goat_desktop.chat_hint import request_chat_response
from goat_desktop.hotkey import EmergencyHotkey, VK_G
from goat_desktop.livetalk import LiveTalkSession, read_response_aloud, start_windows_wav_recording
from goat_desktop.livetalk_live import GeminiLiveSession
from goat_desktop.overlay import BallOverlay
from goat_desktop.popup import GoatPopup
from goat_desktop.redaction import SENSITIVE_TARGET_LABEL
from goat_desktop.screen import capture_visible_desktop
from goat_desktop.stage2_executor import MAX_STAGE2_TEXT_LENGTH
from goat_desktop.screen_context import (
    VISION_CONTEXT_PROMPT,
    build_chat_context,
    build_local_screen_miss_summary,
    build_screen_marker_from_hint,
    build_screen_context_display_status,
    build_screen_context_fallback_response,
    build_screen_context_prompt,
    build_screen_context_summary,
    is_unavailable_chat_response,
    should_answer_screen_question_locally,
    should_use_screen_context,
    should_use_vision_fallback,
)
from goat_desktop.stt_hint import load_stt_config
from goat_desktop.tts_hint import load_tts_config
from goat_desktop.uia_context import (
    build_uia_marker,
    build_uia_screen_context,
    find_uia_match_for_message,
    get_resolver_cache_status,
    warm_taskbar_cache,
    warm_window_cache,
)
from goat_desktop.vision_config import load_vision_config, save_vision_config
from goat_desktop.vision_hint import (
    ReasoningLevel,
    VisionHintConfig,
    VisionMode,
    VisionProvider,
    get_vision_hint,
    load_vision_hint_config,
)

_RESOLVER_CACHE_REFRESH_INTERVAL_MS = 60_000
_LOCAL_ACTION_TIMEOUT_SECONDS = 2
_POST_APPROVAL_ACTION_DELAY_MS = 150


def _no_action_effects() -> dict[str, bool]:
    return {
        "providerCallsMade": False,
        "desktopActionsExecuted": False,
        "mouseActionsExecuted": False,
        "keyboardActionsExecuted": False,
        "tradingActionsExecuted": False,
        "mayExecuteRealAction": False,
    }


def _resolver_cache_refresh_interval_ms() -> int:
    raw = os.getenv("GOAT_RESOLVER_CACHE_REFRESH_MS", "").strip()
    if not raw:
        return _RESOLVER_CACHE_REFRESH_INTERVAL_MS
    try:
        return max(10_000, int(raw))
    except ValueError:
        return _RESOLVER_CACHE_REFRESH_INTERVAL_MS


def _start_resolver_cache_warmup_once() -> None:
    Thread(target=warm_taskbar_cache, name="goat-taskbar-cache-warmup", daemon=True).start()
    Thread(target=warm_window_cache, name="goat-window-cache-warmup", daemon=True).start()


def _is_stage1_navigation_action(action_type: str) -> bool:
    normalized = action_type.strip().lower()
    return any(token in normalized for token in ("hover", "move", "scroll"))


def _is_stage2_text_action(action_type: str) -> bool:
    normalized = action_type.strip().lower()
    return any(token in normalized for token in ("type", "text", "input"))


def _stage1_scroll_amount(message: dict) -> int:
    value = message.get("scroll_amount")
    if value is None or value == "":
        return -360
    try:
        amount = int(float(value))
    except (TypeError, ValueError):
        return -360
    return amount if amount != 0 else -360


def _normalized_stage1_action_type(action_type: str) -> str:
    normalized = action_type.strip().lower()
    if "scroll" in normalized:
        return "scroll"
    if "move" in normalized and "hover" not in normalized:
        return "move"
    return "hover"


def _pending_action_hint(
    stage1_action: dict | None,
    stage2_action: dict | None,
    stage3_action: dict | None = None,
    stage4_action: dict | None = None,
) -> str:
    if stage1_action:
        return "Danach kannst du GOAT navigieren lassen."
    if stage2_action:
        return "Danach kannst du die Eingabe freigeben."
    if stage3_action:
        return "Danach zeigt GOAT dir die wichtige Aktion nur zur Pruefung."
    if stage4_action:
        return "Das wirkt sensibel. GOAT wird das nicht ausfuehren."
    return "Nur mit deiner Freigabe geht es weiter."


def _status_chip_text(connection_text: str) -> str:
    normalized = connection_text.strip().lower()
    if "already running" in normalized or "port_in_use" in normalized or "schon" in normalized:
        return "Status: Schon offen"
    if not normalized or normalized in {"lokal", "offline"}:
        return "Status: Bereit"
    if "connected" in normalized or "verbunden" in normalized:
        return "Status: Verbunden"
    if "reconnecting" in normalized or "verbind" in normalized:
        return "Status: Verbinde neu"
    return "Status: Bereit"


def _speech_chip_text(audio_text: str) -> str:
    normalized = audio_text.strip().lower()
    if not normalized or normalized == "-":
        return "Sprache: Bereit"
    if "fehlgeschlagen" in normalized or "nicht moeglich" in normalized:
        return "Sprache: Problem"
    if "laedt" in normalized or "lädt" in normalized or "denke" in normalized:
        return "Sprache: Arbeitet"
    if "aktiv" in normalized:
        return "Sprache: Bereit"
    if "ms" in normalized or "vorgelesen" in normalized:
        return "Sprache: Fertig"
    return "Sprache: Bereit"


def _pending_target_text(label: str, stage2_action: dict | None) -> str:
    if stage2_action:
        return f"Eingabefeld: {label}"
    return f"Zielvorschlag: {label}"


def _pending_check_text(stage2_action: dict | None) -> str:
    if stage2_action:
        return "Schritt 1: Eingabefeld pruefen"
    return "Schritt 1: Ziel pruefen"


def _execution_step_title(preview: dict) -> str:
    title = str(preview.get("title") or "Freigabe erforderlich")
    return f"Schritt 2: {title}"


def _stage3_review_step_title(preview: dict) -> str:
    status = str(preview.get("reviewStatus") or "Nur Review - keine Ausfuehrung")
    return f"Schritt 2: {status}"


def _stage2_preview_message(stage2_action: dict, preview: dict) -> str:
    if not stage2_action.get("safe_text_context"):
        return "Ich tippe hier noch nicht. Sag mir genauer, welches Feld das ist, oder zeig es deutlicher."
    text_guard = _stage2_text_guard(stage2_action)
    if text_guard == "empty":
        return "Ich tippe hier noch nicht. Mir fehlt noch der Text, den ich eintragen soll."
    if text_guard == "multi_line":
        return "Mehrzeilige Texte tippe ich noch nicht automatisch. Bitte gib mir eine kurze einzeilige Eingabe."
    if text_guard == "too_long":
        return f"Der Text ist zu lang. Ich tippe aktuell hoechstens {MAX_STAGE2_TEXT_LENGTH} Zeichen automatisch."
    message = str(preview.get("message") or "Bitte pruefe die Eingabe.")
    return f"{message} Klicke nur auf Ausfuehren, wenn Feld und Text stimmen."


def _stage2_text_guard(stage2_action: dict) -> str | None:
    text = str(stage2_action.get("text") or "")
    if not text.strip():
        return "empty"
    if "\n" in text or "\r" in text:
        return "multi_line"
    if len(text) > MAX_STAGE2_TEXT_LENGTH:
        return "too_long"
    return None


def _stage2_approve_label(stage2_action: dict) -> str:
    if not stage2_action.get("safe_text_context"):
        return "Nicht sicher"
    text_guard = _stage2_text_guard(stage2_action)
    if text_guard == "empty":
        return "Kein Text"
    if text_guard == "multi_line":
        return "Mehrzeilig"
    if text_guard == "too_long":
        return "Zu lang"
    return "Ausfuehren"


def _stage1_preview_message(preview: dict) -> str:
    message = str(preview.get("message") or "Bitte pruefe die Aktion.")
    approve_label = str(preview.get("primaryButton") or "Navigieren")
    return f"{message} Gib {approve_label} nur frei, wenn das markierte Ziel stimmt."


def _stage3_review_message(preview: dict) -> str:
    action_text = str(preview.get("actionText") or "eine wichtige Aktion ausloesen")
    guidance = str(preview.get("reviewGuidance") or "Pruefe die Folgen selbst und fuehre die Aktion nur aus, wenn du sicher bist.")
    return f"GOAT will {action_text}. Das kann Folgen haben und braucht deine klare Freigabe. {guidance}"


def _stage4_locked_message(preview: dict) -> str:
    action_text = str(preview.get("actionText") or "ein sensibles Feld bearbeiten")
    return f"GOAT fuehrt das nicht aus: {action_text}. Bitte erledige sensible Eingaben selbst im Programm."


def _set_review_status(popup: object, text: str = "") -> None:
    label = getattr(popup, "review_status_value", None)
    if label is None:
        return
    label.setText(text)
    label.setVisible(bool(text))


def _friendly_action_failure_message(response: dict, *, stage: str) -> str:
    reason = str(response.get("reason") or "").strip()
    lowered = reason.lower()
    if stage == "stage2_done":
        if "backend failed" in lowered:
            return "Die Eingabe hat nicht geklappt. Ich melde sie nicht als erledigt."
        if "verification failed" in lowered:
            return "Ich bin nicht sicher, ob die Eingabe angekommen ist. Ich melde sie nicht als erledigt."
        if "safe_text_context" in lowered:
            return "Ich tippe hier nicht. Sag mir genauer, welches Feld das ist, oder zeig es deutlicher."
        if "empty" in lowered:
            return "Ich tippe keinen leeren Text ein."
        if "multi-line" in lowered:
            return "Mehrzeilige Texte tippe ich noch nicht automatisch."
        if "exceeds" in lowered:
            return "Der Text ist zu lang. Bitte kuerzer formulieren."
        if "final_bbox" in lowered:
            return "Ich kenne die genaue Position des Eingabefelds nicht sicher genug."
        if "approval" in lowered or "preview" in lowered or "dry_run" in lowered:
            return "Bitte pruefe die Eingabe erst im GOAT-Fenster."
        return "Ich habe nichts eingetippt. Bitte pruefe Feld und Text erneut."
    action_type = str(response.get("action_type") or "").strip().lower()
    if "backend failed" in lowered:
        if action_type == "scroll":
            return "Ich konnte die Seite nicht scrollen. Ich melde es nicht als erledigt."
        return "Ich konnte den Mauszeiger nicht zum Ziel bewegen. Ich melde es nicht als erledigt."
    if "verification failed" in lowered:
        return "Ich bin nicht sicher, ob der Mauszeiger am Ziel angekommen ist. Ich melde es nicht als erledigt."
    if "approval" in lowered or "preview" in lowered or "dry_run" in lowered:
        return "Bitte gib die Navigation erst im GOAT-Fenster frei."
    return reason or "Bitte pruefe das Ziel erneut."


def _friendly_builder_cue_failure_message(payload: dict) -> str:
    reason = str(payload.get("reason") or payload.get("error") or "").strip().lower()
    if "bbox" in reason or "outside active window" in reason or "geometry" in reason:
        return "Ich konnte das Ziel nicht sicher zuordnen. Bitte zeig mir nochmal, welches Ziel du meinst."
    if "source" in reason or "vision" in reason:
        return "Ich brauche ein klar erkanntes Ziel auf deinem Bildschirm, bevor ich etwas vorbereite."
    if "action_type" in reason or "label" in reason:
        return "Mir fehlt noch, was genau ich mit dem Ziel machen soll. Sag es bitte nochmal kurz."
    if "timed out" in reason or "timeout" in reason or "connection" in reason:
        return "Die lokale Pruefung hat gerade nicht geantwortet. Bitte versuch es nochmal."
    return "Ich konnte das Ziel nicht sicher erkennen. Bitte beschreib es nochmal oder zeig es deutlicher."


def _friendly_stage1_success_message(response: dict) -> str:
    action_type = str(response.get("action_type") or "").strip().lower()
    target = response.get("target") if isinstance(response.get("target"), dict) else {}
    if action_type == "scroll":
        amount = int(target.get("scroll_amount") or 0)
        direction = "nach unten" if amount < 0 else "nach oben"
        return f"Ich habe die Seite {direction} gescrollt. Sag mir einfach, was als Naechstes dran ist."
    return "Ich habe den Mauszeiger zum Ziel bewegt. Du kannst jetzt weitermachen oder mir den naechsten Schritt sagen."


def _friendly_stage1_success_title(response: dict) -> str:
    action_type = str(response.get("action_type") or "").strip().lower()
    if action_type == "scroll":
        return "Scrollen ausgefuehrt"
    return "Mauszeiger bewegt"


def _friendly_stage1_failure_title(response: dict) -> str:
    action_type = str(response.get("action_type") or "").strip().lower()
    if action_type == "scroll":
        return "Scrollen nicht ausgefuehrt"
    if action_type in {"hover", "move"}:
        return "Mauszeiger nicht bewegt"
    return "Navigation nicht ausgefuehrt"


def _friendly_stage2_success_message(response: dict) -> str:
    preview = response.get("preview") if isinstance(response.get("preview"), dict) else {}
    label = str(preview.get("label") or "das Eingabefeld").strip() or "das Eingabefeld"
    return f"Ich habe den Text in {label} eingetragen. Bitte pruefe kurz, ob er stimmt."


def _action_completion_verified(response: dict) -> bool:
    return bool(response.get("executed")) and bool(response.get("completion_verified", response.get("executed")))


def _build_resolver_evidence(screen_resolution: object) -> dict[str, object]:
    resolution = screen_resolution if isinstance(screen_resolution, dict) else {}
    return {
        "source": resolution.get("source"),
        "source_path": resolution.get("source_path"),
        "cache_hit": resolution.get("cache_hit"),
        "cache_refreshed": resolution.get("cache_refreshed"),
        "time_ms": resolution.get("time_ms"),
        "elements_scanned": resolution.get("elements_scanned"),
    }


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
        self.pending_stage1_action: dict | None = None
        self.pending_stage2_action: dict | None = None
        self.pending_stage3_action: dict | None = None
        self.pending_stage4_action: dict | None = None
        self.last_builder_cue_response: dict | None = None
        self.builder_bridge: BuilderBridgeClient | None = None
        self._read_aloud_text = ""
        self._read_aloud_request_id = 0
        self._push_to_talk_stop_event: threading.Event | None = None
        self._push_to_talk_recorder = None
        self._push_to_talk_started = 0.0
        self._push_to_talk_click_handled = False
        self._last_screen_context = ""
        self._screen_context_provider = "gemini_flash_lite"
        self._screen_context_reasoning = "minimal"
        if _livetalk_fallback_enabled():
            self.livetalk = LiveTalkSession(
                status_callback=self._update_livetalk_status,
                response_callback=self._update_livetalk_response,
            )
        else:
            self.livetalk = GeminiLiveSession()
        self.cue_dispatcher = CueDispatcher()
        self.cue_dispatcher.cue_requested.connect(self.move_ball_to_cue)
        self.cue_dispatcher.builder_cue_requested.connect(self.receive_builder_cue)
        self.bridge = LocalBridge(self.cue_dispatcher, screen_question_handler=self.handle_bridge_screen_question)
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
        self._handle_bridge_start_result(self.bridge.start())
        _start_resolver_cache_warmup_once()
        self._resolver_cache_timer = QTimer()
        self._resolver_cache_timer.setInterval(_resolver_cache_refresh_interval_ms())
        self._resolver_cache_timer.timeout.connect(_start_resolver_cache_warmup_once)
        self._resolver_cache_timer.start()
        self._start_builder_bridge_if_configured()
        self._load_vision_config()
        self.popup.video_frames_toggle.setChecked(_video_frames_enabled())
        self._refresh_audio_status()

    def _handle_bridge_start_result(self, result: dict | None) -> None:
        if not result or result.get("ok"):
            return
        if result.get("status") == "port_in_use":
            self.popup.connection_value.setText("GOAT laeuft schon")
            self.popup.connection_chip.setText(_status_chip_text("already running"))
            self.popup.screen_context_value.setText("GOAT ist bereits offen")
            self.popup.maya_value.setText("Bitte nutze das vorhandene GOAT-Fenster. Diese Instanz fuehrt nichts aus.")
            self.popup.cue_approve.setEnabled(False)
            self.popup.cue_reject.setEnabled(False)
            return
        self.popup.connection_value.setText("Startproblem")
        self.popup.connection_chip.setText("Status: Problem")
        self.popup.screen_context_value.setText("GOAT konnte nicht vollstaendig starten")
        self.popup.maya_value.setText("Bitte starte GOAT neu.")

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
        self.popup.target_value.setText(f"Ziel gefunden: x={x}, y={y}")

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
        self.popup.talk_button.pressed.connect(self.start_push_to_talk)
        self.popup.talk_button.released.connect(self.finish_push_to_talk)
        self.popup.talk_button.clicked.connect(self.run_gemini_live)
        self.popup.exit_livetalk.clicked.connect(self.exit_livetalk_mode)
        self.popup.chat_send.clicked.connect(self.send_chat_message)
        self.popup.chat_input.returnPressed.connect(self.send_chat_message)
        self.popup.read_aloud.clicked.connect(self.read_livetalk_response_aloud)
        self.popup.read_aloud_finished.connect(self._finish_read_livetalk_response_aloud)
        self.popup.push_to_talk_finished.connect(self._finish_push_to_talk_payload)
        self.popup.builder_cue_finished.connect(self._finish_builder_cue)
        self.popup.chat_finished.connect(self._finish_chat_message)
        self.popup.video_frames_toggle.toggled.connect(self._set_video_frames_enabled)
        self.popup.screen_context_button.clicked.connect(self.request_screen_context)
        self.popup.screen_context_finished.connect(self._finish_screen_context)
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

    def _set_video_frames_enabled(self, enabled: bool) -> None:
        os.environ["GOAT_LIVETALK_VIDEO_FRAMES"] = "1" if enabled else "0"

    def run_livetalk_once(self) -> None:
        if self._push_to_talk_click_handled:
            self._push_to_talk_click_handled = False
            return
        self.popup.set_livetalk_mode(True)
        self.popup.talk_button.setEnabled(False)
        self._set_read_aloud_available("")
        self._refresh_audio_status()
        self.popup.screen_context_value.setText("Bereit zum Zuhoeren")
        self.popup.maya_value.setText("Halte den Button und sprich.")
        QApplication.processEvents()
        try:
            result = self.livetalk.run_once()
            self.popup.screen_context_value.setText(result.transcript)
            self.popup.maya_value.setText(result.response_text)
            self._set_read_aloud_available(result.response_text if result.audio_pending else "")
            if result.provider == "gemini_live":
                self.popup.audio_value.setText(
                    "Gemini Live {time:.0f}ms / Aufnahme {rec:.1f}s".format(
                        time=result.chat_time_ms,
                        rec=result.record_seconds,
                    )
                )
            else:
                self.popup.audio_value.setText(
                    "STT {stt:.0f}ms / Chat {chat:.0f}ms / TTS {tts} / Aufnahme {rec:.1f}s".format(
                        stt=result.stt_time_ms,
                        chat=result.chat_time_ms,
                        tts=("aus" if result.audio_pending else f"{result.tts_time_ms:.0f}ms"),
                        rec=result.record_seconds,
                    )
                )
        except Exception as exc:
            self.popup.screen_context_value.setText("Sprechen gerade nicht moeglich")
            self.popup.maya_value.setText(str(exc))
        finally:
            self.popup.talk_button.setEnabled(True)

    def run_gemini_live(self) -> None:
        self.run_livetalk_once()

    def start_push_to_talk(self) -> None:
        if self.livetalk.provider != "gemini_live" or self._push_to_talk_stop_event is not None:
            return
        self._push_to_talk_click_handled = True
        self.popup.set_livetalk_mode(True, focus_chat=False)
        self._set_read_aloud_available("")
        self._refresh_audio_status()
        self.livetalk.audio_dir.mkdir(parents=True, exist_ok=True)
        audio_path = self.livetalk.audio_dir / "livetalk-last-recording.wav"
        max_seconds = float(os.environ.get("GOAT_LIVETALK_PUSH_TO_TALK_MAX_SECONDS", "30.0"))
        self._push_to_talk_started = perf_counter()
        self._push_to_talk_stop_event = threading.Event()
        self.popup.screen_context_value.setText("Ich hoere zu")
        self.popup.maya_value.setText("Loslassen zum Senden")
        self.popup.talk_button.setText("Loslassen zum Senden")
        QApplication.processEvents()
        if _streaming_livetalk_enabled():
            Thread(
                target=self._push_to_talk_stream_worker,
                args=(self._push_to_talk_stop_event, max_seconds, self._push_to_talk_started),
                name="goat-push-to-talk-stream",
                daemon=True,
            ).start()
        else:
            self._push_to_talk_recorder = start_windows_wav_recording(audio_path, max_seconds=max_seconds)
        QTimer.singleShot(int(max_seconds * 1000), self.finish_push_to_talk)

    def finish_push_to_talk(self) -> None:
        stop_event = self._push_to_talk_stop_event
        recorder = self._push_to_talk_recorder
        if stop_event is None and recorder is None:
            return
        self._push_to_talk_stop_event = None
        self._push_to_talk_recorder = None
        if stop_event is not None:
            stop_event.set()
        self.popup.talk_button.setEnabled(False)
        self.popup.talk_button.setText("Sende...")
        self.popup.screen_context_value.setText("Ich denke nach")
        self.popup.maya_value.setText("Maya antwortet gleich")
        QApplication.processEvents()
        if recorder is not None:
            Thread(
                target=self._finish_push_to_talk_recorded_worker,
                args=(recorder, self._push_to_talk_started),
                name="goat-push-to-talk-recorded",
                daemon=True,
            ).start()

    def _push_to_talk_stream_worker(self, stop_event: threading.Event, max_seconds: float, started: float) -> None:
        try:
            result = self.livetalk.run_stream(stop_event, max_seconds=max_seconds)
            record_seconds = float(result.raw_evidence.get("record_seconds") or round(perf_counter() - started, 2))
            self.popup.push_to_talk_finished.emit(
                {
                    "status": "ok",
                    "result": {
                        "provider": "gemini_live",
                        "mode": "push_to_talk_stream",
                        "transcript": result.transcript or ("Keine Sprache erkannt" if result.status != "ok" else ""),
                        "response_text": result.response_text,
                        "chat_time_ms": result.time_ms,
                        "record_seconds": record_seconds,
                        "audio_played": False,
                    },
                    "audio_path": result.audio_path,
                }
            )
            if result.audio_path:
                from goat_desktop.livetalk import play_windows_wav

                played = play_windows_wav(Path(result.audio_path))
                self.popup.push_to_talk_finished.emit({"status": "audio_done", "audio_played": played})
        except Exception as exc:  # noqa: BLE001 - show user-visible failure in popup
            self.popup.push_to_talk_finished.emit({"status": "error", "error": str(exc)})

    def _finish_push_to_talk_recorded_worker(self, recorder, started: float) -> None:
        try:
            audio_recorded = recorder.stop()
            result = self.livetalk.run_gemini_live_recorded(
                Path(recorder.output_path),
                started=started,
                record_seconds=recorder.recorded_seconds,
                audio_recorded=audio_recorded,
                play_audio=False,
                screen_context=self._last_screen_context,
            )
            payload = result.to_dict()
            self.popup.push_to_talk_finished.emit({"status": "ok", "result": payload})
            if result.response_audio_path:
                from goat_desktop.livetalk import play_windows_wav

                played = play_windows_wav(Path(result.response_audio_path))
                self.popup.push_to_talk_finished.emit({"status": "audio_done", "audio_played": played})
        except Exception as exc:  # noqa: BLE001 - show user-visible failure in popup
            self.popup.push_to_talk_finished.emit({"status": "error", "error": str(exc)})

    def _finish_push_to_talk_payload(self, payload: dict) -> None:
        if payload.get("status") == "audio_done":
            return
        if payload.get("status") != "ok":
            self.popup.screen_context_value.setText("Sprechen gerade nicht moeglich")
            self.popup.maya_value.setText(str(payload.get("error") or "Push-to-talk fehlgeschlagen"))
        else:
            result = dict(payload.get("result") or {})
            self.last_livetalk_result = result
            self.popup.screen_context_value.setText(str(result.get("transcript") or ""))
            self.popup.maya_value.setText(str(result.get("response_text") or ""))
            self.popup.audio_value.setText(
                "Gemini Live {time:.0f}ms / Aufnahme {rec:.1f}s".format(
                    time=float(result.get("chat_time_ms") or 0.0),
                    rec=float(result.get("record_seconds") or 0.0),
                )
            )
            self.popup.audio_chip.setText("Sprache: Fertig")
        self.popup.talk_button.setEnabled(True)
        self.popup.talk_button.setText("Halten zum Sprechen")

    def exit_livetalk_mode(self) -> None:
        self.popup.set_livetalk_mode(False)
        self._set_read_aloud_available("")
        self.popup.screen_context_value.setText("Noch keine Frage")
        self.popup.maya_value.setText("Bereit. Frag mich, was ich fuer dich finden soll.")

    def send_chat_message(self) -> None:
        text = self.popup.chat_input.text().strip()
        if not text:
            return
        self.popup.chat_input.clear()
        self.popup.screen_context_value.setText(text)
        self.popup.maya_value.setText("Ich schaue nach..." if should_use_screen_context(text) else "Ich frage Maya...")
        self.popup.chat_send.setEnabled(False)
        QApplication.processEvents()
        provider = str(self.popup.vision_provider.currentData())
        reasoning = str(self.popup.vision_reasoning.currentData())
        Thread(
            target=self._chat_message_worker,
            args=(text, self.popup.target_value.text(), provider, reasoning),
            name="goat-chat-message",
            daemon=True,
        ).start()

    def _chat_message_worker(self, text: str, target: str, provider: str, reasoning: str) -> None:
        payload = self._build_chat_message_payload(text, target, provider, reasoning)
        self.popup.chat_finished.emit(payload)

    def _build_chat_message_payload(self, text: str, target: str, provider: str, reasoning: str) -> dict:
        screen_context = self._last_screen_context
        screen_marker = None
        screen_resolution = None
        is_screen_question = should_use_screen_context(text)
        if is_screen_question:
            screen_context_result = self._resolve_screen_context_for_message(text, provider, reasoning)
            if screen_context_result.get("status") == "ok":
                screen_context = str(screen_context_result.get("summary") or "")
                screen_marker = screen_context_result.get("marker") if isinstance(screen_context_result.get("marker"), dict) else None
                screen_resolution = screen_context_result.get("uia") if isinstance(screen_context_result.get("uia"), dict) else None
            elif not screen_context:
                screen_context = f"Bildschirm-Kontext nicht verfuegbar: {screen_context_result.get('error') or 'Vision fehlgeschlagen'}"
        if should_answer_screen_question_locally(text, screen_context):
            response_text = build_screen_context_fallback_response(screen_context)
            chat_payload = {
                "status": "ok",
                "provider": "goat_local_screen_context",
                "reasoning_level": "none",
                "confidence": 1.0,
                "raw_evidence": {"source": "screen_context_direct"},
            }
            chat_status = "ok"
        else:
            result = request_chat_response(
                text,
                context=build_chat_context(screen_context, target),
            )
            response_text = result.response_text
            if is_screen_question and is_unavailable_chat_response(response_text):
                response_text = build_screen_context_fallback_response(screen_context)
            chat_payload = result.to_dict()
            chat_status = result.status
        return {
            "status": chat_status,
            "message": text,
            "response_text": response_text,
            "is_screen_question": is_screen_question,
            "screen_context": screen_context,
            "marker": screen_marker,
            "screen_resolution": screen_resolution,
            "chat": chat_payload,
        }

    def handle_bridge_screen_question(self, payload: dict) -> dict:
        started = perf_counter()
        text = str(payload.get("message") or "").strip()
        if not text:
            return {"ok": False, "status": "error", "error": "message is required", "effects": _no_action_effects()}
        provider = str(payload.get("provider") or self._screen_context_provider)
        reasoning = str(payload.get("reasoning") or self._screen_context_reasoning)
        result = self._build_chat_message_payload(text, self.popup.target_value.text(), provider, reasoning)
        self.popup.chat_finished.emit(result)
        elapsed_ms = round((perf_counter() - started) * 1000, 2)
        resolver = _build_resolver_evidence(result.get("screen_resolution"))
        resolver_caches = get_resolver_cache_status()
        return {
            "ok": result.get("status") == "ok",
            "diagnostic": True,
            "scope": "local_screen_question_smoke",
            "time_ms": elapsed_ms,
            "payload": result,
            "evidence": {
                "screen_context": result.get("screen_context"),
                "marker_source": (result.get("marker") or {}).get("source") if isinstance(result.get("marker"), dict) else None,
                "chat_provider": (result.get("chat") or {}).get("provider") if isinstance(result.get("chat"), dict) else None,
                "resolver": resolver,
                "resolver_caches": resolver_caches,
                "source_path": resolver.get("source_path"),
                "cache_hit": resolver.get("cache_hit"),
                "cache_refreshed": resolver.get("cache_refreshed"),
                "elements_scanned": resolver.get("elements_scanned"),
            },
            "effects": _no_action_effects(),
        }

    def _resolve_screen_context_for_message(self, text: str, provider: str, reasoning: str) -> dict:
        uia_context = find_uia_match_for_message(text)
        if uia_context.get("ok"):
            match = uia_context.get("match") if isinstance(uia_context.get("match"), dict) else None
            if match is not None:
                return {
                    "status": "ok",
                    "summary": build_uia_screen_context(match),
                    "marker": build_uia_marker(match),
                    "source": "uia",
                    "uia": {
                        "time_ms": uia_context.get("time_ms"),
                        "elements_scanned": uia_context.get("elements_scanned"),
                        "source": uia_context.get("source"),
                        "source_path": uia_context.get("source_path"),
                        "cache_hit": uia_context.get("cache_hit"),
                        "cache_refreshed": uia_context.get("cache_refreshed"),
                        "match": match,
                    },
                }
            if not should_use_vision_fallback(text):
                return {
                    "status": "ok",
                    "summary": build_local_screen_miss_summary(text, uia_context),
                    "marker": None,
                    "source": "local_screen_miss",
                    "uia": {
                        "status": "miss",
                        "time_ms": uia_context.get("time_ms"),
                        "elements_scanned": uia_context.get("elements_scanned"),
                        "source": uia_context.get("source"),
                        "source_path": uia_context.get("source_path"),
                        "cache_hit": uia_context.get("cache_hit"),
                        "cache_refreshed": uia_context.get("cache_refreshed"),
                    },
                }
        elif not should_use_vision_fallback(text):
            return {
                "status": "ok",
                "summary": build_local_screen_miss_summary(text, uia_context),
                "marker": None,
                "source": "local_screen_unavailable",
                "uia": {
                    "status": "error",
                    "time_ms": uia_context.get("time_ms"),
                    "elements_scanned": uia_context.get("elements_scanned"),
                    "error": uia_context.get("error"),
                },
            }
        vision_context = self._capture_screen_context_for_message(text, provider, reasoning)
        if isinstance(vision_context, dict):
            vision_context.setdefault(
                "uia",
                {
                    "status": "miss",
                    "time_ms": uia_context.get("time_ms"),
                    "elements_scanned": uia_context.get("elements_scanned"),
                    "error": uia_context.get("error"),
                },
            )
        return vision_context

    def _capture_screen_context_for_message(self, text: str, provider: str, reasoning: str) -> dict:
        try:
            with tempfile.TemporaryDirectory(prefix="goat-chat-screen-") as tmp:
                image_path = Path(tmp) / "visible-desktop.png"
                capture = capture_visible_desktop(output_path=image_path)
                if not capture.get("ok"):
                    return {"status": "error", "error": capture.get("error", "screen capture failed"), "capture": capture}
                base_config = load_vision_hint_config()
                config = VisionHintConfig(
                    mode=VisionMode.BUILDER_PROXY,
                    provider=VisionProvider(provider),
                    reasoning_level=ReasoningLevel(reasoning),
                    builder_url=base_config.builder_url,
                    builder_token=base_config.builder_token,
                    timeout_seconds=base_config.timeout_seconds,
                )
                hint = get_vision_hint(image_path, build_screen_context_prompt(text), config=config)
                if hint.status != "ok":
                    return {"status": "error", "error": hint.error or "vision failed", "capture": capture, "hint": hint.to_dict()}
                return {
                    "status": "ok",
                    "summary": build_screen_context_summary(capture, hint),
                    "marker": build_screen_marker_from_hint(capture, hint),
                    "capture": capture,
                    "hint": hint.to_dict(),
                }
        except Exception as exc:  # noqa: BLE001 - surfaced in chat context
            return {"status": "error", "error": str(exc)}

    def _finish_chat_message(self, payload: dict) -> None:
        self.popup.chat_send.setEnabled(True)
        screen_context = str(payload.get("screen_context") or "").strip()
        if screen_context:
            self._last_screen_context = screen_context
            if payload.get("is_screen_question"):
                self.popup.screen_context_value.setText(build_screen_context_display_status(screen_context))
            else:
                self.popup.screen_context_value.setText(screen_context)
        else:
            self.popup.screen_context_value.setText(str(payload.get("message") or ""))
        response_text = str(payload.get("response_text") or "")
        self.popup.maya_value.setText(response_text)
        marker = payload.get("marker") if isinstance(payload.get("marker"), dict) else None
        if marker and isinstance(marker.get("region"), dict):
            region = marker["region"]
            x = int(float(region["x"]) + float(region["width"]) / 2)
            y = int(float(region["y"]) + float(region["height"]) / 2)
            self.move_ball_to_cue(x, y)
            self.popup.target_value.setText(f"Ziel gefunden: {marker.get('label') or 'markiertes Ziel'}")
        self._set_read_aloud_available(response_text)

    def request_screen_context(self) -> None:
        self.popup.screen_context_button.setEnabled(False)
        self.popup.screen_context_button.setText("Pruefe...")
        self.popup.screen_context_value.setText("Ich schaue auf den Bildschirm...")
        self.popup.maya_value.setText("Einen Moment")
        self._screen_context_provider = str(self.popup.vision_provider.currentData())
        self._screen_context_reasoning = str(self.popup.vision_reasoning.currentData())
        self.popup.hide()
        QTimer.singleShot(250, self._start_screen_context_worker)

    def _start_screen_context_worker(self) -> None:
        Thread(target=self._screen_context_worker, name="goat-screen-context", daemon=True).start()

    def _screen_context_worker(self) -> None:
        try:
            with tempfile.TemporaryDirectory(prefix="goat-screen-context-") as tmp:
                image_path = Path(tmp) / "active-window.png"
                capture = capture_visible_desktop(output_path=image_path)
                if not capture.get("ok"):
                    self.popup.screen_context_finished.emit(
                        {"status": "error", "error": capture.get("error", "screen capture failed"), "capture": capture}
                    )
                    return
                base_config = load_vision_hint_config()
                config = VisionHintConfig(
                    mode=VisionMode.BUILDER_PROXY,
                    provider=VisionProvider(self._screen_context_provider),
                    reasoning_level=ReasoningLevel(self._screen_context_reasoning),
                    builder_url=base_config.builder_url,
                    builder_token=base_config.builder_token,
                    timeout_seconds=base_config.timeout_seconds,
                )
                hint = get_vision_hint(image_path, VISION_CONTEXT_PROMPT, config=config)
                if hint.status != "ok":
                    self.popup.screen_context_finished.emit(
                        {"status": "error", "error": hint.error or "vision failed", "capture": capture, "hint": hint.to_dict()}
                    )
                    return
                summary = build_screen_context_summary(capture, hint)
                self.popup.screen_context_finished.emit(
                    {"status": "ok", "summary": summary, "capture": capture, "hint": hint.to_dict()}
                )
        except Exception as exc:  # noqa: BLE001 - user-visible failure in popup
            self.popup.screen_context_finished.emit({"status": "error", "error": str(exc)})

    def _finish_screen_context(self, payload: dict) -> None:
        self.popup.showNormal()
        self.popup.ensure_visible()
        self.popup.screen_context_button.setEnabled(True)
        self.popup.screen_context_button.setText("Bildschirm pruefen")
        if payload.get("status") != "ok":
            self.popup.screen_context_value.setText("Bildschirm konnte nicht gelesen werden")
            self.popup.maya_value.setText(str(payload.get("error") or "Bitte versuch es erneut."))
            return
        summary = str(payload.get("summary") or "")
        self._last_screen_context = summary
        self.popup.screen_context_value.setText(summary)
        self.popup.maya_value.setText("Bildschirm verstanden")

    def _set_read_aloud_available(self, text: str) -> None:
        self._read_aloud_request_id += 1
        self._read_aloud_text = text.strip()
        visible = bool(self._read_aloud_text) and self.popup.exit_livetalk.isVisible()
        self.popup.read_aloud.setVisible(visible)
        self.popup.read_aloud.setEnabled(visible)
        self.popup.read_aloud.setText("Vorlesen")

    def read_livetalk_response_aloud(self) -> None:
        text = self._read_aloud_text.strip()
        if not text:
            self._set_read_aloud_available("")
            return
        self._read_aloud_request_id += 1
        request_id = self._read_aloud_request_id
        self.popup.read_aloud.setEnabled(False)
        self.popup.read_aloud.setText("Lade Audio...")
        self.popup.audio_value.setText("Builder-TTS laedt Audio...")
        Thread(
            target=self._read_livetalk_response_aloud_worker,
            args=(request_id, text),
            name="goat-read-aloud",
            daemon=True,
        ).start()

    def _read_livetalk_response_aloud_worker(self, request_id: int, text: str) -> None:
        if request_id != self._read_aloud_request_id:
            return
        result = read_response_aloud(text, self.livetalk.audio_dir)
        self.popup.read_aloud_finished.emit(
            {
                "request_id": request_id,
                "status": result.status,
                "audio_played": result.audio_played,
                "tts_provider": result.tts_provider,
                "tts_time_ms": result.tts_time_ms,
                "error": result.error,
            }
        )

    def _finish_read_livetalk_response_aloud(self, payload: dict) -> None:
        if int(payload.get("request_id", -1)) != self._read_aloud_request_id:
            return
        self.popup.read_aloud.setEnabled(True)
        self.popup.read_aloud.setText("Vorlesen")
        if payload.get("status") == "ok" and payload.get("audio_played"):
            self.popup.audio_value.setText("Vorgelesen ({time:.0f}ms)".format(time=float(payload.get("tts_time_ms") or 0.0)))
            self.popup.audio_chip.setText("Sprache: Fertig")
            return
        error = str(payload.get("error") or "TTS fehlgeschlagen")
        self.popup.audio_value.setText(f"Vorlesen fehlgeschlagen: {error}")
        self.popup.audio_chip.setText("Sprache: Problem")

    def _refresh_audio_status(self) -> None:
        if self.livetalk.provider == "gemini_live":
            text = "Gemini Live aktiv"
            self.popup.audio_value.setText(text)
            self.popup.audio_chip.setText(_speech_chip_text(text))
            return
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
        self.popup.audio_chip.setText(_speech_chip_text(text))

    def _update_livetalk_status(self, state: str) -> None:
        if self.livetalk.provider == "gemini_live":
            labels = {
                "prepare": ("Gleich sprechen", "Nach dem Ton sprechen"),
                "listening": ("Ich hoere zu", "Jetzt sprechen"),
                "thinking": ("Ich denke nach", "Maya antwortet gleich"),
                "speaking": ("Maya antwortet", "Audio wird abgespielt"),
                "idle": ("Bereit", "Bereit. Frag mich, was ich fuer dich finden soll."),
            }
        else:
            labels = {
                "prepare": ("Gleich sprechen", "Nach dem Ton sprechen"),
                "listening": ("Ich hoere zu", "Jetzt sprechen"),
                "thinking": ("Ich denke nach", "Maya antwortet gleich"),
                "speaking": ("Maya antwortet", "Audio wird geladen"),
                "idle": ("Bereit", "Bereit. Frag mich, was ich fuer dich finden soll."),
            }
        screen_text, maya_text = labels.get(state, (state, "Bereit."))
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
            with urllib.request.urlopen(request, timeout=_LOCAL_ACTION_TIMEOUT_SECONDS) as response:
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
            self.popup.connection_chip.setText(_status_chip_text("lokal"))
            return
        self.builder_bridge = BuilderBridgeClient(url=url, token=token)
        self.builder_bridge.status_changed.connect(self._update_connection_status)
        self.builder_bridge.cue_received.connect(self.receive_builder_cue)
        self.builder_bridge.start()

    def _update_connection_status(self, text: str) -> None:
        self.popup.connection_value.setText(text)
        self.popup.connection_chip.setText(_status_chip_text(text))

    def receive_builder_cue(self, message: dict) -> None:
        if message.get("status") == "rejected" or (
            message.get("ok") is False and message.get("scope") == "local_builder_cue_proposal"
        ):
            self.pending_builder_cue = None
            self.pending_stage1_action = None
            self.pending_stage2_action = None
            self.pending_stage3_action = None
            self.pending_stage4_action = None
            _set_review_status(self.popup)
            self.popup.target_value.setText("Kein Ziel markiert")
            self.popup.screen_context_value.setText("Ziel nicht sicher erkannt")
            self.popup.maya_value.setText(_friendly_builder_cue_failure_message(message))
            self.popup.cue_approve.setText("Pruefen")
            self.popup.cue_approve.setEnabled(False)
            self.popup.cue_reject.setEnabled(True)
            self.show_popup()
            return
        action_type = str(message.get("action_type") or "").strip()
        self.pending_builder_cue = {
            "source": message.get("source", "active_window"),
            "label": message.get("label", "Builder test cue"),
            "bbox": message.get("bbox"),
            "confidence": message.get("confidence", 0.9),
        }
        if isinstance(message.get("broker_response"), dict):
            self.pending_builder_cue["broker_response"] = message["broker_response"]
        self.pending_stage1_action = None
        self.pending_stage2_action = None
        self.pending_stage3_action = None
        self.pending_stage4_action = None
        _set_review_status(self.popup)
        label = str(message.get("label") or "Ziel")
        context = dict(message.get("context") or {})
        classification = classify_action_with_reason(action_type, label, context)
        if message.get("stage4_lock") is True or classification.stage_enum == ActionStage.TECHNICAL_LOCK:
            self.pending_stage4_action = {
                "action_type": action_type,
                "label": SENSITIVE_TARGET_LABEL if message.get("stage4_lock") is True else label,
                "context": context,
            }
        elif classification.stage_enum == ActionStage.LIGHT_APPROVAL:
            self.pending_stage2_action = {
                "action_type": "type" if not _is_stage2_text_action(action_type) else action_type,
                "label": str(message.get("label") or "Eingabefeld"),
                "text": str(message.get("text") or ""),
                "safe_text_context": bool(message.get("safe_text_context") or False),
            }
        elif _is_stage1_navigation_action(action_type):
            self.pending_stage1_action = {
                "action_type": _normalized_stage1_action_type(action_type),
                "label": label,
                "scroll_amount": _stage1_scroll_amount(message),
            }
        else:
            self.pending_stage3_action = {
                "action_type": action_type,
                "label": label,
                "consequence_summary": str(message.get("consequence_summary") or ""),
            }
        if self.pending_builder_cue["bbox"] is None:
            self.pending_builder_cue.pop("bbox")
        label = str(self.pending_builder_cue.get("label") or "Builder-Cue")
        self.popup.target_value.setText(_pending_target_text(label, self.pending_stage2_action))
        self.popup.screen_context_value.setText(_pending_check_text(self.pending_stage2_action))
        self.popup.maya_value.setText(
            _pending_action_hint(
                self.pending_stage1_action,
                self.pending_stage2_action,
                self.pending_stage3_action,
                self.pending_stage4_action,
            )
        )
        self.popup.cue_approve.setText("Pruefen")
        self.popup.cue_approve.setEnabled(True)
        self.popup.cue_reject.setEnabled(True)
        self.show_popup()

    def approve_pending_cue(self) -> None:
        if self.pending_stage1_action and self.pending_stage1_action.get("broker_decision"):
            payload = dict(self.pending_stage1_action)
            self.popup.cue_approve.setEnabled(False)
            self.popup.cue_reject.setEnabled(False)
            self.popup.screen_context_value.setText("Navigation wird ausgefuehrt")
            QTimer.singleShot(_POST_APPROVAL_ACTION_DELAY_MS, lambda: self._execute_pending_stage1_action(payload))
            return
        if self.pending_stage2_action and self.pending_stage2_action.get("broker_decision"):
            payload = dict(self.pending_stage2_action)
            self.popup.cue_approve.setEnabled(False)
            self.popup.cue_reject.setEnabled(False)
            self.popup.screen_context_value.setText("Eingabe wird ausgefuehrt")
            QTimer.singleShot(_POST_APPROVAL_ACTION_DELAY_MS, lambda: self._execute_pending_stage2_action(payload))
            return
        if self.pending_stage3_action and self.pending_stage3_action.get("broker_decision"):
            self.pending_builder_cue = None
            self.pending_stage3_action = None
            self.popup.screen_context_value.setText("Review geschlossen")
            self.popup.maya_value.setText("Ich habe nichts ausgefuehrt. Bitte entscheide selbst im Programm, ob du weitermachst.")
            _set_review_status(self.popup)
            self.popup.cue_approve.setText("Pruefen")
            self.popup.cue_approve.setEnabled(False)
            self.popup.cue_reject.setEnabled(False)
            return
        if self.pending_stage4_action and self.pending_stage4_action.get("broker_decision"):
            self.pending_builder_cue = None
            self.pending_stage4_action = None
            self.popup.screen_context_value.setText("Sperre geschlossen")
            self.popup.maya_value.setText("Ich habe nichts ausgefuehrt. Bitte erledige sensible Eingaben selbst im Programm.")
            _set_review_status(self.popup)
            self.popup.cue_approve.setText("Pruefen")
            self.popup.cue_approve.setEnabled(False)
            self.popup.cue_reject.setEnabled(False)
            return
        if self.pending_builder_cue is None:
            return
        if isinstance(self.pending_builder_cue.get("broker_response"), dict):
            response = dict(self.pending_builder_cue["broker_response"])
            self.popup.cue_approve.setEnabled(False)
            self.popup.cue_reject.setEnabled(False)
            QTimer.singleShot(10, lambda: self._finish_builder_cue({"status": "ok", "response": response}))
            return
        payload = dict(self.pending_builder_cue)
        self.popup.cue_approve.setEnabled(False)
        self.popup.cue_reject.setEnabled(False)
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
            with urllib.request.urlopen(request, timeout=_LOCAL_ACTION_TIMEOUT_SECONDS) as response:
                self.last_builder_cue_response = json.loads(response.read().decode("utf-8"))
                self.popup.builder_cue_finished.emit({"status": "ok", "response": self.last_builder_cue_response})
        except Exception as exc:
            self.last_builder_cue_response = {"safety_state": "stop", "error": repr(exc)}
            self.popup.builder_cue_finished.emit({"status": "error", "error": repr(exc)})

    def _finish_builder_cue(self, payload: dict) -> None:
        if payload.get("status") in {"stage1_done", "stage2_done"}:
            response = dict(payload.get("response") or {})
            if _action_completion_verified(response):
                if payload.get("status") == "stage2_done":
                    self.popup.screen_context_value.setText("Eingabe ausgefuehrt")
                    self.popup.maya_value.setText(_friendly_stage2_success_message(response))
                else:
                    self.popup.screen_context_value.setText(_friendly_stage1_success_title(response))
                    self.popup.maya_value.setText(_friendly_stage1_success_message(response))
                self.pending_builder_cue = None
                self.pending_stage1_action = None
                self.pending_stage2_action = None
                self.pending_stage3_action = None
                self.pending_stage4_action = None
                _set_review_status(self.popup)
            else:
                self.popup.screen_context_value.setText(
                    "Eingabe nicht ausgefuehrt"
                    if payload.get("status") == "stage2_done"
                    else _friendly_stage1_failure_title(response)
                )
                self.popup.maya_value.setText(_friendly_action_failure_message(response, stage=str(payload.get("status") or "")))
            self.popup.cue_approve.setText("Pruefen")
            self.popup.cue_approve.setEnabled(False)
            self.popup.cue_reject.setEnabled(False)
            return
        if payload.get("status") != "ok":
            self.popup.screen_context_value.setText("Ziel konnte nicht geprueft werden")
            self.popup.maya_value.setText(_friendly_builder_cue_failure_message(payload))
            _set_review_status(self.popup)
            self.popup.cue_approve.setEnabled(False)
            self.popup.cue_reject.setEnabled(True)
            return
        response = dict(payload.get("response") or {})
        if response.get("safety_state") != "accept":
            self.popup.screen_context_value.setText("Ziel nicht sicher")
            self.popup.maya_value.setText(_friendly_builder_cue_failure_message(response.get("broker_decision") or response))
            _set_review_status(self.popup)
            self.popup.cue_approve.setEnabled(False)
            self.popup.cue_reject.setEnabled(True)
            return
        if (
            self.pending_stage1_action is None
            and self.pending_stage2_action is None
            and self.pending_stage3_action is None
            and self.pending_stage4_action is None
        ):
            self.popup.screen_context_value.setText("Ziel ist markiert")
            self.popup.maya_value.setText("Sag mir, was du damit tun moechtest.")
            _set_review_status(self.popup)
            self.popup.cue_approve.setEnabled(False)
            self.popup.cue_reject.setEnabled(True)
            return
        broker_decision = response.get("broker_decision") if isinstance(response.get("broker_decision"), dict) else response
        if self.pending_stage4_action is not None:
            self.pending_stage4_action["broker_decision"] = broker_decision
            preview = build_action_preview(
                str(self.pending_stage4_action.get("action_type") or ""),
                str(self.pending_stage4_action.get("label") or ""),
                broker_decision,
                text=str(self.pending_stage4_action.get("text") or ""),
                dry_run=True,
                context=dict(self.pending_stage4_action.get("context") or {}),
            )
            self.popup.screen_context_value.setText(_execution_step_title(preview))
            self.popup.maya_value.setText(_stage4_locked_message(preview))
            _set_review_status(self.popup, "Gesperrt - selbst erledigen")
            self.popup.cue_approve.setText("Verstanden")
            self.popup.cue_approve.setEnabled(True)
            self.popup.cue_reject.setEnabled(True)
            return
        if self.pending_stage3_action is not None:
            self.pending_stage3_action["broker_decision"] = broker_decision
            preview = build_action_preview(
                str(self.pending_stage3_action.get("action_type") or ""),
                str(self.pending_stage3_action.get("label") or ""),
                broker_decision,
                dry_run=True,
                context={"consequence_summary": str(self.pending_stage3_action.get("consequence_summary") or "")},
            )
            self.popup.screen_context_value.setText(_stage3_review_step_title(preview))
            self.popup.maya_value.setText(_stage3_review_message(preview))
            _set_review_status(self.popup, str(preview.get("reviewStatus") or "Nur Review - keine Ausfuehrung"))
            self.popup.cue_approve.setText("Verstanden")
            self.popup.cue_approve.setEnabled(bool(preview.get("ok")))
            self.popup.cue_reject.setEnabled(True)
            return
        if self.pending_stage2_action is not None:
            self.pending_stage2_action["broker_decision"] = broker_decision
            preview = build_action_preview(
                str(self.pending_stage2_action.get("action_type") or ""),
                str(self.pending_stage2_action.get("label") or ""),
                broker_decision,
                text=str(self.pending_stage2_action.get("text") or ""),
                dry_run=True,
            )
            self.popup.screen_context_value.setText(_execution_step_title(preview))
            self.popup.maya_value.setText(_stage2_preview_message(self.pending_stage2_action, preview))
            _set_review_status(self.popup)
            safe_text_context = bool(self.pending_stage2_action.get("safe_text_context"))
            text_guard = _stage2_text_guard(self.pending_stage2_action)
            approve_label = _stage2_approve_label(self.pending_stage2_action)
            self.popup.cue_approve.setText(approve_label)
            self.popup.cue_approve.setEnabled(bool(preview.get("ok")) and safe_text_context and text_guard is None)
            self.popup.cue_reject.setEnabled(True)
            return
        self.pending_stage1_action["broker_decision"] = broker_decision
        preview = build_action_preview(
            str(self.pending_stage1_action.get("action_type") or ""),
            str(self.pending_stage1_action.get("label") or ""),
            broker_decision,
            dry_run=True,
            context={"scroll_amount": int(self.pending_stage1_action.get("scroll_amount") or -360)},
        )
        self.popup.screen_context_value.setText(_execution_step_title(preview))
        self.popup.maya_value.setText(_stage1_preview_message(preview))
        _set_review_status(self.popup)
        self.popup.cue_approve.setText(str(preview.get("primaryButton") or "Navigieren"))
        self.popup.cue_approve.setEnabled(bool(preview.get("ok")))
        self.popup.cue_reject.setEnabled(True)

    def _execute_pending_stage1_action(self, payload: dict) -> None:
        Thread(target=self._execute_pending_stage1_action_worker, args=(payload,), name="goat-stage1-navigation", daemon=True).start()

    def _execute_pending_stage1_action_worker(self, payload: dict) -> None:
        request_payload = {
            "action_type": str(payload.get("action_type") or ""),
            "label": str(payload.get("label") or ""),
            "broker_decision": dict(payload.get("broker_decision") or {}),
            "scroll_amount": int(payload.get("scroll_amount") or -360),
            "dry_run": False,
            "user_approved": True,
        }
        request = urllib.request.Request(
            "http://127.0.0.1:8765/action/stage1",
            data=json.dumps(request_payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=_LOCAL_ACTION_TIMEOUT_SECONDS) as response:
                result = json.loads(response.read().decode("utf-8"))
            self.popup.builder_cue_finished.emit({"status": "stage1_done", "response": result})
        except Exception as exc:
            self.popup.builder_cue_finished.emit({"status": "error", "error": repr(exc)})

    def _execute_pending_stage2_action(self, payload: dict) -> None:
        Thread(target=self._execute_pending_stage2_action_worker, args=(payload,), name="goat-stage2-text", daemon=True).start()

    def _execute_pending_stage2_action_worker(self, payload: dict) -> None:
        request_payload = {
            "action_type": str(payload.get("action_type") or "type"),
            "label": str(payload.get("label") or ""),
            "broker_decision": dict(payload.get("broker_decision") or {}),
            "text": str(payload.get("text") or ""),
            "dry_run": False,
            "user_approved": True,
            "safe_text_context": bool(payload.get("safe_text_context") or False),
        }
        request = urllib.request.Request(
            "http://127.0.0.1:8765/action/stage2/text",
            data=json.dumps(request_payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=_LOCAL_ACTION_TIMEOUT_SECONDS) as response:
                result = json.loads(response.read().decode("utf-8"))
            self.popup.builder_cue_finished.emit({"status": "stage2_done", "response": result})
        except Exception as exc:
            self.popup.builder_cue_finished.emit({"status": "error", "error": repr(exc)})

    def reject_pending_cue(self) -> None:
        self.pending_builder_cue = None
        self.pending_stage1_action = None
        self.pending_stage2_action = None
        self.pending_stage3_action = None
        self.pending_stage4_action = None
        _set_review_status(self.popup)
        self.popup.target_value.setText("Kein Ziel markiert")
        self.popup.screen_context_value.setText("Abgebrochen")
        self.popup.maya_value.setText("Bereit. Sag mir, welches Ziel du meinst.")
        self.popup.cue_approve.setText("Pruefen")
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


def _livetalk_fallback_enabled() -> bool:
    return os.environ.get("GOAT_LIVETALK_FALLBACK", "").strip().lower() in {"1", "true", "yes", "on"}


def _streaming_livetalk_enabled() -> bool:
    return os.environ.get("GOAT_LIVETALK_STREAMING_PTT", "0").strip().lower() in {"1", "true", "yes", "on"}


def _video_frames_enabled() -> bool:
    return os.environ.get("GOAT_LIVETALK_VIDEO_FRAMES", "0").strip().lower() not in {"0", "false", "no", "off"}
