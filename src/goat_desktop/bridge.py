from __future__ import annotations

from pathlib import Path
from math import isfinite
from threading import Thread
from typing import Any, Callable

import uvicorn
from fastapi import FastAPI
from PyQt6.QtCore import QObject, pyqtSignal

from goat_desktop.broker import build_candidate, verify_candidate
from goat_desktop.screen import capture_active_window, get_active_window
from goat_desktop.stage1_executor import Stage1ExecutionRequest, execute_stage1_action
from goat_desktop.stage2_executor import Stage2ExecutionRequest, execute_stage2_text_input
from goat_desktop.stage3_approval import Stage3ApprovalRequest, review_stage3_action
from goat_desktop.vision_hint import load_vision_hint_config, get_vision_hint


class CueDispatcher(QObject):
    cue_requested = pyqtSignal(int, int)


def create_app(
    dispatch_cue: Callable[[int, int], None] | None = None,
    screen_question_handler: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
) -> FastAPI:
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

    @app.post("/screen-marker")
    def screen_marker(payload: dict[str, Any]) -> dict[str, Any]:
        decision = validate_flat_marker_contract(payload)
        if decision["status"] == "accept" and dispatch_cue is not None:
            region = decision["marker"]["region"]
            dispatch_cue(int(region["x"] + region["width"] / 2), int(region["y"] + region["height"] / 2))
        return decision

    @app.post("/chat/screen-question")
    def chat_screen_question(payload: dict[str, Any]) -> dict[str, Any]:
        if screen_question_handler is None:
            return {
                "ok": False,
                "status": "unavailable",
                "diagnostic": True,
                "scope": "local_screen_question_smoke",
                "error": "screen question handler is not attached",
                "effects": _no_action_effects(),
            }
        result = screen_question_handler(payload)
        result.setdefault("diagnostic", True)
        result.setdefault("scope", "local_screen_question_smoke")
        return result

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

    @app.post("/action/stage2/text")
    def stage2_text_action(payload: dict[str, Any]) -> dict[str, Any]:
        request = Stage2ExecutionRequest(
            action_type=str(payload.get("action_type") or "type"),
            label=str(payload.get("label") or ""),
            broker_decision=dict(payload.get("broker_decision") or {}),
            text=str(payload.get("text") or ""),
            user_approved=bool(payload.get("user_approved") or False),
            dry_run=bool(payload.get("dry_run") if "dry_run" in payload else True),
            safe_text_context=bool(payload.get("safe_text_context") or False),
        )
        return execute_stage2_text_input(request).to_dict()

    @app.post("/action/stage3/review")
    def stage3_review(payload: dict[str, Any]) -> dict[str, Any]:
        request = Stage3ApprovalRequest(
            action_type=str(payload.get("action_type") or "click"),
            label=str(payload.get("label") or ""),
            broker_decision=dict(payload.get("broker_decision") or {}),
            consequence_summary=str(payload.get("consequence_summary") or ""),
            user_approved=bool(payload.get("user_approved") or False),
            approval_phrase=str(payload.get("approval_phrase") or ""),
            dry_run=bool(payload.get("dry_run") if "dry_run" in payload else False),
        )
        return review_stage3_action(request).to_dict()

    return app


def validate_flat_marker_contract(payload: dict[str, Any]) -> dict[str, Any]:
    marker = payload.get("marker") if isinstance(payload.get("marker"), dict) else {}
    safety = payload.get("safety") if isinstance(payload.get("safety"), dict) else {}
    region = marker.get("region") if isinstance(marker.get("region"), dict) else {}
    effects = _no_action_effects()
    reasons: list[str] = []

    if payload.get("ok") is not True:
        reasons.append("contract ok must be true")
    if marker.get("available") is not True:
        reasons.append("marker must be available")
    if not str(marker.get("label") or "").strip():
        reasons.append("marker label is required")
    if not _safety_is_read_only(safety):
        reasons.append("safety must be read-only with no click, keyboard, or desktop action")

    try:
        normalized_region = {
            "x": float(region.get("x")),
            "y": float(region.get("y")),
            "width": float(region.get("width")),
            "height": float(region.get("height")),
        }
    except (TypeError, ValueError):
        normalized_region = None
    if normalized_region is None or not all(isfinite(value) for value in normalized_region.values()):
        reasons.append("marker region must contain finite x, y, width, and height")
    elif normalized_region["width"] <= 0 or normalized_region["height"] <= 0:
        reasons.append("marker region must have positive size")

    status = "stop" if reasons else "accept"
    return {
        "ok": status == "accept",
        "status": status,
        "mode": "read_only_flat_screen_marker_contract",
        "reason": "; ".join(reasons) if reasons else "flat contract accepted for cue marker only",
        "command": str(payload.get("command") or ""),
        "targetHint": str(payload.get("targetHint") or ""),
        "marker": {
            "available": status == "accept",
            "label": str(marker.get("label") or ""),
            "region": normalized_region if status == "accept" else None,
            "confidence": float(marker.get("confidence") or 0.0),
            "source": str(marker.get("source") or "flat_goat_contract"),
        },
        "safety": {
            "readOnly": True,
            "noClick": True,
            "noKeyboard": True,
            "noDesktopAction": True,
            "requiresGate": True,
        },
        "effects": effects,
    }


def _safety_is_read_only(safety: dict[str, Any]) -> bool:
    return (
        safety.get("readOnly") is True
        and safety.get("noClick") is True
        and safety.get("noKeyboard") is True
        and safety.get("noDesktopAction") is True
        and safety.get("requiresGate") is True
    )


def _no_action_effects() -> dict[str, Any]:
    return {
        "providerCallsMade": 0,
        "desktopActionsExecuted": False,
        "mouseActionsExecuted": False,
        "keyboardActionsExecuted": False,
        "tradingActionsExecuted": False,
        "mayExecuteRealAction": False,
    }


class LocalBridge:
    def __init__(
        self,
        dispatcher: CueDispatcher,
        host: str = "127.0.0.1",
        port: int = 8765,
        screen_question_handler: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
    ) -> None:
        self.dispatcher = dispatcher
        self.host = host
        self.port = port
        self.app = create_app(self.dispatcher.cue_requested.emit, screen_question_handler=screen_question_handler)
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
