from __future__ import annotations

from goat_desktop.action_preview import build_action_preview
from goat_desktop.bridge import create_app


ACCEPTED = {"status": "accept", "final_bbox": [10, 20, 110, 80]}


def test_stage1_preview_is_plain_navigation_copy() -> None:
    preview = build_action_preview("hover", "Senden Button", ACCEPTED, dry_run=True)

    assert preview["ok"] is True
    assert preview["title"] == "GOAT kann dich navigieren"
    assert preview["message"] == "GOAT will den Mauszeiger auf Senden Button bewegen. Dabei wird nichts geklickt und nichts getippt."
    assert preview["primaryButton"] == "Navigieren"
    assert preview["secondaryButton"] == "Abbrechen"
    assert preview["requiresUserApproval"] is False
    assert preview["mayExecute"] is False
    assert preview["effects"]["desktopActionsExecuted"] is False
    assert preview["effects"]["mouseActionsExecuted"] is False
    assert preview["effects"]["keyboardActionsExecuted"] is False


def test_stage2_preview_names_text_before_execution() -> None:
    preview = build_action_preview("type", "Suchfeld", ACCEPTED, text="StepStack", dry_run=True)

    assert preview["title"] == "Freigabe fuer Eingabe"
    assert preview["message"] == 'GOAT will Text in Suchfeld eingeben: "StepStack". Bitte pruefe die Eingabe vor dem Ausfuehren.'
    assert preview["primaryButton"] == "Eingabe ausfuehren"
    assert preview["requiresUserApproval"] is True
    assert preview["mayExecute"] is False


def test_stage3_preview_requires_clear_approval() -> None:
    preview = build_action_preview("click", "Kaufen", ACCEPTED, dry_run=True)

    assert preview["title"] == "Wichtige Aktion braucht Freigabe"
    assert preview["primaryButton"] == "Freigeben"
    assert "braucht deine klare Freigabe" in preview["message"]
    assert preview["requiresUserApproval"] is True


def test_stage4_preview_locks_sensitive_actions() -> None:
    preview = build_action_preview("type", "Passwortfeld", ACCEPTED, text="secret", dry_run=True)

    assert preview["ok"] is False
    assert preview["title"] == "Bitte selbst erledigen"
    assert preview["message"] == "Das wirkt sensibel. GOAT fuehrt das nicht aus."
    assert preview["primaryButton"] == "Verstanden"
    assert preview["mayExecute"] is False


def test_preview_stops_when_target_is_not_accepted() -> None:
    preview = build_action_preview("hover", "Senden Button", {"status": "uncertain"}, dry_run=True)

    assert preview["ok"] is False
    assert preview["title"] == "Ziel nicht sicher"
    assert preview["message"] == "Das Ziel ist nicht sicher genug erkannt. Bitte erst neu markieren."


def test_bridge_action_preview_endpoint_is_read_only() -> None:
    endpoint = _endpoint_for(create_app(), "/action/preview")

    body = endpoint({"action_type": "hover", "label": "Senden Button", "broker_decision": ACCEPTED})

    assert body["title"] == "GOAT kann dich navigieren"
    assert body["effects"]["desktopActionsExecuted"] is False
    assert body["effects"]["mouseActionsExecuted"] is False
    assert body["effects"]["keyboardActionsExecuted"] is False


def test_bridge_stage1_requires_user_approval_for_real_navigation() -> None:
    endpoint = _endpoint_for(create_app(), "/action/stage1")

    body = endpoint(
        {
            "action_type": "hover",
            "label": "Senden Button",
            "broker_decision": ACCEPTED,
            "dry_run": False,
            "user_approved": False,
        }
    )

    assert body["status"] == "preview_required"
    assert body["executed"] is False
    assert body["reason"] == "Bitte erst in GOAT freigeben."
    assert body["preview"]["title"] == "GOAT kann dich navigieren"
    assert body["effects"]["desktopActionsExecuted"] is False
    assert body["effects"]["mouseActionsExecuted"] is False
    assert body["effects"]["keyboardActionsExecuted"] is False


def test_bridge_stage1_dry_run_remains_read_only() -> None:
    endpoint = _endpoint_for(create_app(), "/action/stage1")

    body = endpoint({"action_type": "scroll", "label": "scroll page", "broker_decision": ACCEPTED})

    assert body["status"] == "blocked"
    assert body["executed"] is False
    assert "dry_run_ready" in body["reason"]
    assert body["effects"]["desktopActionsExecuted"] is False
    assert body["effects"]["mouseActionsExecuted"] is False


def _endpoint_for(app, path: str):
    for route in app.routes:
        if getattr(route, "path", None) == path:
            return route.endpoint
    raise AssertionError(f"route not found: {path}")
