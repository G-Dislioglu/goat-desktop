from __future__ import annotations

from goat_desktop import uia_context
from goat_desktop.uia_context import (
    _TASKBAR_CACHE,
    _TASKBAR_WARMUP,
    _WINDOW_CACHE,
    _WINDOW_WARMUP,
    _find_best_uia_match_in_wrappers,
    _get_taskbar_cache,
    _get_window_cache,
    _set_taskbar_cache,
    _set_window_cache,
    _target_terms,
    build_uia_marker,
    build_uia_screen_context,
    build_local_screen_readiness,
    find_best_uia_match,
    find_uia_match_for_message,
    get_resolver_cache_status,
)


class FakeRect:
    def __init__(self, left: float, top: float, right: float, bottom: float) -> None:
        self.left = left
        self.top = top
        self.right = right
        self.bottom = bottom


class FakeInfo:
    def __init__(self, name: str, control_type: str, rect: FakeRect) -> None:
        self.name = name
        self.control_type = control_type
        self.rectangle = rect


class FakeWrapper:
    def __init__(self, name: str, control_type: str = "ListItem", children: list["FakeWrapper"] | None = None) -> None:
        self.element_info = FakeInfo(name, control_type, FakeRect(10, 20, 110, 70))
        self._children = children or []

    def children(self) -> list["FakeWrapper"]:
        return self._children


def test_resolver_cache_status_reports_empty_caches(monkeypatch) -> None:
    monkeypatch.setattr(uia_context, "perf_counter", lambda: 100.0)
    _TASKBAR_CACHE["elements"] = []
    _TASKBAR_CACHE["time"] = 0.0
    _TASKBAR_WARMUP.update({"in_progress": False, "started": 0.0, "finished": 0.0, "ok": None, "error": None})
    _WINDOW_CACHE["elements"] = []
    _WINDOW_CACHE["time"] = 0.0
    _WINDOW_WARMUP.update({"in_progress": False, "started": 0.0, "finished": 0.0, "ok": None, "error": None})

    status = get_resolver_cache_status()

    assert status["ready"] is False
    assert status["state"] == "cold"
    assert status["taskbar"]["state"] == "cold"
    assert status["taskbar"]["warm"] is False
    assert status["taskbar"]["warming"] is False
    assert status["taskbar"]["lastWarmupOk"] is None
    assert status["taskbar"]["elements"] == 0
    assert status["taskbar"]["age_ms"] is None
    assert status["taskbar"]["ttl_ms"] == 120000.0
    assert status["windows"]["state"] == "cold"
    assert status["windows"]["warm"] is False
    assert status["windows"]["warming"] is False
    assert status["windows"]["lastWarmupOk"] is None
    assert status["windows"]["elements"] == 0
    assert status["windows"]["age_ms"] is None
    assert status["windows"]["ttl_ms"] == 120000.0


def test_resolver_cache_status_reports_warm_and_stale_caches(monkeypatch) -> None:
    monkeypatch.setattr(uia_context, "perf_counter", lambda: 100.0)
    monkeypatch.setattr(uia_context, "_TASKBAR_CACHE_TTL_SECONDS", 120.0)
    monkeypatch.setattr(uia_context, "_WINDOW_CACHE_TTL_SECONDS", 10.0)
    _TASKBAR_WARMUP.update({"in_progress": False, "started": 100.0, "finished": 101.0, "ok": True, "error": None})
    _WINDOW_WARMUP.update({"in_progress": False, "started": 100.0, "finished": 101.0, "ok": True, "error": None})
    _set_taskbar_cache([{"name": "Codex"}])
    _set_window_cache([{"name": "Old Window"}])

    monkeypatch.setattr(uia_context, "perf_counter", lambda: 111.5)
    status = get_resolver_cache_status()

    assert status["ready"] is False
    assert status["state"] == "partial"
    assert status["taskbar"]["state"] == "warm"
    assert status["taskbar"]["warm"] is True
    assert status["taskbar"]["stale"] is False
    assert status["taskbar"]["elements"] == 1
    assert status["taskbar"]["age_ms"] == 11500.0
    assert status["taskbar"]["ttl_ms"] == 120000.0
    assert status["windows"]["state"] == "stale"
    assert status["windows"]["warm"] is False
    assert status["windows"]["stale"] is True
    assert status["windows"]["elements"] == 1
    assert status["windows"]["age_ms"] == 11500.0
    assert status["windows"]["ttl_ms"] == 10000.0


def test_resolver_cache_status_reports_warming_and_failed_states(monkeypatch) -> None:
    monkeypatch.setattr(uia_context, "perf_counter", lambda: 200.0)
    _TASKBAR_CACHE["elements"] = []
    _TASKBAR_CACHE["time"] = 0.0
    _WINDOW_CACHE["elements"] = []
    _WINDOW_CACHE["time"] = 0.0
    _TASKBAR_WARMUP.update({"in_progress": True, "started": 199.0, "finished": 0.0, "ok": None, "error": None})
    _WINDOW_WARMUP.update({"in_progress": False, "started": 198.0, "finished": 199.0, "ok": False, "error": "RuntimeError"})

    status = get_resolver_cache_status()

    assert status["ready"] is False
    assert status["state"] == "degraded"
    assert status["taskbar"]["state"] == "warming"
    assert status["taskbar"]["warming"] is True
    assert status["windows"]["state"] == "failed"
    assert status["windows"]["lastWarmupOk"] is False
    assert status["windows"]["lastWarmupError"] == "RuntimeError"


def test_local_screen_readiness_uses_plain_user_copy() -> None:
    ready = build_local_screen_readiness({"ready": True, "state": "ready"})
    warming = build_local_screen_readiness({"ready": False, "state": "warming"})
    degraded = build_local_screen_readiness({"ready": False, "state": "degraded"})

    assert ready == {
        "ready": True,
        "state": "ready",
        "statusText": "Bildschirm bereit",
        "reason": "GOAT kann sichtbare Fenster und Taskleiste schnell pruefen.",
    }
    assert warming["statusText"] == "Bildschirm wird vorbereitet"
    assert "Hintergrund" in warming["reason"]
    assert degraded["statusText"] == "Bildschirm eingeschraenkt"


def test_find_best_uia_match_finds_named_target() -> None:
    match = find_best_uia_match(
        [
            {
                "name": "Downloads",
                "control_type": "ListItem",
                "rect": {"left": 20, "top": 30, "right": 120, "bottom": 80},
            },
            {
                "name": "StepStack",
                "control_type": "ListItem",
                "rect": {"left": 200, "top": 100, "right": 340, "bottom": 150},
            },
        ],
        "Siehst du den StepStack Ordner auf meinem Desktop?",
    )

    assert match is not None
    assert match["element"]["name"] == "StepStack"
    assert match["score"] >= 0.95


def test_find_uia_match_in_wrappers_stops_on_strong_match() -> None:
    root = FakeWrapper(
        "Desktop",
        "List",
        [
            FakeWrapper("Downloads"),
            FakeWrapper("StepStack"),
            FakeWrapper("Later item"),
        ],
    )

    match, scanned = _find_best_uia_match_in_wrappers(
        [root],
        ["stepstack"],
        min_score=0.58,
        early_score=0.95,
        scan_limit=20,
    )

    assert match is not None
    assert match["element"]["name"] == "StepStack"
    assert scanned == 3


def test_find_best_uia_match_normalizes_german_umlauts() -> None:
    match = find_best_uia_match(
        [
            {
                "name": "Senden Schaltfl\u00e4che",
                "control_type": "Button",
                "rect": {"left": 20, "top": 30, "right": 120, "bottom": 80},
            }
        ],
        "Wo ist die Senden Schaltflaeche?",
    )

    assert match is not None
    assert match["element"]["name"] == "Senden Schaltfl\u00e4che"


def test_target_terms_drop_taskbar_and_window_context_words() -> None:
    assert _target_terms("Siehst du Codex in der Taskleiste?") == ["codex"]
    assert _target_terms("Siehst du GOAT Desktop Fenster?") == ["goat", "desktop"]
    assert _target_terms("Siehst du GOAT Desktop auf dem Bildschirm?") == ["goat", "desktop"]


def test_find_best_uia_match_ignores_weak_match() -> None:
    match = find_best_uia_match(
        [{"name": "Downloads", "control_type": "ListItem", "rect": {"left": 0, "top": 0, "right": 1, "bottom": 1}}],
        "Wo ist StepStack?",
    )

    assert match is None


def test_find_best_uia_match_does_not_match_short_prefix_noise() -> None:
    match = find_best_uia_match(
        [
            {
                "name": "Ihr Geraet muss zur Installation wichtiger Updates neu gestartet werden.",
                "control_type": "Button",
                "rect": {"left": 0, "top": 0, "right": 1, "bottom": 1},
            }
        ],
        "Siehst du DiesesZielGibtEsNicht in der Taskleiste?",
    )

    assert match is None


def test_find_best_uia_match_does_not_match_partial_common_word_prefix() -> None:
    match = find_best_uia_match(
        [
            {
                "name": "Ihr Geraet muss zur Installation wichtiger Updates neu gestartet werden. Dieses Symbol zeigt mehr Informationen.",
                "control_type": "Button",
                "rect": {"left": 0, "top": 0, "right": 1, "bottom": 1},
            }
        ],
        "Siehst du DiesesZielGibtEsNicht in der Taskleiste?",
    )

    assert match is None


def test_build_uia_marker_uses_element_rect() -> None:
    match = {
        "score": 0.95,
        "element": {
            "name": "StepStack",
            "control_type": "ListItem",
            "rect": {"left": 200, "top": 100, "right": 340, "bottom": 150},
        },
    }

    marker = build_uia_marker(match)

    assert marker == {
        "available": True,
        "label": "StepStack",
        "region": {"x": 200.0, "y": 100.0, "width": 140.0, "height": 50.0},
        "confidence": 0.95,
        "source": "uia",
    }


def test_build_uia_marker_preserves_element_source() -> None:
    match = {
        "score": 1.0,
        "element": {
            "name": "StepStack",
            "control_type": "ListItem",
            "source": "win32_desktop",
            "rect": {"left": 200, "top": 100, "right": 340, "bottom": 150},
        },
    }

    marker = build_uia_marker(match)

    assert marker is not None
    assert marker["label"] == "StepStack"
    assert marker["source"] == "win32_desktop"


def test_build_uia_screen_context_is_clear() -> None:
    context = build_uia_screen_context(
        {
            "score": 0.95,
            "element": {
                "name": "StepStack",
                "control_type": "ListItem",
                "rect": {"left": 200, "top": 100, "right": 340, "bottom": 150},
            },
        }
    )

    assert context == "Lokales UIA: StepStack (ListItem) sichtbar. Vertrauen 0.95 via uia."


def test_build_uia_screen_context_names_desktop_source() -> None:
    context = build_uia_screen_context(
        {
            "score": 1.0,
            "element": {
                "name": "StepStack",
                "control_type": "ListItem",
                "source": "win32_desktop",
                "rect": {"left": 200, "top": 100, "right": 340, "bottom": 150},
            },
        }
    )

    assert context == "Lokaler Screen: StepStack (ListItem) sichtbar. Vertrauen 1.00 via win32_desktop."


def test_build_uia_screen_context_names_window_source() -> None:
    context = build_uia_screen_context(
        {
            "score": 1.0,
            "element": {
                "name": "GOAT Desktop",
                "control_type": "Window",
                "source": "win32_window",
                "rect": {"left": 200, "top": 100, "right": 340, "bottom": 150},
            },
        }
    )

    assert context == "Lokales Fenster: GOAT Desktop (Window) sichtbar. Vertrauen 1.00 via win32_window."


def test_window_question_stops_after_window_fastpath_miss(monkeypatch) -> None:
    monkeypatch.setattr(uia_context, "_find_window_match_win32", lambda *_args, **_kwargs: (None, 5, False))

    class FailingDesktop:
        def __init__(self, backend: str) -> None:
            if backend == "uia":
                raise AssertionError("explicit window miss should not use full UIA scan")

    monkeypatch.setattr("pywinauto.Desktop", FailingDesktop)

    result = find_uia_match_for_message("Siehst du DiesesZielGibtEsNicht Fenster?")

    assert result["ok"] is True
    assert result["match"] is None
    assert result["source"] == "win32_window"
    assert result["source_path"] == "win32_window_miss"
    assert result["elements_scanned"] == 5


def test_window_match_uses_warmed_cache(monkeypatch) -> None:
    _set_window_cache(
        [
            {
                "name": "GOAT Desktop",
                "control_type": "Window",
                "source": "win32_window",
                "rect": {"left": 10, "top": 20, "right": 210, "bottom": 170},
            }
        ]
    )
    monkeypatch.setattr(uia_context, "_collect_window_elements_win32", lambda: (_ for _ in ()).throw(AssertionError("cache missed")))

    result = find_uia_match_for_message("Siehst du GOAT Desktop Fenster?")

    assert result["source"] == "win32_window"
    assert result["source_path"] == "win32_window_cache"
    assert result["cache_hit"] is True
    assert result["elements_scanned"] == 1
    assert result["match"]["element"]["name"] == "GOAT Desktop"


def test_broad_screen_question_can_find_visible_window_after_desktop_miss(monkeypatch) -> None:
    monkeypatch.setattr(uia_context, "_find_desktop_icon_match_win32", lambda *_args, **_kwargs: (None, 4))
    _set_window_cache(
        [
            {
                "name": "GOAT Desktop",
                "control_type": "Window",
                "source": "win32_window",
                "rect": {"left": 10, "top": 20, "right": 210, "bottom": 170},
            }
        ]
    )

    result = find_uia_match_for_message("Siehst du GOAT Desktop auf dem Bildschirm?")

    assert result["source"] == "win32_window"
    assert result["source_path"] == "win32_window_cache"
    assert result["cache_hit"] is True
    assert result["elements_scanned"] == 1
    assert result["match"]["element"]["name"] == "GOAT Desktop"


def test_user_formulation_matrix_keeps_screen_window_taskbar_desktop_routes(monkeypatch) -> None:
    monkeypatch.setattr(
        uia_context,
        "_find_desktop_icon_match_win32",
        lambda terms, **_kwargs: (
            {
                "element": {
                    "name": "StepStack",
                    "control_type": "ListItem",
                    "source": "win32_desktop",
                    "rect": {"left": 10, "top": 20, "right": 110, "bottom": 70},
                },
                "score": 1.0,
                "target_terms": terms,
            },
            1,
        )
        if "stepstack" in terms
        else (None, 1),
    )
    _set_window_cache(
        [
            {
                "name": "GOAT Desktop",
                "control_type": "Window",
                "source": "win32_window",
                "rect": {"left": 20, "top": 30, "right": 220, "bottom": 180},
            }
        ]
    )
    _set_taskbar_cache(
        [
            {
                "name": "Codex - 1 aktives Fenster angeheftet",
                "control_type": "Button",
                "source": "uia_taskbar",
                "rect": {"left": 30, "top": 40, "right": 130, "bottom": 90},
            }
        ]
    )

    cases = [
        ("Siehst du GOAT Desktop auf dem Bildschirm?", "win32_window", "win32_window_cache"),
        ("Siehst du GOAT Desktop Fenster?", "win32_window", "win32_window_cache"),
        ("Siehst du Codex in der Taskleiste?", "uia_taskbar", "uia_taskbar_cache"),
        ("Siehst du StepStack auf dem Desktop?", "win32_desktop", "win32_desktop"),
    ]

    for message, source, source_path in cases:
        result = find_uia_match_for_message(message)

        assert result["source"] == source
        assert result["source_path"] == source_path
        assert result["match"] is not None


def test_window_cache_miss_stops_without_live_refresh(monkeypatch) -> None:
    _set_window_cache(
        [
            {
                "name": "Other Window",
                "control_type": "Window",
                "source": "win32_window",
                "rect": {"left": 10, "top": 20, "right": 210, "bottom": 170},
            }
        ]
    )
    monkeypatch.setattr(uia_context, "_collect_window_elements_win32", lambda: (_ for _ in ()).throw(AssertionError("cache miss should not refresh")))

    result = find_uia_match_for_message("Siehst du GOAT Desktop Fenster?")

    assert result["source_path"] == "win32_window_miss"
    assert result["cache_hit"] is True
    assert result["match"] is None
    assert _get_window_cache()[0]["name"] == "Other Window"


def test_window_cache_can_expire(monkeypatch) -> None:
    _set_window_cache(
        [
            {
                "name": "Codex",
                "control_type": "Window",
                "source": "win32_window",
                "rect": {"left": 10, "top": 20, "right": 210, "bottom": 170},
            }
        ]
    )
    monkeypatch.setattr(uia_context, "_WINDOW_CACHE_TTL_SECONDS", -1.0)

    assert _get_window_cache() == []


def test_window_cache_hit_refreshes_ttl(monkeypatch) -> None:
    times = iter([100.0, 110.0, 110.0, 200.0, 200.0])
    monkeypatch.setattr(uia_context, "perf_counter", lambda: next(times))
    monkeypatch.setattr(uia_context, "_WINDOW_CACHE_TTL_SECONDS", 120.0)
    _set_window_cache(
        [
            {
                "name": "Codex",
                "control_type": "Window",
                "source": "win32_window",
                "rect": {"left": 10, "top": 20, "right": 210, "bottom": 170},
            }
        ]
    )

    assert _get_window_cache()
    assert _WINDOW_CACHE["time"] == 110.0
    assert _get_window_cache()


def test_build_uia_screen_context_names_taskbar_source() -> None:
    context = build_uia_screen_context(
        {
            "score": 1.0,
            "element": {
                "name": "Codex \u2013 1 aktives Fenster angeheftet",
                "control_type": "Button",
                "source": "uia_taskbar",
                "rect": {"left": 200, "top": 100, "right": 340, "bottom": 150},
            },
        }
    )

    assert context == "Lokale Taskleiste: Codex - 1 aktives Fenster angeheftet (Button) sichtbar. Vertrauen 1.00 via uia_taskbar."


def test_desktop_question_stops_after_desktop_fastpath_miss(monkeypatch) -> None:
    monkeypatch.setattr(uia_context, "_find_desktop_icon_match_win32", lambda *_args, **_kwargs: (None, 3))

    class FailingDesktop:
        def __init__(self, backend: str) -> None:
            if backend == "uia":
                raise AssertionError("explicit desktop miss should not use full UIA scan")

    monkeypatch.setattr("pywinauto.Desktop", FailingDesktop)

    result = find_uia_match_for_message("Siehst du DiesesZielGibtEsNicht auf dem Desktop?")

    assert result["ok"] is True
    assert result["match"] is None
    assert result["source"] == "win32_desktop"
    assert result["source_path"] == "win32_desktop_miss"
    assert result["elements_scanned"] == 3


def test_taskbar_match_uses_warmed_cache(monkeypatch) -> None:
    _set_taskbar_cache(
        [
            {
                "name": "Codex - 1 aktives Fenster angeheftet",
                "control_type": "Button",
                "source": "uia_taskbar",
                "rect": {"left": 10, "top": 20, "right": 110, "bottom": 70},
            }
        ]
    )
    monkeypatch.setattr(uia_context, "_collect_taskbar_elements_uia", lambda: (_ for _ in ()).throw(AssertionError("cache missed")))

    result = find_uia_match_for_message("Siehst du Codex in der Taskleiste?")

    assert result["source"] == "uia_taskbar"
    assert result["source_path"] == "uia_taskbar_cache"
    assert result["cache_hit"] is True
    assert result["cache_refreshed"] is False
    assert result["elements_scanned"] == 1
    assert result["match"]["element"]["name"] == "Codex - 1 aktives Fenster angeheftet"


def test_taskbar_cache_miss_stops_without_live_refresh(monkeypatch) -> None:
    _set_taskbar_cache(
        [
            {
                "name": "Other App",
                "control_type": "Button",
                "source": "uia_taskbar",
                "rect": {"left": 10, "top": 20, "right": 110, "bottom": 70},
            }
        ]
    )
    monkeypatch.setattr(uia_context, "_collect_taskbar_elements_uia", lambda: (_ for _ in ()).throw(AssertionError("cache miss should not refresh")))

    result = find_uia_match_for_message("Siehst du Codex in der Taskleiste?")

    assert result["source_path"] == "uia_taskbar_miss"
    assert result["cache_hit"] is True
    assert result["cache_refreshed"] is False
    assert result["match"] is None
    assert _get_taskbar_cache()[0]["name"] == "Other App"


def test_taskbar_question_stops_after_taskbar_miss(monkeypatch) -> None:
    _set_taskbar_cache([])
    monkeypatch.setattr(uia_context, "_collect_taskbar_elements_uia", lambda: ([], 4))

    class FailingDesktop:
        def __init__(self, backend: str) -> None:
            if backend == "uia":
                raise AssertionError("explicit taskbar miss should not use full UIA scan")

    monkeypatch.setattr("pywinauto.Desktop", FailingDesktop)

    result = find_uia_match_for_message("Siehst du DiesesZielGibtEsNicht in der Taskleiste?")

    assert result["ok"] is True
    assert result["match"] is None
    assert result["source"] == "uia_taskbar"
    assert result["source_path"] == "uia_taskbar_miss"
    assert result["elements_scanned"] == 4


def test_taskbar_cache_can_expire(monkeypatch) -> None:
    _set_taskbar_cache(
        [
            {
                "name": "Codex",
                "control_type": "Button",
                "source": "uia_taskbar",
                "rect": {"left": 10, "top": 20, "right": 110, "bottom": 70},
            }
        ]
    )
    monkeypatch.setattr(uia_context, "_TASKBAR_CACHE_TTL_SECONDS", -1.0)

    assert _get_taskbar_cache() == []


def test_taskbar_cache_hit_refreshes_ttl(monkeypatch) -> None:
    times = iter([100.0, 110.0, 110.0, 200.0, 200.0])
    monkeypatch.setattr(uia_context, "perf_counter", lambda: next(times))
    monkeypatch.setattr(uia_context, "_TASKBAR_CACHE_TTL_SECONDS", 120.0)
    _set_taskbar_cache(
        [
            {
                "name": "Codex",
                "control_type": "Button",
                "source": "uia_taskbar",
                "rect": {"left": 10, "top": 20, "right": 110, "bottom": 70},
            }
        ]
    )

    assert _get_taskbar_cache()
    assert _TASKBAR_CACHE["time"] == 110.0
    assert _get_taskbar_cache()


def test_build_uia_screen_context_capitalizes_lowercase_icon_name() -> None:
    context = build_uia_screen_context(
        {
            "score": 1.0,
            "element": {
                "name": "stepstack",
                "control_type": "ListItem",
                "source": "win32_desktop",
                "rect": {"left": 200, "top": 100, "right": 340, "bottom": 150},
            },
        }
    )

    assert context == "Lokaler Screen: StepStack (ListItem) sichtbar. Vertrauen 1.00 via win32_desktop."
