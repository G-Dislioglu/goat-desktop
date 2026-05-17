from __future__ import annotations

from pathlib import Path
from threading import Thread
from typing import Any, Callable

import uvicorn
from fastapi import FastAPI
from PyQt6.QtCore import QObject, pyqtSignal

from goat_desktop.broker import build_candidate, verify_candidate
from goat_desktop.screen import capture_active_window, get_active_window
from goat_desktop.stage1_executor import Stage1ExecutionRequest, execute_stage1_action
from goat_desktop.vision_hint import load_vision_hint_config, get_vision_hint


class CueDispatcher(QObject):
    cue_requested = pyqtSignal(int, int)


def create_app(dispatch_cue: Callable[[int, int], None] | None = None) -> FastAPI:
    app = FastAPI(title="GOAT Desktop Local Bridge", version="0.1.0")

    @app.get("/healthz")
    def healthz() -> dict[str, Any]:
        return {
            "ok": True,
            "service": "goat-desktop-local-bridge",
            "scope": "local-only",
            "host": "127.0.0.1",
        }

    @app.get("/active-window")
    def active_window() -> dict[str, Any]:
        return get_active_window().to_dict()

    @app.get("/screen-capture")
    def screen_capture(save: bool = False) -> dict[str, Any]:
        output_path = None
        if save:
            output_path = Path("docs/screenshots/run-c-active-window-capture.png").resolve()
        return capture_active_window(output_path=output_path)

    @app.post("/vision-hint")
    def vision_hint(payload: dict[str, Any]) -> dict[str, Any]:
        output_path = Path("docs/screenshots/run-e-vision-input.png").resolve()
        capture = capture_active_window(output_path=output_path)
        if not capture.get("ok"):
            return {
                "ok": False,
                "provider": load_vision_hint_config().provider.value,
                "error": capture.get("error", "screen capture failed"),
                "capture": capture,
            }
        prompt = str(payload.get("prompt") or "Describe the primary actionable UI element semantically.")
        try:
            hint = get_vision_hint(output_path, prompt)
            return {
                "ok": True,
                "provider": hint.provider,
                "hint": hint.to_dict(),
                "capture": capture,
                "authority": "semantic_hint_only",
            }
        except Exception as exc:  # noqa: BLE001 - reported to spike output
            return {
                "ok": False,
                "provider": load_vision_hint_config().provider.value,
                "error": repr(exc),
                "capture": capture,
                "authority": "semantic_hint_only",
            }

    @app.post("/screen-cue")
    def screen_cue(payload: dict[str, Any]) -> dict[str, Any]:
        window = get_active_window()
        candidate = build_candidate(payload, window)
        decision = verify_candidate(candidate, window)
        if decision["status"] == "accept" and dispatch_cue is not None:
            left, top, right, bottom = decision["final_bbox"]
            dispatch_cue(int((left + right) / 2), int((top + bottom) / 2))
        return {
            "safety_state": decision["status"],
            "anchors": decision["anchors"],
            "broker_decision": decision,
        }

    @app.post("/action/stage1")
    def stage1_action(payload: dict[str, Any]) -> dict[str, Any]:
        scroll_amount = payload.get("scroll_amount")
        request = Stage1ExecutionRequest(
            action_type=str(payload.get("action_type") or ""),
            label=str(payload.get("label") or ""),
            broker_decision=dict(payload.get("broker_decision") or {}),
            user_approved=bool(payload.get("user_approved") or False),
            dry_run=bool(payload.get("dry_run") if "dry_run" in payload else True),
            scroll_amount=int(scroll_amount) if scroll_amount is not None else -360,
        )
        return execute_stage1_action(request).to_dict()

    return app


class LocalBridge:
    def __init__(self, dispatcher: CueDispatcher, host: str = "127.0.0.1", port: int = 8765) -> None:
        self.dispatcher = dispatcher
        self.host = host
        self.port = port
        self.app = create_app(self.dispatcher.cue_requested.emit)
        self.server: uvicorn.Server | None = None
        self.thread: Thread | None = None

    def start(self) -> None:
        if self.thread is not None and self.thread.is_alive():
            return
        config = uvicorn.Config(self.app, host=self.host, port=self.port, log_level="warning")
        self.server = uvicorn.Server(config)
        self.thread = Thread(target=self.server.run, name="goat-local-bridge", daemon=True)
        self.thread.start()

    def stop(self) -> None:
        if self.server is not None:
            self.server.should_exit = True
