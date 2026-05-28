from __future__ import annotations

from dataclasses import asdict, dataclass, field
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
    "token",
    "private key",
    "recovery code",
    "backup code",
    "seed phrase",
    "mnemonic",
    "security code",
    "sicherheitscode",
    "pin",
}

STAGE_3_TERMS = {
    "apply",
    "anwenden",
    "confirm",
    "bestaetigen",
    "submit",
    "send",
    "absenden",
    "publish",
    "veroeffentlichen",
    "deploy",
    "manual deploy",
    "release",
    "pay",
    "bezahlen",
    "purchase",
    "kaufen",
    "order",
    "bestellen",
    "book",
    "buchen",
    "save",
    "speichern",
    "delete",
    "loeschen",
    "cancel booking",
    "cancel subscription",
    "stornieren",
    "kuendigen",
    "upload",
    "hochladen",
    "share",
    "teilen",
    "invite",
    "einladen",
    "sign",
    "unterschreiben",
    "transfer",
    "ueberweisen",
    "refund",
    "rueckerstatten",
    "archive",
    "archivieren",
}

STAGE_2_TERMS = {
    "type",
    "enter text",
    "input",
    "text field",
    "search field",
    "eingabefeld",
    "suchfeld",
    "dropdown",
    "select",
    "auswaehlen",
    "checkbox",
    "radio",
    "date",
    "file dialog",
    "attach",
    "anhaengen",
    "copy",
    "paste",
    "einfuegen",
}

STAGE_1_TERMS = {
    "scroll",
    "tab",
    "open menu",
    "hover",
    "move pointer",
    "move mouse",
    "tooltip",
    "pagination",
    "next page",
    "previous page",
    "zoom",
    "pan",
    "mehr anzeigen",
    "filter anzeigen",
}


@dataclass(frozen=True)
class ActionClassification:
    stage_enum: ActionStage
    matched_term: str | None
    reason: str
    normalized_text: str

    @property
    def stage(self) -> int:
        return int(self.stage_enum)

    def to_dict(self) -> dict[str, Any]:
        return {
            "stage": self.stage,
            "matched_term": self.matched_term,
            "reason": self.reason,
            "normalized_text": self.normalized_text,
        }


@dataclass(frozen=True)
class ActionRequest:
    action_type: str
    label: str
    broker_decision: dict[str, Any]
    user_approved: bool = False
    dry_run: bool = True
    context: dict[str, Any] = field(default_factory=dict)


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
    return classify_action_with_reason(action_type, label).stage_enum


def classify_action_with_reason(
    action_type: str,
    label: str,
    context: dict[str, Any] | None = None,
) -> ActionClassification:
    action_text = _normalize_text(action_type)
    text = _normalize_text(" ".join([action_type, label, _context_text(context or {})]))
    technical_term = _first_matching_term(text, STAGE_4_TERMS)
    if technical_term is not None:
        return ActionClassification(
            stage_enum=ActionStage.TECHNICAL_LOCK,
            matched_term=technical_term,
            reason="sensitive-field or secret-like term matched",
            normalized_text=text,
        )
    nav_term = _first_matching_term(action_text, STAGE_1_TERMS)
    if nav_term is not None:
        return ActionClassification(
            stage_enum=ActionStage.FREE_NAVIGATION,
            matched_term=nav_term,
            reason="free-navigation action type matched",
            normalized_text=text,
        )
    for stage, terms, reason in [
        (ActionStage.HARD_APPROVAL, STAGE_3_TERMS, "consequential-action term matched"),
        (ActionStage.LIGHT_APPROVAL, STAGE_2_TERMS, "light-input or selection term matched"),
        (ActionStage.FREE_NAVIGATION, STAGE_1_TERMS, "free-navigation term matched"),
    ]:
        term = _first_matching_term(text, terms)
        if term is not None:
            return ActionClassification(stage_enum=stage, matched_term=term, reason=reason, normalized_text=text)
    return ActionClassification(
        stage_enum=ActionStage.HARD_APPROVAL,
        matched_term=None,
        reason="unknown action defaults to stage 3",
        normalized_text=text,
    )


def evaluate_action_gate(request: ActionRequest) -> GateDecision:
    classification = classify_action_with_reason(request.action_type, request.label, request.context)
    stage = classification.stage_enum
    broker_status = request.broker_decision.get("status") or request.broker_decision.get("safety_state")

    if broker_status != "accept":
        return _audit_decision(
            request,
            classification,
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
            classification,
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
            classification,
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
            classification,
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
        classification,
        GateDecision(
            status="dry_run_ready" if request.dry_run else "ready",
            stage=int(stage),
            requires_user_approval=stage in {ActionStage.LIGHT_APPROVAL, ActionStage.HARD_APPROVAL},
            allowed_to_execute=not request.dry_run,
            reason="dry-run skeleton only; no OS action executed" if request.dry_run else "gate passed",
            audit_event_type="action_gate_ready",
        ),
    )


def _audit_decision(
    request: ActionRequest,
    classification: ActionClassification,
    decision: GateDecision,
) -> GateDecision:
    append_audit_event(
        decision.audit_event_type,
        decision.status,
        {
            "request": _audit_request(request, classification),
            "decision": decision.to_dict(),
            "classification": _audit_classification(classification),
            "assumptions": [
                "broker_decision must be accept before any action gate can pass",
                "unknown action labels are classified as stage 3",
                "stage 4 terms override all lower-stage terms",
                "vision hints are semantic context only",
                "run_g1 is gate-only; run_g2/g3 may execute only separately allowlisted stage 1/2 actions",
            ],
        },
    )
    return decision


def _audit_request(request: ActionRequest, classification: ActionClassification) -> dict[str, Any]:
    payload = asdict(request)
    if classification.stage_enum == ActionStage.TECHNICAL_LOCK and payload.get("context"):
        payload["context"] = {key: "[redacted]" for key in payload["context"]}
        payload["context_redacted"] = True
    return payload


def _audit_classification(classification: ActionClassification) -> dict[str, Any]:
    payload = classification.to_dict()
    if classification.stage_enum == ActionStage.TECHNICAL_LOCK:
        payload["normalized_text"] = "[redacted]"
        payload["normalized_text_redacted"] = True
    return payload


def _normalize_text(text: str) -> str:
    replacements = {
        "\u00e4": "ae",
        "\u00f6": "oe",
        "\u00fc": "ue",
        "\u00df": "ss",
        "\u00c3\u00a4": "ae",
        "\u00c3\u00b6": "oe",
        "\u00c3\u00bc": "ue",
    }
    normalized = text.casefold()
    for source, target in replacements.items():
        normalized = normalized.replace(source, target)
    return " ".join(normalized.split())


def _context_text(context: dict[str, Any]) -> str:
    parts: list[str] = []
    for key in ["control_type", "automation_id", "name", "role", "aria_label", "input_type"]:
        value = context.get(key)
        if value is not None:
            parts.append(str(value))
    return " ".join(parts)


def _first_matching_term(text: str, terms: set[str]) -> str | None:
    for term in sorted(terms, key=lambda item: (-len(item), item)):
        if _normalize_text(term) in text:
            return term
    return None
