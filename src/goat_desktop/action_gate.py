from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import IntEnum
from typing import Any

from goat_desktop.audit_log import append_audit_event


class ActionStage(IntEnum):
    FREE_NAVIGATION = 1
    LIGHT_APPROVAL = 2
    HARD_APPROVAL = 3
    TECHNICAL_LOCK = 4


STAGE_4_TERMS = {
    "password",
    "passwort",
    "2fa",
    "otp",
    "tan",
    "cvv",
    "credit card",
    "kreditkarte",
    "api key",
    "secret",
    "private key",
}

STAGE_3_TERMS = {
    "submit",
    "send",
    "absenden",
    "pay",
    "bezahlen",
    "order",
    "bestellen",
    "book",
    "buchen",
    "save",
    "speichern",
    "delete",
    "loeschen",
    "löschen",
    "cancel booking",
    "stornieren",
    "upload",
    "hochladen",
}

STAGE_2_TERMS = {
    "type",
    "enter text",
    "input",
    "dropdown",
    "select",
    "checkbox",
    "radio",
    "date",
    "file dialog",
}

STAGE_1_TERMS = {
    "scroll",
    "tab",
    "open menu",
    "hover",
    "tooltip",
    "pagination",
    "mehr anzeigen",
    "filter anzeigen",
}


@dataclass(frozen=True)
class ActionRequest:
    action_type: str
    label: str
    broker_decision: dict[str, Any]
    user_approved: bool = False
    dry_run: bool = True


@dataclass(frozen=True)
class GateDecision:
    status: str
    stage: int
    requires_user_approval: bool
    allowed_to_execute: bool
    reason: str
    audit_event_type: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def classify_action(action_type: str, label: str) -> ActionStage:
    text = f"{action_type} {label}".lower()
    if any(term in text for term in STAGE_4_TERMS):
        return ActionStage.TECHNICAL_LOCK
    if any(term in text for term in STAGE_3_TERMS):
        return ActionStage.HARD_APPROVAL
    if any(term in text for term in STAGE_2_TERMS):
        return ActionStage.LIGHT_APPROVAL
    if any(term in text for term in STAGE_1_TERMS):
        return ActionStage.FREE_NAVIGATION
    return ActionStage.HARD_APPROVAL


def evaluate_action_gate(request: ActionRequest) -> GateDecision:
    stage = classify_action(request.action_type, request.label)
    broker_status = request.broker_decision.get("status") or request.broker_decision.get("safety_state")

    if broker_status != "accept":
        return _audit_decision(
            request,
            GateDecision(
                status="stop",
                stage=int(stage),
                requires_user_approval=True,
                allowed_to_execute=False,
                reason="broker did not accept target",
                audit_event_type="action_gate_stop",
            ),
        )

    if stage == ActionStage.TECHNICAL_LOCK:
        return _audit_decision(
            request,
            GateDecision(
                status="locked",
                stage=int(stage),
                requires_user_approval=False,
                allowed_to_execute=False,
                reason="technical lock: user must handle sensitive field manually",
                audit_event_type="action_gate_locked",
            ),
        )

    if stage == ActionStage.HARD_APPROVAL and not request.user_approved:
        return _audit_decision(
            request,
            GateDecision(
                status="needs_approval",
                stage=int(stage),
                requires_user_approval=True,
                allowed_to_execute=False,
                reason="stage 3 action requires explicit user approval",
                audit_event_type="action_gate_needs_approval",
            ),
        )

    if stage == ActionStage.LIGHT_APPROVAL and not request.user_approved:
        return _audit_decision(
            request,
            GateDecision(
                status="preview",
                stage=int(stage),
                requires_user_approval=True,
                allowed_to_execute=False,
                reason="stage 2 action requires preview approval",
                audit_event_type="action_gate_preview",
            ),
        )

    return _audit_decision(
        request,
        GateDecision(
            status="dry_run_ready" if request.dry_run else "ready",
            stage=int(stage),
            requires_user_approval=stage in {ActionStage.LIGHT_APPROVAL, ActionStage.HARD_APPROVAL},
            allowed_to_execute=not request.dry_run,
            reason="dry-run skeleton only; no OS action executed" if request.dry_run else "gate passed",
            audit_event_type="action_gate_ready",
        ),
    )


def _audit_decision(request: ActionRequest, decision: GateDecision) -> GateDecision:
    append_audit_event(
        decision.audit_event_type,
        decision.status,
        {
            "request": asdict(request),
            "decision": decision.to_dict(),
            "assumptions": [
                "broker_decision must be accept before any action gate can pass",
                "unknown action labels are classified as stage 3",
                "vision hints are semantic context only",
                "run_g1 is gate-only; run_g2/g3 may execute only separately allowlisted stage 1/2 actions",
            ],
        },
    )
    return decision
