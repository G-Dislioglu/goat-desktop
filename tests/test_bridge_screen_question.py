from __future__ import annotations

from goat_desktop import tray
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
        self._last_screen_context = ""
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
            "screen_resolution": {
                "source": "win32_desktop",
                "source_path": "win32_desktop",
                "cache_hit": False,
                "cache_refreshed": False,
                "time_ms": 12.5,
                "elements_scanned": 2,
            },
            "chat": {"provider": "goat_local_screen_context"},
        }

    def _resolve_screen_context_for_message(self, text: str, provider: str, reasoning: str) -> dict:
        return GoatTrayApp._resolve_screen_context_for_message(self, text, provider, reasoning)


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
    assert body["diagnostic"] is True
    assert body["scope"] == "local_screen_question_smoke"
    assert body["payload"]["chat"]["provider"] == "goat_local_screen_context"
    assert body["effects"]["desktopActionsExecuted"] is False


def test_bridge_screen_question_fails_closed_without_handler() -> None:
    endpoint = _endpoint_for(create_app(), "/chat/screen-question")
    body = endpoint({"message": "Siehst du StepStack?"})

    assert body["ok"] is False
    assert body["status"] == "unavailable"
    assert body["diagnostic"] is True
    assert body["scope"] == "local_screen_question_smoke"
    assert body["effects"]["desktopActionsExecuted"] is False


def test_tray_bridge_screen_question_returns_timing_and_evidence() -> None:
    fake = FakeTray()

    body = GoatTrayApp.handle_bridge_screen_question(fake, {"message": "Siehst du StepStack?"})

    assert body["ok"] is True
    assert body["diagnostic"] is True
    assert body["scope"] == "local_screen_question_smoke"
    assert body["time_ms"] >= 0
    assert body["evidence"]["marker_source"] == "win32_desktop"
    assert body["evidence"]["chat_provider"] == "goat_local_screen_context"
    assert body["evidence"]["source_path"] == "win32_desktop"
    assert body["evidence"]["cache_hit"] is False
    assert body["evidence"]["cache_refreshed"] is False
    assert body["evidence"]["elements_scanned"] == 2
    assert body["evidence"]["resolver"] == {
        "source": "win32_desktop",
        "source_path": "win32_desktop",
        "cache_hit": False,
        "cache_refreshed": False,
        "time_ms": 12.5,
        "elements_scanned": 2,
    }
    assert fake.popup.chat_finished.payloads[0]["response_text"] == "Gesehen per Desktop: StepStack sichtbar."


def test_tray_screen_question_local_miss_does_not_call_vision(monkeypatch) -> None:
    fake = FakeTray()
    monkeypatch.setattr(
        tray,
        "find_uia_match_for_message",
        lambda _text: {
            "ok": True,
            "match": None,
            "source_path": "uia_scan",
            "elements_scanned": 7,
            "time_ms": 3.5,
        },
    )
    fake._capture_screen_context_for_message = lambda *_args, **_kwargs: (_ for _ in ()).throw(  # type: ignore[attr-defined]
        AssertionError("vision fallback should stay off")
    )

    result = GoatTrayApp._build_chat_message_payload(
        fake,
        "Siehst du StepStack auf dem Desktop?",
        "Kein Ziel markiert",
        "gemini_flash_lite",
        "minimal",
    )

    assert result["response_text"] == (
        "Nicht sicher gesehen: Ziel ist im aktuellen Bildschirmbild nicht klar erkennbar. Grund: kein verlaesslicher Treffer."
    )
    assert result["chat"]["provider"] == "goat_local_screen_context"
    assert result["screen_resolution"]["source_path"] == "uia_scan"


def test_tray_screen_question_explicit_vision_fallback_can_call_vision(monkeypatch) -> None:
    fake = FakeTray()
    calls = {"vision": 0}
    monkeypatch.setattr(
        tray,
        "find_uia_match_for_message",
        lambda _text: {
            "ok": True,
            "match": None,
            "source_path": "uia_scan",
            "elements_scanned": 7,
            "time_ms": 3.5,
        },
    )

    def fake_vision(_text, _provider, _reasoning):
        calls["vision"] += 1
        return {
            "status": "ok",
            "summary": "Explorer (visible_desktop): StepStack sichtbar. Vertrauen 0.82, 300ms via gemini_flash_lite.",
            "marker": None,
        }

    fake._capture_screen_context_for_message = fake_vision  # type: ignore[attr-defined]

    result = GoatTrayApp._build_chat_message_payload(
        fake,
        "Pruef genau per Vision, ob StepStack sichtbar ist.",
        "Kein Ziel markiert",
        "gemini_flash_lite",
        "minimal",
    )

    assert calls["vision"] == 1
    assert result["response_text"] == "Gesehen: StepStack sichtbar."


def _endpoint_for(app, path: str):
    for route in app.routes:
        if getattr(route, "path", None) == path:
            return route.endpoint
    raise AssertionError(f"route not found: {path}")
