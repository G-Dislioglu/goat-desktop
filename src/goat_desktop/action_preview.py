from __future__ import annotations

from typing import Any

from goat_desktop.action_gate import ActionRequest, evaluate_action_gate


def build_action_preview(
    action_type: str,
    label: str,
    broker_decision: dict[str, Any],
    *,
    text: str = "",
    user_approved: bool = False,
    dry_run: bool = True,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    preview_context = context or {}
    gate_action_type = _gate_action_type_for_preview(action_type)
    gate = evaluate_action_gate(
        ActionRequest(
            action_type=gate_action_type,
            label=label,
            broker_decision=broker_decision,
            user_approved=user_approved,
            dry_run=dry_run,
            context=preview_context,
        )
    )
    target = _target_name(label)
    action_kind = _action_kind(action_type)
    action_text = _plain_action(action_type, target, text, preview_context)
    return {
        "ok": gate.status not in {"stop", "locked"},
        "status": gate.status,
        "stage": gate.stage,
        "title": _title_for_gate(gate.stage, gate.status),
        "message": _message_for_gate(gate.stage, gate.status, action_text),
        "actionText": action_text,
        "primaryButton": _primary_button_for_gate(gate.stage, gate.status, action_kind),
        "secondaryButton": "Abbrechen",
        "requiresUserApproval": gate.requires_user_approval,
        "mayExecute": gate.allowed_to_execute,
        "reason": _reason_for_gate(gate.status),
        "gateDecision": gate.to_dict(),
        "gateActionType": gate_action_type,
        "effects": _no_action_effects(),
    }


def _gate_action_type_for_preview(action_type: str) -> str:
    normalized = action_type.strip().lower()
    if any(token in normalized for token in ("hover", "move", "scroll")):
        return normalized
    return action_type


def _action_kind(action_type: str) -> str:
    normalized = action_type.strip().lower()
    if "scroll" in normalized:
        return "scroll"
    if "hover" in normalized or "move" in normalized or "tooltip" in normalized:
        return "move"
    if "type" in normalized or "text" in normalized or "input" in normalized:
        return "type"
    return "other"


def _plain_action(action_type: str, target: str, text: str, context: dict[str, Any]) -> str:
    normalized = f"{action_type} {target}".strip().lower()
    if "scroll" in normalized:
        direction = _scroll_direction(context.get("scroll_amount"))
        return f"auf der Seite {direction} scrollen"
    if "hover" in normalized or "move" in normalized or "tooltip" in normalized:
        return f"den Mauszeiger auf {target} bewegen"
    if "type" in normalized or "text" in normalized or "input" in normalized:
        preview_text = text.strip()
        suffix = f": \"{preview_text}\"" if preview_text else ""
        return f"Text in {target} eingeben{suffix}"
    stage3_text = _stage3_action_text(normalized, target)
    if stage3_text:
        return stage3_text
    if "click" in normalized or "open" in normalized or "select" in normalized:
        return f"{target} auswaehlen"
    return f"{target} bedienen"


def _stage3_action_text(normalized: str, target: str) -> str:
    if any(term in normalized for term in ("deploy", "release", "veroeffentlichen")):
        return f"Deploy oder Veroeffentlichung ueber {target} ausloesen"
    if any(term in normalized for term in ("delete", "loeschen", "stornieren", "kuendigen", "cancel")):
        return f"Loeschen oder Abbrechen ueber {target} ausloesen"
    if any(term in normalized for term in ("purchase", "kaufen", "pay", "bezahlen", "order", "bestellen", "book", "buchen")):
        return f"Kauf, Zahlung oder Buchung ueber {target} ausloesen"
    if any(term in normalized for term in ("save", "speichern", "apply", "anwenden")):
        return f"Speichern oder Anwenden von Aenderungen ueber {target} ausloesen"
    if any(term in normalized for term in ("send", "submit", "absenden", "share", "teilen", "invite", "einladen")):
        return f"etwas ueber {target} senden oder teilen"
    if any(term in normalized for term in ("upload", "hochladen", "attach", "anhaengen")):
        return f"Datei oder Inhalt ueber {target} hochladen"
    if any(term in normalized for term in ("sign", "unterschreiben", "transfer", "ueberweisen", "refund", "rueckerstatten")):
        return f"verbindliche Aktion ueber {target} ausloesen"
    return ""


def _title_for_gate(stage: int, status: str) -> str:
    if status == "locked":
        return "Bitte selbst erledigen"
    if status == "stop":
        return "Ziel nicht sicher"
    if stage == 1:
        return "GOAT kann dich navigieren"
    if stage == 2:
        return "Freigabe fuer Eingabe"
    return "Wichtige Aktion braucht Freigabe"


def _message_for_gate(stage: int, status: str, action_text: str) -> str:
    if status == "locked":
        return "Das wirkt sensibel. GOAT fuehrt das nicht aus."
    if status == "stop":
        return "Das Ziel ist nicht sicher genug erkannt. Bitte erst neu markieren."
    if stage == 1:
        return f"GOAT will {action_text}. Dabei wird nichts geklickt und nichts getippt."
    if stage == 2:
        return f"GOAT will {action_text}. Bitte pruefe die Eingabe vor dem Ausfuehren."
    return f"GOAT will {action_text}. Das kann Folgen haben und braucht deine klare Freigabe."


def _primary_button_for_gate(stage: int, status: str, action_kind: str = "other") -> str:
    if status in {"locked", "stop"}:
        return "Verstanden"
    if stage == 1:
        if action_kind == "scroll":
            return "Scrollen"
        return "Navigieren"
    if stage == 2:
        return "Eingabe ausfuehren"
    return "Freigabe pruefen"


def _reason_for_gate(status: str) -> str:
    reasons = {
        "stop": "Ziel wurde nicht sicher bestaetigt.",
        "locked": "Sensible oder technisch gesperrte Aktion.",
        "preview": "Erst Vorschau, dann Ausfuehrung.",
        "needs_approval": "Ausdrueckliche Freigabe erforderlich.",
        "dry_run_ready": "Testmodus: keine echte Aktion.",
        "ready": "Freigabe und Sicherheitspruefung bestanden.",
    }
    return reasons.get(status, "Sicherheitspruefung abgeschlossen.")


def _target_name(label: str) -> str:
    clean = " ".join(str(label or "Ziel").split())
    return clean or "Ziel"


def _scroll_direction(scroll_amount: Any) -> str:
    try:
        amount = int(scroll_amount)
    except (TypeError, ValueError):
        amount = -360
    return "nach unten" if amount < 0 else "nach oben"


def _no_action_effects() -> dict[str, bool]:
    return {
        "providerCallsMade": False,
        "desktopActionsExecuted": False,
        "mouseActionsExecuted": False,
        "keyboardActionsExecuted": False,
        "tradingActionsExecuted": False,
        "mayExecuteRealAction": False,
    }
