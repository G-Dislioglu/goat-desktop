from __future__ import annotations

from goat_desktop.bridge import create_app
from goat_desktop.tray import GoatTrayApp


class FakeSignal:
    def __init__(self) -> None:
        self.payloads: list[dict] = []

    def emit(self, payload: dict) -> None:
        self.payloads.append(payload)


class FakeTargetValue:
    def text(self) -> str:
        return "Kein Ziel markiert"


class FakePopup:
    def __init__(self) -> None:
        self.target_value = FakeTargetValue()
        self.chat_finished = FakeSignal()


class FakeTray:
    def __init__(self) -> None:
        self._screen_context_provider = "gemini_flash_lite"
        self._screen_context_reasoning = "minimal"
        self.popup = FakePopup()

    def _build_chat_message_payload(self, text: str, target: str, provider: str, reasoning: str) -> dict:
        return {
            "status": "ok",
            "message": text,
            "response_text": "Gesehen per Desktop: StepStack sichtbar.",
            "screen_context": "Lokaler Screen: StepStack sichtbar. Vertrauen 1.00 via win32_desktop.",
            "marker": {"source": "win32_desktop"},
            "chat": {"provider": "goat_local_screen_context"},
        }


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


def test_tray_bridge_screen_question_returns_timing_and_evidence() -> None:
    fake = FakeTray()

    body = GoatTrayApp.handle_bridge_screen_question(fake, {"message": "Siehst du StepStack?"})

    assert body["ok"] is True
    assert body["time_ms"] >= 0
    assert body["evidence"]["marker_source"] == "win32_desktop"
    assert body["evidence"]["chat_provider"] == "goat_local_screen_context"
    assert fake.popup.chat_finished.payloads[0]["response_text"] == "Gesehen per Desktop: StepStack sichtbar."


def _endpoint_for(app, path: str):
    for route in app.routes:
        if getattr(route, "path", None) == path:
            return route.endpoint
    raise AssertionError(f"route not found: {path}")
