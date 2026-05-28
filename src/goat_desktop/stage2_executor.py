from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Protocol

from goat_desktop.action_gate import ActionRequest, ActionStage, evaluate_action_gate
from goat_desktop.audit_log import append_audit_event


MAX_STAGE2_TEXT_LENGTH = 120


class TextInputBackend(Protocol):
    def move_to(self, x: int, y: int) -> None: ...

    def click_left(self) -> None: ...

    def type_text(self, text: str) -> None: ...


class Win32TextInputBackend:
    def move_to(self, x: int, y: int) -> None:
        from ctypes import windll

        windll.user32.SetCursorPos(int(x), int(y))

    def click_left(self) -> None:
        from ctypes import windll

        mouseeventf_leftdown = 0x0002
        mouseeventf_leftup = 0x0004
        windll.user32.mouse_event(mouseeventf_leftdown, 0, 0, 0, 0)
        windll.user32.mouse_event(mouseeventf_leftup, 0, 0, 0, 0)

    def type_text(self, text: str) -> None:
        import time
        from ctypes import Structure, Union, WinDLL, byref, c_size_t, get_last_error, sizeof
        from ctypes import wintypes

        input_keyboard = 1
        keyeventf_unicode = 0x0004
        keyeventf_keyup = 0x0002
        user32 = WinDLL("user32", use_last_error=True)

        class KeyBdInput(Structure):
            _fields_ = [
                ("wVk", wintypes.WORD),
                ("wScan", wintypes.WORD),
                ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD),
                ("dwExtraInfo", c_size_t),
            ]

        class MouseInput(Structure):
            _fields_ = [
                ("dx", wintypes.LONG),
                ("dy", wintypes.LONG),
                ("mouseData", wintypes.DWORD),
                ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD),
                ("dwExtraInfo", c_size_t),
            ]

        class HardwareInput(Structure):
            _fields_ = [
                ("uMsg", wintypes.DWORD),
                ("wParamL", wintypes.WORD),
                ("wParamH", wintypes.WORD),
            ]

        class InputUnion(Union):
            _fields_ = [("mi", MouseInput), ("ki", KeyBdInput), ("hi", HardwareInput)]

        class Input(Structure):
            _fields_ = [("type", wintypes.DWORD), ("union", InputUnion)]

        for char in text:
            code = ord(char)
            down = Input(type=input_keyboard, union=InputUnion(ki=KeyBdInput(0, code, keyeventf_unicode, 0, 0)))
            up = Input(
                type=input_keyboard,
                union=InputUnion(ki=KeyBdInput(0, code, keyeventf_unicode | keyeventf_keyup, 0, 0)),
            )
            if user32.SendInput(1, byref(down), sizeof(down)) != 1:
                raise OSError(get_last_error(), "SendInput key-down failed")
            if user32.SendInput(1, byref(up), sizeof(up)) != 1:
                raise OSError(get_last_error(), "SendInput key-up failed")
            time.sleep(0.005)


@dataclass(frozen=True)
class Stage2ExecutionRequest:
    action_type: str
    label: str
    broker_decision: dict
    text: str
    user_approved: bool = False
    dry_run: bool = True
    safe_text_context: bool = False
    context: dict | None = None


@dataclass(frozen=True)
class Stage2ExecutionResult:
    status: str
    executed: bool
    stage: int
    reason: str
    preview: dict
    gate_decision: dict
    target: dict | None = None
    completion_verified: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


def execute_stage2_text_input(
    request: Stage2ExecutionRequest,
    backend: TextInputBackend | None = None,
) -> Stage2ExecutionResult:
    gate_request = ActionRequest(
        action_type=request.action_type,
        label=request.label,
        broker_decision=request.broker_decision,
        user_approved=request.user_approved,
        dry_run=request.dry_run,
        context=request.context or {},
    )
    gate_decision = evaluate_action_gate(gate_request)
    preview = _preview(request, include_text=gate_decision.stage != int(ActionStage.TECHNICAL_LOCK))

    if gate_decision.stage != int(ActionStage.LIGHT_APPROVAL):
        return _audit_execution(
            request,
            Stage2ExecutionResult(
                status="blocked",
                executed=False,
                stage=gate_decision.stage,
                reason="stage2 executor only handles light-approval input actions",
                preview=preview,
                gate_decision=gate_decision.to_dict(),
            ),
        )

    if not request.safe_text_context:
        return _audit_execution(
            request,
            Stage2ExecutionResult(
                status="preview",
                executed=False,
                stage=gate_decision.stage,
                reason="safe_text_context must be true before stage 2 text input can execute",
                preview=preview,
                gate_decision=gate_decision.to_dict(),
            ),
        )

    validation_error = _validate_text(request.text)
    if validation_error:
        return _audit_execution(
            request,
            Stage2ExecutionResult(
                status="blocked",
                executed=False,
                stage=gate_decision.stage,
                reason=validation_error,
                preview=preview,
                gate_decision=gate_decision.to_dict(),
            ),
        )

    if not gate_decision.allowed_to_execute:
        return _audit_execution(
            request,
            Stage2ExecutionResult(
                status="preview",
                executed=False,
                stage=gate_decision.stage,
                reason=f"action gate did not allow execution: {gate_decision.status}",
                preview=preview,
                gate_decision=gate_decision.to_dict(),
            ),
        )

    target = _target_center(request.broker_decision)
    if target is None:
        return _audit_execution(
            request,
            Stage2ExecutionResult(
                status="blocked",
                executed=False,
                stage=gate_decision.stage,
                reason="stage 2 input requires broker final_bbox",
                preview=preview,
                gate_decision=gate_decision.to_dict(),
            ),
        )

    selected_backend = backend or Win32TextInputBackend()
    try:
        selected_backend.move_to(target["x"], target["y"])
        selected_backend.click_left()
        selected_backend.type_text(request.text)
    except Exception:
        return _audit_execution(
            request,
            Stage2ExecutionResult(
                status="failed",
                executed=False,
                stage=gate_decision.stage,
                reason="text input backend failed before completion",
                preview=preview,
                gate_decision=gate_decision.to_dict(),
                target=target,
            ),
        )
    if not _text_input_is_verified(selected_backend, request.text):
        return _audit_execution(
            request,
            Stage2ExecutionResult(
                status="failed",
                executed=False,
                stage=gate_decision.stage,
                reason="text input verification failed after typing",
                preview=preview,
                gate_decision=gate_decision.to_dict(),
                target=target,
            ),
        )

    return _audit_execution(
        request,
        Stage2ExecutionResult(
            status="executed",
            executed=True,
            stage=gate_decision.stage,
            reason="stage 2 text input executed after preview approval",
            preview=preview,
            gate_decision=gate_decision.to_dict(),
            target=target,
            completion_verified=True,
        ),
    )


def _preview(request: Stage2ExecutionRequest, *, include_text: bool = True) -> dict:
    preview = {
        "label": request.label,
        "text": request.text if include_text else "",
        "text_length": len(request.text) if include_text else 0,
        "requires_user_approval": True,
        "safe_text_context": request.safe_text_context,
    }
    if not include_text:
        preview["text_redacted"] = True
    return preview


def _validate_text(text: str) -> str | None:
    if not text:
        return "text input is empty"
    if len(text) > MAX_STAGE2_TEXT_LENGTH:
        return f"text input exceeds {MAX_STAGE2_TEXT_LENGTH} characters"
    if "\n" in text or "\r" in text:
        return "multi-line text input is outside Run G3 scope"
    return None


def _target_center(broker_decision: dict) -> dict[str, int] | None:
    bbox = broker_decision.get("final_bbox")
    if bbox is None and isinstance(broker_decision.get("broker_decision"), dict):
        bbox = broker_decision["broker_decision"].get("final_bbox")
    if not bbox or len(bbox) != 4:
        return None
    left, top, right, bottom = [float(value) for value in bbox]
    if right <= left or bottom <= top:
        return None
    return {"x": int(round((left + right) / 2)), "y": int(round((top + bottom) / 2))}


def _text_input_is_verified(backend: TextInputBackend, text: str) -> bool:
    verifier = getattr(backend, "typed_text_matches", None)
    if not callable(verifier):
        return True
    try:
        return bool(verifier(text))
    except Exception:
        return False


def _audit_execution(
    request: Stage2ExecutionRequest,
    result: Stage2ExecutionResult,
) -> Stage2ExecutionResult:
    append_audit_event(
        "stage2_execution",
        result.status,
        {
            "request": _audit_request(request, result),
            "result": result.to_dict(),
            "assumptions": [
                "run_g3 only executes stage 2 text input after explicit preview approval",
                "stage 3 and stage 4 actions are blocked even if a caller reaches this module",
                "safe_text_context is required to avoid typing into unknown or sensitive fields",
                "broker_decision must be accept before action_gate can allow execution",
            ],
        },
    )
    return result


def _audit_request(request: Stage2ExecutionRequest, result: Stage2ExecutionResult) -> dict:
    payload = asdict(request)
    if result.stage == int(ActionStage.TECHNICAL_LOCK):
        payload["text"] = ""
        payload["text_redacted"] = True
        if payload.get("context"):
            payload["context"] = {key: "[redacted]" for key in payload["context"]}
            payload["context_redacted"] = True
    return payload
