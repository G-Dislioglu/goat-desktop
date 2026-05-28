from __future__ import annotations

import goat_desktop.stage2_executor as stage2_executor
from goat_desktop.action_preview import build_action_preview
from goat_desktop.bridge import create_app
from goat_desktop.stage3_approval import APPROVAL_PHRASE


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


def test_stage1_scroll_preview_names_direction_and_button() -> None:
    down = build_action_preview("scroll", "Seite", ACCEPTED, dry_run=True, context={"scroll_amount": -360})
    up = build_action_preview("scroll", "Seite", ACCEPTED, dry_run=True, context={"scroll_amount": 360})

    assert down["message"] == "GOAT will auf der Seite nach unten scrollen. Dabei wird nichts geklickt und nichts getippt."
    assert down["primaryButton"] == "Scrollen"
    assert up["message"] == "GOAT will auf der Seite nach oben scrollen. Dabei wird nichts geklickt und nichts getippt."
    assert up["primaryButton"] == "Scrollen"


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
    assert preview["primaryButton"] == "Freigabe pruefen"
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


def test_bridge_action_preview_uses_scroll_amount_for_plain_copy() -> None:
    endpoint = _endpoint_for(create_app(), "/action/preview")

    body = endpoint({"action_type": "scroll", "label": "Seite", "broker_decision": ACCEPTED, "scroll_amount": 360})

    assert body["primaryButton"] == "Scrollen"
    assert body["message"] == "GOAT will auf der Seite nach oben scrollen. Dabei wird nichts geklickt und nichts getippt."


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


def test_bridge_stage2_requires_user_approval_for_real_text_input() -> None:
    endpoint = _endpoint_for(create_app(), "/action/stage2/text")

    body = endpoint(
        {
            "action_type": "type",
            "label": "Suchfeld",
            "text": "StepStack",
            "broker_decision": ACCEPTED,
            "safe_text_context": True,
            "dry_run": False,
            "user_approved": False,
        }
    )

    assert body["status"] == "preview_required"
    assert body["executed"] is False
    assert body["reason"] == "Bitte pruefe die Eingabe zuerst in GOAT."
    assert body["preview"]["title"] == "Freigabe fuer Eingabe"
    assert body["preview"]["primaryButton"] == "Eingabe ausfuehren"
    assert body["effects"]["desktopActionsExecuted"] is False
    assert body["effects"]["mouseActionsExecuted"] is False
    assert body["effects"]["keyboardActionsExecuted"] is False


def test_bridge_stage2_dry_run_remains_read_only() -> None:
    endpoint = _endpoint_for(create_app(), "/action/stage2/text")

    body = endpoint(
        {
            "action_type": "type",
            "label": "Suchfeld",
            "text": "StepStack",
            "broker_decision": ACCEPTED,
            "safe_text_context": True,
        }
    )

    assert body["status"] == "preview"
    assert body["executed"] is False
    assert "preview" in body["reason"]
    assert body["effects"]["desktopActionsExecuted"] is False
    assert body["effects"]["mouseActionsExecuted"] is False
    assert body["effects"]["keyboardActionsExecuted"] is False


def test_bridge_stage2_real_text_input_reports_mouse_and_keyboard_effect(monkeypatch) -> None:
    calls: list[tuple[str, object]] = []

    class FakeTextInputBackend:
        def move_to(self, x: int, y: int) -> None:
            calls.append(("move_to", (x, y)))

        def click_left(self) -> None:
            calls.append(("click_left", None))

        def type_text(self, text: str) -> None:
            calls.append(("type_text", text))

    monkeypatch.setattr(stage2_executor, "Win32TextInputBackend", FakeTextInputBackend)
    endpoint = _endpoint_for(create_app(), "/action/stage2/text")

    body = endpoint(
        {
            "action_type": "type",
            "label": "Suchfeld",
            "text": "StepStack",
            "broker_decision": ACCEPTED,
            "safe_text_context": True,
            "dry_run": False,
            "user_approved": True,
        }
    )

    assert body["status"] == "executed"
    assert body["executed"] is True
    assert body["effects"]["desktopActionsExecuted"] is True
    assert body["effects"]["mouseActionsExecuted"] is True
    assert body["effects"]["keyboardActionsExecuted"] is True
    assert calls == [("move_to", (60, 50)), ("click_left", None), ("type_text", "StepStack")]


def test_bridge_stage3_review_never_reports_real_execution() -> None:
    endpoint = _endpoint_for(create_app(), "/action/stage3/review")

    body = endpoint(
        {
            "action_type": "click",
            "label": "Kaufen",
            "broker_decision": ACCEPTED,
            "consequence_summary": "Das wuerde einen Kauf ausloesen.",
            "user_approved": True,
            "approval_phrase": APPROVAL_PHRASE,
            "dry_run": False,
        }
    )

    assert body["status"] == "approved_not_executed"
    assert body["executed"] is False
    assert body["completion_verified"] is False
    assert body["mayExecuteRealAction"] is False
    assert body["effects"]["desktopActionsExecuted"] is False
    assert body["effects"]["mouseActionsExecuted"] is False
    assert body["effects"]["keyboardActionsExecuted"] is False
    assert body["effects"]["tradingActionsExecuted"] is False


def _endpoint_for(app, path: str):
    for route in app.routes:
        if getattr(route, "path", None) == path:
            return route.endpoint
    raise AssertionError(f"route not found: {path}")
