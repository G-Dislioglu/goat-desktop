from __future__ import annotations

from goat_desktop import bridge
from goat_desktop import tray
from goat_desktop.bridge import create_app
from goat_desktop.screen import WindowInfo
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


def test_bridge_healthz_reports_resolver_cache_status(monkeypatch) -> None:
    monkeypatch.setattr(
        bridge,
        "get_resolver_cache_status",
        lambda: {
            "ready": True,
            "state": "ready",
            "taskbar": {"warm": True, "stale": False, "elements": 3, "age_ms": 10.0, "ttl_ms": 120000.0},
            "windows": {"warm": False, "stale": True, "elements": 0, "age_ms": None, "ttl_ms": 120000.0},
        },
    )
    endpoint = _endpoint_for(create_app(), "/healthz")

    body = endpoint()

    assert body["ok"] is True
    assert body["localScreen"]["ready"] is True
    assert body["localScreen"]["statusText"] == "Bildschirm bereit"
    assert body["resolverCaches"]["taskbar"]["warm"] is True
    assert body["resolverCaches"]["taskbar"]["elements"] == 3
    assert body["resolverCaches"]["windows"]["stale"] is True


def test_builder_cue_endpoint_emits_proposal_without_actions(monkeypatch) -> None:
    emitted = FakeSignal()
    moved: list[tuple[int, int]] = []
    monkeypatch.setattr(
        bridge,
        "get_active_window",
        lambda: WindowInfo(hwnd=1, title="Test Window", rect=[0, 0, 300, 200], foreground=True),
    )
    endpoint = _endpoint_for(
        create_app(dispatch_cue=lambda x, y: moved.append((x, y)), dispatch_builder_cue=emitted.emit),
        "/builder-cue",
    )

    body = endpoint({"source": "test_cue", "action_type": "type", "label": "Testfeld", "bbox": [20, 20, 120, 50]})

    assert body["ok"] is True
    assert body["scope"] == "local_builder_cue_proposal"
    assert body["requiresPopupApproval"] is True
    assert body["mayExecute"] is False
    assert body["authority"] == "proposal_only_user_approval_required"
    assert body["dispatch"]["popupProposalEmitted"] is True
    assert body["effects"]["desktopActionsExecuted"] is False
    assert body["effects"]["mouseActionsExecuted"] is False
    assert body["effects"]["keyboardActionsExecuted"] is False
    assert body["effects"]["mayExecuteRealAction"] is False
    assert moved == []
    assert emitted.payloads[0]["label"] == "Testfeld"
    assert emitted.payloads[0]["broker_response"]["safety_state"] == "accept"


def test_builder_cue_rejects_missing_bbox_without_dispatch(monkeypatch) -> None:
    emitted = FakeSignal()
    monkeypatch.setattr(
        bridge,
        "get_active_window",
        lambda: WindowInfo(hwnd=1, title="Test Window", rect=[0, 0, 300, 200], foreground=True),
    )
    endpoint = _endpoint_for(create_app(dispatch_builder_cue=emitted.emit), "/builder-cue")

    body = endpoint({"source": "test_cue", "action_type": "type", "label": "Testfeld"})

    assert body["ok"] is False
    assert body["status"] == "rejected"
    assert body["safety_state"] == "stop"
    assert "bbox" in body["reason"]
    assert body["dispatch"]["popupProposalEmitted"] is False
    assert body["effects"]["desktopActionsExecuted"] is False
    assert emitted.payloads == []


def test_builder_cue_rejects_missing_action_type_without_dispatch(monkeypatch) -> None:
    emitted = FakeSignal()
    monkeypatch.setattr(
        bridge,
        "get_active_window",
        lambda: WindowInfo(hwnd=1, title="Test Window", rect=[0, 0, 300, 200], foreground=True),
    )
    endpoint = _endpoint_for(create_app(dispatch_builder_cue=emitted.emit), "/builder-cue")

    body = endpoint({"source": "test_cue", "label": "Testfeld", "bbox": [20, 20, 120, 50]})

    assert body["ok"] is False
    assert body["status"] == "rejected"
    assert "action_type" in body["reason"]
    assert body["dispatch"]["popupProposalEmitted"] is False
    assert emitted.payloads == []


def test_builder_cue_rejects_vision_source_without_dispatch(monkeypatch) -> None:
    emitted = FakeSignal()
    monkeypatch.setattr(
        bridge,
        "get_active_window",
        lambda: WindowInfo(hwnd=1, title="Test Window", rect=[0, 0, 300, 200], foreground=True),
    )
    endpoint = _endpoint_for(create_app(dispatch_builder_cue=emitted.emit), "/builder-cue")

    body = endpoint({"source": "vision", "action_type": "hover", "label": "Testfeld", "bbox": [20, 20, 120, 50]})

    assert body["ok"] is False
    assert body["status"] == "rejected"
    assert "source" in body["reason"]
    assert body["dispatch"]["popupProposalEmitted"] is False
    assert emitted.payloads == []


def test_builder_cue_verifier_reject_does_not_emit_popup(monkeypatch) -> None:
    emitted = FakeSignal()
    monkeypatch.setattr(
        bridge,
        "get_active_window",
        lambda: WindowInfo(hwnd=1, title="Test Window", rect=[0, 0, 300, 200], foreground=True),
    )
    endpoint = _endpoint_for(create_app(dispatch_builder_cue=emitted.emit), "/builder-cue")

    body = endpoint({"source": "test_cue", "action_type": "hover", "label": "Testfeld", "bbox": [400, 20, 500, 50]})

    assert body["ok"] is False
    assert body["safety_state"] == "stop"
    assert body["dispatch"]["popupProposalEmitted"] is False
    assert body["effects"]["desktopActionsExecuted"] is False
    assert emitted.payloads == []


def test_local_bridge_reports_port_in_use_without_starting_thread(monkeypatch) -> None:
    monkeypatch.setattr(bridge, "_port_is_available", lambda _host, _port: False)
    local_bridge = bridge.LocalBridge(bridge.CueDispatcher())

    result = local_bridge.start()

    assert result["ok"] is False
    assert result["status"] == "port_in_use"
    assert local_bridge.status == "port_in_use"
    assert local_bridge.thread is None


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
    assert body["evidence"]["resolver_caches"]["taskbar"]["ttl_ms"] == 120000.0
    assert body["evidence"]["resolver_caches"]["windows"]["ttl_ms"] == 120000.0
    assert body["evidence"]["resolver"] == {
        "source": "win32_desktop",
        "source_path": "win32_desktop",
        "cache_hit": False,
        "cache_refreshed": False,
        "time_ms": 12.5,
        "elements_scanned": 2,
    }
    assert fake.popup.chat_finished.payloads[0]["response_text"] == "Gesehen per Desktop: StepStack sichtbar."


def test_resolver_cache_refresh_interval_is_configurable(monkeypatch) -> None:
    monkeypatch.delenv("GOAT_RESOLVER_CACHE_REFRESH_MS", raising=False)
    assert tray._resolver_cache_refresh_interval_ms() == 60000

    monkeypatch.setenv("GOAT_RESOLVER_CACHE_REFRESH_MS", "25000")
    assert tray._resolver_cache_refresh_interval_ms() == 25000

    monkeypatch.setenv("GOAT_RESOLVER_CACHE_REFRESH_MS", "500")
    assert tray._resolver_cache_refresh_interval_ms() == 10000

    monkeypatch.setenv("GOAT_RESOLVER_CACHE_REFRESH_MS", "nope")
    assert tray._resolver_cache_refresh_interval_ms() == 60000


def test_start_resolver_cache_warmup_once_starts_both_warmers(monkeypatch) -> None:
    started: list[tuple[str, object, bool]] = []

    class FakeThread:
        def __init__(self, target, name: str, daemon: bool) -> None:
            self.target = target
            self.name = name
            self.daemon = daemon

        def start(self) -> None:
            started.append((self.name, self.target, self.daemon))

    monkeypatch.setattr(tray, "Thread", FakeThread)
    monkeypatch.setattr(tray, "warm_taskbar_cache", lambda: None)
    monkeypatch.setattr(tray, "warm_window_cache", lambda: None)

    tray._start_resolver_cache_warmup_once()

    assert started == [
        ("goat-taskbar-cache-warmup", tray.warm_taskbar_cache, True),
        ("goat-window-cache-warmup", tray.warm_window_cache, True),
    ]


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
        "Nicht gefunden: Ich habe lokal geprueft, aber keinen passenden Treffer gesehen. Quelle: Desktop."
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
