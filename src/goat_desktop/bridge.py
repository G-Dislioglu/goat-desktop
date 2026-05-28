from __future__ import annotations

import socket
from pathlib import Path
from math import isfinite
from threading import Thread
from typing import Any, Callable

import uvicorn
from fastapi import FastAPI
from PyQt6.QtCore import QObject, pyqtSignal

from goat_desktop.broker import LOCAL_GEOMETRY_SOURCES, build_candidate, verify_candidate
from goat_desktop.action_gate import ActionStage, classify_action_with_reason
from goat_desktop.action_preview import build_action_preview
from goat_desktop.redaction import (
    REDACTED_VALUE,
    SENSITIVE_TARGET_LABEL,
    redact_locked_request_payload,
    redact_nested_context_values,
)
from goat_desktop.screen import capture_active_window, get_active_window
from goat_desktop.stage1_executor import Stage1ExecutionRequest, execute_stage1_action
from goat_desktop.stage2_executor import Stage2ExecutionRequest, execute_stage2_text_input
from goat_desktop.stage3_approval import Stage3ApprovalRequest, review_stage3_action
from goat_desktop.uia_context import build_local_screen_readiness, get_resolver_cache_status
from goat_desktop.vision_hint import load_vision_hint_config, get_vision_hint


class CueDispatcher(QObject):
    cue_requested = pyqtSignal(int, int)
    builder_cue_requested = pyqtSignal(dict)


def create_app(
    dispatch_cue: Callable[[int, int], None] | None = None,
    dispatch_builder_cue: Callable[[dict[str, Any]], None] | None = None,
    screen_question_handler: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
) -> FastAPI:
    app = FastAPI(title="GOAT Desktop Local Bridge", version="0.1.0")

    @app.get("/healthz")
    def healthz() -> dict[str, Any]:
        resolver_caches = get_resolver_cache_status()
        return {
            "ok": True,
            "service": "goat-desktop-local-bridge",
            "scope": "local-only",
            "host": "127.0.0.1",
            "localScreen": build_local_screen_readiness(resolver_caches),
            "resolverCaches": resolver_caches,
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

    @app.post("/builder-cue")
    def builder_cue(payload: dict[str, Any]) -> dict[str, Any]:
        contract_errors = _builder_cue_contract_errors(payload)
        if contract_errors:
            return _builder_cue_rejected("; ".join(contract_errors))
        window = get_active_window()
        candidate = build_candidate(payload, window)
        decision = verify_candidate(candidate, window)
        classification = _builder_cue_classification(payload)
        response = {
            "safety_state": decision["status"],
            "anchors": decision["anchors"],
            "broker_decision": decision,
        }
        if classification.stage_enum == ActionStage.TECHNICAL_LOCK and isinstance(payload.get("context"), dict):
            response = redact_nested_context_values(response)
        if classification.stage_enum == ActionStage.TECHNICAL_LOCK:
            response = _redact_builder_cue_label(response)
        proposal_emitted = False
        if decision["status"] == "accept" and dispatch_builder_cue is not None:
            cue_payload = _builder_cue_popup_payload(payload, classification)
            cue_payload["broker_response"] = response
            dispatch_builder_cue(cue_payload)
            proposal_emitted = True
        return {
            "ok": decision["status"] == "accept",
            "diagnostic": True,
            "scope": "local_builder_cue_proposal",
            "safety_state": decision["status"],
            "broker_response": response,
            "requiresPopupApproval": True,
            "mayExecute": False,
            "authority": "proposal_only_user_approval_required",
            "dispatch": {"popupProposalEmitted": proposal_emitted},
            "effects": _no_action_effects(),
        }

    @app.post("/screen-marker")
    def screen_marker(payload: dict[str, Any]) -> dict[str, Any]:
        decision = validate_flat_marker_contract(payload)
        if decision["status"] == "accept" and dispatch_cue is not None:
            region = decision["marker"]["region"]
            dispatch_cue(int(region["x"] + region["width"] / 2), int(region["y"] + region["height"] / 2))
        return decision

    @app.post("/action/preview")
    def action_preview(payload: dict[str, Any]) -> dict[str, Any]:
        return build_action_preview(
            str(payload.get("action_type") or ""),
            str(payload.get("label") or ""),
            dict(payload.get("broker_decision") or {}),
            text=str(payload.get("text") or ""),
            user_approved=bool(payload.get("user_approved") or False),
            dry_run=bool(payload.get("dry_run") if "dry_run" in payload else True),
            context=_action_preview_context(payload),
        )

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
        requested_dry_run = bool(payload.get("dry_run") if "dry_run" in payload else True)
        user_approved = bool(payload.get("user_approved") or False)
        if not requested_dry_run and not user_approved:
            preview = build_action_preview(
                str(payload.get("action_type") or ""),
                str(payload.get("label") or ""),
                dict(payload.get("broker_decision") or {}),
                dry_run=True,
                context=_action_preview_context(payload),
            )
            return {
                "status": "preview_required",
                "executed": False,
                "stage": preview.get("stage"),
                "reason": "Bitte erst in GOAT freigeben.",
                "preview": preview,
                "effects": _no_action_effects(),
            }
        request = Stage1ExecutionRequest(
            action_type=str(payload.get("action_type") or ""),
            label=str(payload.get("label") or ""),
            broker_decision=dict(payload.get("broker_decision") or {}),
            user_approved=user_approved,
            dry_run=requested_dry_run,
            scroll_amount=int(scroll_amount) if scroll_amount is not None else -360,
        )
        result = execute_stage1_action(request).to_dict()
        result["effects"] = _stage1_effects(result)
        return result

    @app.post("/action/stage2/text")
    def stage2_text_action(payload: dict[str, Any]) -> dict[str, Any]:
        requested_dry_run = bool(payload.get("dry_run") if "dry_run" in payload else True)
        user_approved = bool(payload.get("user_approved") or False)
        safe_text_context = _bool_from_payload(payload.get("safe_text_context"))
        if not requested_dry_run and not user_approved:
            preview = build_action_preview(
                str(payload.get("action_type") or "type"),
                str(payload.get("label") or ""),
                dict(payload.get("broker_decision") or {}),
                text=str(payload.get("text") or ""),
                dry_run=True,
                context=_action_preview_context(payload),
            )
            return {
                "status": "preview_required",
                "executed": False,
                "stage": preview.get("stage"),
                "reason": "Bitte pruefe die Eingabe zuerst in GOAT.",
                "preview": preview,
                "effects": _no_action_effects(),
            }
        request = Stage2ExecutionRequest(
            action_type=str(payload.get("action_type") or "type"),
            label=str(payload.get("label") or ""),
            broker_decision=dict(payload.get("broker_decision") or {}),
            text=str(payload.get("text") or ""),
            user_approved=user_approved,
            dry_run=requested_dry_run,
            safe_text_context=safe_text_context,
            context=_action_preview_context(payload),
        )
        result = execute_stage2_text_input(request).to_dict()
        result["effects"] = _stage2_effects(result)
        return result

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


def _builder_cue_contract_errors(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    source = str(payload.get("source") or "").strip()
    action_type = str(payload.get("action_type") or "").strip()
    label = str(payload.get("label") or "").strip()
    bbox = payload.get("bbox")

    if not source:
        errors.append("source is required")
    elif source not in LOCAL_GEOMETRY_SOURCES:
        errors.append("source must be an accepted local geometry source")
    if source == "vision":
        errors.append("vision source cannot create a builder cue proposal")
    if not action_type:
        errors.append("action_type is required")
    if not label:
        errors.append("label is required")
    if not isinstance(bbox, list) or len(bbox) != 4:
        errors.append("bbox with four numeric values is required")
    else:
        try:
            normalized = [float(value) for value in bbox]
        except (TypeError, ValueError):
            errors.append("bbox values must be numeric")
        else:
            if not all(isfinite(value) for value in normalized):
                errors.append("bbox values must be finite")
            elif normalized[2] <= normalized[0] or normalized[3] <= normalized[1]:
                errors.append("bbox must have positive size")
    if "scroll" in action_type.lower() and "scroll_amount" in payload:
        try:
            scroll_amount = float(payload.get("scroll_amount"))
        except (TypeError, ValueError):
            errors.append("scroll_amount must be numeric")
        else:
            if not isfinite(scroll_amount):
                errors.append("scroll_amount must be finite")
            elif int(scroll_amount) == 0:
                errors.append("scroll_amount must not be zero")
    return errors


def _builder_cue_rejected(reason: str) -> dict[str, Any]:
    return {
        "ok": False,
        "diagnostic": True,
        "scope": "local_builder_cue_proposal",
        "status": "rejected",
        "safety_state": "stop",
        "reason": reason,
        "requiresPopupApproval": True,
        "mayExecute": False,
        "authority": "proposal_only_user_approval_required",
        "dispatch": {"popupProposalEmitted": False},
        "effects": _no_action_effects(),
    }


def _builder_cue_classification(payload: dict[str, Any]):
    return classify_action_with_reason(
        str(payload.get("action_type") or ""),
        str(payload.get("label") or ""),
        dict(payload.get("context") or {}),
    )


def _builder_cue_popup_payload(payload: dict[str, Any], classification=None) -> dict[str, Any]:
    cue_payload = dict(payload)
    classification = classification or _builder_cue_classification(payload)
    if classification.stage_enum == ActionStage.TECHNICAL_LOCK:
        cue_payload = redact_locked_request_payload(cue_payload, redact_text=True)
        cue_payload["stage4_lock"] = True
        cue_payload["label"] = SENSITIVE_TARGET_LABEL
    return cue_payload


def _redact_builder_cue_label(response: dict[str, Any]) -> dict[str, Any]:
    redacted = dict(response)
    broker_decision = dict(redacted.get("broker_decision") or {})
    candidate = dict(broker_decision.get("candidate") or {})
    if candidate:
        candidate["label"] = REDACTED_VALUE
        raw_evidence = dict(candidate.get("raw_evidence") or {})
        request = dict(raw_evidence.get("request") or {})
        if request:
            request = redact_locked_request_payload(request, redact_text=True)
            raw_evidence["request"] = request
        candidate["raw_evidence"] = raw_evidence
        broker_decision["candidate"] = candidate
    redacted["broker_decision"] = broker_decision
    return redacted


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


def _stage1_effects(result: dict[str, Any]) -> dict[str, Any]:
    effects = _no_action_effects()
    executed = bool(result.get("executed"))
    action_type = str(result.get("action_type") or "")
    effects["desktopActionsExecuted"] = executed
    effects["mouseActionsExecuted"] = executed and action_type in {"hover", "move", "scroll"}
    effects["mayExecuteRealAction"] = executed
    return effects


def _stage2_effects(result: dict[str, Any]) -> dict[str, Any]:
    effects = _no_action_effects()
    executed = bool(result.get("executed"))
    effects["desktopActionsExecuted"] = executed
    effects["mouseActionsExecuted"] = executed
    effects["keyboardActionsExecuted"] = executed
    effects["mayExecuteRealAction"] = executed
    return effects


def _bool_from_payload(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes"}
    return False


def _action_preview_context(payload: dict[str, Any]) -> dict[str, Any]:
    context = dict(payload.get("context") or {})
    if "scroll_amount" in payload:
        try:
            context["scroll_amount"] = int(payload.get("scroll_amount"))
        except (TypeError, ValueError):
            context["scroll_amount"] = -360
    return context


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
        self.app = create_app(
            self.dispatcher.cue_requested.emit,
            self.dispatcher.builder_cue_requested.emit,
            screen_question_handler=screen_question_handler,
        )
        self.server: uvicorn.Server | None = None
        self.thread: Thread | None = None
        self.status = "stopped"
        self.last_error: str | None = None

    def start(self) -> dict[str, Any]:
        if self.thread is not None and self.thread.is_alive():
            return {"ok": True, "status": "running", "host": self.host, "port": self.port}
        if not _port_is_available(self.host, self.port):
            self.status = "port_in_use"
            self.last_error = f"{self.host}:{self.port} is already in use"
            return {"ok": False, "status": self.status, "host": self.host, "port": self.port, "error": self.last_error}
        config = uvicorn.Config(self.app, host=self.host, port=self.port, log_level="warning")
        self.server = uvicorn.Server(config)
        self.thread = Thread(target=self.server.run, name="goat-local-bridge", daemon=True)
        self.thread.start()
        self.status = "starting"
        self.last_error = None
        return {"ok": True, "status": self.status, "host": self.host, "port": self.port}

    def stop(self) -> None:
        if self.server is not None:
            self.server.should_exit = True


def _port_is_available(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        try:
            probe.bind((host, int(port)))
        except OSError:
            return False
    return True
