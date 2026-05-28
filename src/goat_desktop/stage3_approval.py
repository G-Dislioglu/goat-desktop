from __future__ import annotations

from dataclasses import asdict, dataclass

from goat_desktop.action_gate import ActionRequest, ActionStage, evaluate_action_gate
from goat_desktop.audit_log import append_audit_event
from goat_desktop.redaction import SENSITIVE_FIELD_LABEL, redact_locked_stage3_payload


APPROVAL_PHRASE = "I approve this stage 3 action"


@dataclass(frozen=True)
class Stage3ApprovalRequest:
    action_type: str
    label: str
    broker_decision: dict
    consequence_summary: str
    user_approved: bool = False
    approval_phrase: str = ""
    dry_run: bool = False


@dataclass(frozen=True)
class Stage3ApprovalResult:
    status: str
    executed: bool
    stage: int
    reason: str
    approval_required: bool
    preview: dict
    gate_decision: dict
    user_message: str = ""

    def to_dict(self) -> dict:
        result = asdict(self)
        result["completion_verified"] = False
        result["mayExecuteRealAction"] = False
        result["effects"] = _no_action_effects()
        return result


def _no_action_effects() -> dict[str, bool]:
    return {
        "providerCallsMade": False,
        "desktopActionsExecuted": False,
        "mouseActionsExecuted": False,
        "keyboardActionsExecuted": False,
        "tradingActionsExecuted": False,
        "mayExecuteRealAction": False,
    }


def review_stage3_action(request: Stage3ApprovalRequest) -> Stage3ApprovalResult:
    gate_request = ActionRequest(
        action_type=request.action_type,
        label=request.label,
        broker_decision=request.broker_decision,
        user_approved=request.user_approved,
        dry_run=request.dry_run,
    )
    gate_decision = evaluate_action_gate(gate_request)
    preview = _preview(request, locked=gate_decision.stage == int(ActionStage.TECHNICAL_LOCK))

    if gate_decision.stage == int(ActionStage.TECHNICAL_LOCK):
        return _audit_review(
            request,
            Stage3ApprovalResult(
                status="locked",
                executed=False,
                stage=gate_decision.stage,
                reason="stage 4 technical lock: user must handle sensitive field manually",
                approval_required=False,
                preview=preview,
                gate_decision=gate_decision.to_dict(),
            ),
        )

    if gate_decision.stage != int(ActionStage.HARD_APPROVAL):
        return _audit_review(
            request,
            Stage3ApprovalResult(
                status="blocked",
                executed=False,
                stage=gate_decision.stage,
                reason="stage3 approval only handles hard-approval actions",
                approval_required=True,
                preview=preview,
                gate_decision=gate_decision.to_dict(),
            ),
        )

    if gate_decision.status == "stop":
        return _audit_review(
            request,
            Stage3ApprovalResult(
                status="stop",
                executed=False,
                stage=gate_decision.stage,
                reason="broker did not accept target",
                approval_required=True,
                preview=preview,
                gate_decision=gate_decision.to_dict(),
            ),
        )

    if not request.user_approved:
        return _audit_review(
            request,
            Stage3ApprovalResult(
                status="needs_approval",
                executed=False,
                stage=gate_decision.stage,
                reason="stage 3 action requires explicit user approval",
                approval_required=True,
                preview=preview,
                gate_decision=gate_decision.to_dict(),
            ),
        )

    if request.approval_phrase.strip() != APPROVAL_PHRASE:
        return _audit_review(
            request,
            Stage3ApprovalResult(
                status="approval_phrase_mismatch",
                executed=False,
                stage=gate_decision.stage,
                reason="approval phrase did not match",
                approval_required=True,
                preview=preview,
                gate_decision=gate_decision.to_dict(),
            ),
        )

    if request.dry_run:
        return _audit_review(
            request,
            Stage3ApprovalResult(
                status="approved_dry_run",
                executed=False,
                stage=gate_decision.stage,
                reason="stage 3 approval accepted in dry-run mode; no action executed",
                approval_required=False,
                preview=preview,
                gate_decision=gate_decision.to_dict(),
            ),
        )

    return _audit_review(
        request,
        Stage3ApprovalResult(
            status="approved_not_executed",
            executed=False,
            stage=gate_decision.stage,
            reason="stage 3 approval accepted; real execution is intentionally outside Run G4 scope",
            approval_required=False,
            preview=preview,
            gate_decision=gate_decision.to_dict(),
        ),
    )


def _preview(request: Stage3ApprovalRequest, *, locked: bool = False) -> dict:
    preview = {
        "label": request.label,
        "action_type": request.action_type,
        "consequence_summary": request.consequence_summary,
        "approval_phrase_required": APPROVAL_PHRASE,
        "broker_decision": request.broker_decision,
    }
    if locked:
        preview["label"] = SENSITIVE_FIELD_LABEL
        preview["label_redacted"] = True
        preview["consequence_summary"] = ""
        preview["consequence_summary_redacted"] = True
    return preview


def _audit_review(request: Stage3ApprovalRequest, result: Stage3ApprovalResult) -> Stage3ApprovalResult:
    result = _with_user_message(result)
    append_audit_event(
        "stage3_approval",
        result.status,
        {
            "request": _audit_request(request, result),
            "result": result.to_dict(),
            "assumptions": [
                "run_g4 validates hard approval only and executes no stage 3 OS action",
                "stage 3 approval requires broker accept, explicit user_approved true, and exact approval phrase",
                "stage 4 technical lock remains non-overridable",
                "approved_not_executed is the expected terminal status for Run G4 real approval",
            ],
        },
    )
    return result


def _with_user_message(result: Stage3ApprovalResult) -> Stage3ApprovalResult:
    if result.user_message:
        return result
    return Stage3ApprovalResult(
        status=result.status,
        executed=result.executed,
        stage=result.stage,
        reason=result.reason,
        approval_required=result.approval_required,
        preview=result.preview,
        gate_decision=result.gate_decision,
        user_message=_stage3_user_message(result),
    )


def _stage3_user_message(result: Stage3ApprovalResult) -> str:
    if result.status == "approved_not_executed":
        return "Review verstanden. Keine Aktion ausgefuehrt."
    if result.status == "approved_dry_run":
        return "Review geprueft. Keine Aktion ausgefuehrt."
    if result.status == "locked":
        return "Gesperrt. Bitte selbst erledigen."
    if result.status in {"needs_approval", "approval_phrase_mismatch"}:
        return "Review nicht freigegeben."
    return "Review nicht ausgefuehrt."


def _audit_request(request: Stage3ApprovalRequest, result: Stage3ApprovalResult) -> dict:
    payload = asdict(request)
    if result.stage == int(ActionStage.TECHNICAL_LOCK):
        payload = redact_locked_stage3_payload(payload)
    return payload
