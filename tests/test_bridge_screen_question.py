from __future__ import annotations

from goat_desktop.bridge import create_app


def test_bridge_screen_question_uses_attached_handler() -> None:
    def handler(payload: dict) -> dict:
        return {
            "ok": True,
            "payload": {
                "message": payload["message"],
                "response_text": "Gesehen per Desktop: StepStack sichtbar.",
                "chat": {"provider": "goat_local_screen_context"},
            },
            "effects": {"desktopActionsExecuted": False},
        }

    endpoint = _endpoint_for(create_app(screen_question_handler=handler), "/chat/screen-question")
    body = endpoint({"message": "Siehst du StepStack?"})

    assert body["ok"] is True
    assert body["payload"]["chat"]["provider"] == "goat_local_screen_context"
    assert body["effects"]["desktopActionsExecuted"] is False


def test_bridge_screen_question_fails_closed_without_handler() -> None:
    endpoint = _endpoint_for(create_app(), "/chat/screen-question")
    body = endpoint({"message": "Siehst du StepStack?"})

    assert body["ok"] is False
    assert body["status"] == "unavailable"
    assert body["effects"]["desktopActionsExecuted"] is False


def _endpoint_for(app, path: str):
    for route in app.routes:
        if getattr(route, "path", None) == path:
            return route.endpoint
    raise AssertionError(f"route not found: {path}")
