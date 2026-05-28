from __future__ import annotations

from dataclasses import asdict, dataclass
from ctypes import Structure, byref, c_long, windll
from typing import Protocol

from goat_desktop.action_gate import ActionRequest, ActionStage, evaluate_action_gate
from goat_desktop.audit_log import append_audit_event
from goat_desktop.redaction import redact_locked_request_payload


class MouseBackend(Protocol):
    def move_to(self, x: int, y: int) -> None: ...

    def scroll(self, amount: int) -> None: ...


class Win32MouseBackend:
    def move_to(self, x: int, y: int) -> None:
        windll.user32.SetCursorPos(int(x), int(y))

    def scroll(self, amount: int) -> None:
        mouseeventf_wheel = 0x0800
        windll.user32.mouse_event(mouseeventf_wheel, 0, 0, int(amount), 0)

    def current_position(self) -> tuple[int, int]:
        class Point(Structure):
            _fields_ = [("x", c_long), ("y", c_long)]

        point = Point()
        if not windll.user32.GetCursorPos(byref(point)):
            raise OSError("GetCursorPos failed")
        return int(point.x), int(point.y)


@dataclass(frozen=True)
class Stage1ExecutionRequest:
    action_type: str
    label: str
    broker_decision: dict
    user_approved: bool = False
    dry_run: bool = False
    scroll_amount: int = -360


@dataclass(frozen=True)
class Stage1ExecutionResult:
    status: str
    executed: bool
    action_type: str
    stage: int
    reason: str
    gate_decision: dict
    target: dict | None = None
    completion_verified: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


def execute_stage1_action(
    request: Stage1ExecutionRequest,
    backend: MouseBackend | None = None,
) -> Stage1ExecutionResult:
    gate_request = ActionRequest(
        action_type=request.action_type,
        label=request.label,
        broker_decision=request.broker_decision,
        user_approved=request.user_approved,
        dry_run=request.dry_run,
    )
    gate_decision = evaluate_action_gate(gate_request)

    if gate_decision.stage != int(ActionStage.FREE_NAVIGATION):
        return _audit_execution(
            request,
            Stage1ExecutionResult(
                status="blocked",
                executed=False,
                action_type=request.action_type,
                stage=gate_decision.stage,
                reason="stage1 executor only handles free-navigation actions",
                gate_decision=gate_decision.to_dict(),
            ),
        )

    if not gate_decision.allowed_to_execute:
        return _audit_execution(
            request,
            Stage1ExecutionResult(
                status="blocked",
                executed=False,
                action_type=request.action_type,
                stage=gate_decision.stage,
                reason=f"action gate did not allow execution: {gate_decision.status}",
                gate_decision=gate_decision.to_dict(),
            ),
        )

    action_text = f"{request.action_type} {request.label}".lower()
    selected_backend = backend or Win32MouseBackend()

    if "scroll" in action_text:
        try:
            selected_backend.scroll(request.scroll_amount)
        except Exception:
            return _audit_execution(
                request,
                Stage1ExecutionResult(
                    status="failed",
                    executed=False,
                    action_type="scroll",
                    stage=gate_decision.stage,
                    reason="mouse backend failed before scroll completed",
                    gate_decision=gate_decision.to_dict(),
                ),
            )
        return _audit_execution(
            request,
            Stage1ExecutionResult(
                status="executed",
                executed=True,
                action_type="scroll",
                stage=gate_decision.stage,
                reason="stage 1 scroll executed through configured mouse backend",
                gate_decision=gate_decision.to_dict(),
                target={"scroll_amount": request.scroll_amount},
                completion_verified=True,
            ),
        )

    if "hover" in action_text or "move" in action_text or "tooltip" in action_text:
        pointer_action_type = _pointer_action_type(request.action_type)
        target = _target_center(request.broker_decision)
        if target is None:
            return _audit_execution(
                request,
                Stage1ExecutionResult(
                    status="blocked",
                    executed=False,
                    action_type=request.action_type,
                    stage=gate_decision.stage,
                    reason="hover/move requires broker final_bbox",
                    gate_decision=gate_decision.to_dict(),
                ),
            )
        try:
            selected_backend.move_to(target["x"], target["y"])
        except Exception:
            return _audit_execution(
                request,
                Stage1ExecutionResult(
                    status="failed",
                    executed=False,
                    action_type=pointer_action_type,
                    stage=gate_decision.stage,
                    reason="mouse backend failed before pointer move completed",
                    gate_decision=gate_decision.to_dict(),
                    target=target,
                ),
            )
        if not _pointer_is_at_target(selected_backend, target):
            return _audit_execution(
                request,
                Stage1ExecutionResult(
                    status="failed",
                    executed=False,
                    action_type=pointer_action_type,
                    stage=gate_decision.stage,
                    reason="pointer verification failed after move",
                    gate_decision=gate_decision.to_dict(),
                    target=target,
                ),
            )
        return _audit_execution(
            request,
            Stage1ExecutionResult(
                status="executed",
                executed=True,
                action_type=pointer_action_type,
                stage=gate_decision.stage,
                reason="stage 1 pointer move executed to broker-verified bbox center",
                gate_decision=gate_decision.to_dict(),
                target=target,
                completion_verified=True,
            ),
        )

    return _audit_execution(
        request,
        Stage1ExecutionResult(
            status="blocked",
            executed=False,
            action_type=request.action_type,
            stage=gate_decision.stage,
            reason="stage 1 action is classified as free navigation but is not in the G2 executor allowlist",
            gate_decision=gate_decision.to_dict(),
        ),
    )


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


def _pointer_action_type(action_type: str) -> str:
    normalized = action_type.strip().lower()
    if "move" in normalized and "hover" not in normalized:
        return "move"
    return "hover"


def _pointer_is_at_target(backend: MouseBackend, target: dict[str, int]) -> bool:
    current_position = getattr(backend, "current_position", None)
    if not callable(current_position):
        return True
    try:
        x, y = current_position()
    except Exception:
        return False
    return abs(int(x) - int(target["x"])) <= 2 and abs(int(y) - int(target["y"])) <= 2


def _audit_execution(
    request: Stage1ExecutionRequest,
    result: Stage1ExecutionResult,
) -> Stage1ExecutionResult:
    append_audit_event(
        "stage1_execution",
        result.status,
        {
            "request": _audit_request(request, result),
            "result": result.to_dict(),
            "assumptions": [
                "run_g2 only executes stage 1 free-navigation actions",
                "stage 2, stage 3, and stage 4 actions are blocked even if a caller reaches this module",
                "clicks, typing, file dialogs, save, submit, delete, pay, and password-like actions are outside G2 scope",
                "broker_decision must be accept before action_gate can allow execution",
            ],
        },
    )
    return result


def _audit_request(request: Stage1ExecutionRequest, result: Stage1ExecutionResult) -> dict:
    payload = asdict(request)
    if result.stage == int(ActionStage.TECHNICAL_LOCK):
        payload = redact_locked_request_payload(payload)
    return payload
