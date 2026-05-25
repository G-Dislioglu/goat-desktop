from __future__ import annotations

from goat_desktop.screen_context import (
    VISION_CONTEXT_PROMPT,
    build_chat_context,
    build_screen_marker_from_hint,
    build_screen_context_display_status,
    build_screen_context_fallback_response,
    build_screen_context_prompt,
    build_screen_context_summary,
    is_unavailable_chat_response,
    should_use_screen_context,
)


class Hint:
    provider = "gemini_flash_lite"
    label = "Senden-Button und Texteingabe sichtbar"
    rough_position = "unten rechts"
    confidence = 0.82
    time_ms = 456.0


def test_build_screen_context_summary_is_short_and_actionable() -> None:
    summary = build_screen_context_summary(
        {"active_window": {"title": "GOAT Desktop"}, "capture": {"scope": "visible_desktop"}},
        Hint(),
    )

    assert "GOAT Desktop" in summary
    assert "visible_desktop" in summary
    assert "Senden-Button" in summary
    assert "unten rechts" in summary
    assert "0.82" in summary
    assert "gemini_flash_lite" in summary


def test_build_chat_context_preserves_last_screen_context() -> None:
    context = build_chat_context("Chrome: Login sichtbar.", "Kein Ziel markiert")

    assert context["screen_context"] == "Chrome: Login sichtbar."
    assert context["target"] == "Kein Ziel markiert"
    assert "approval" in context["safety_rule"]


def test_should_use_screen_context_for_visible_target_questions() -> None:
    assert should_use_screen_context("Siehst du den StepStack Ordner auf meinem Desktop?") is True
    assert should_use_screen_context("Wo ist der Senden Button?") is True
    assert should_use_screen_context("Kannst du mich zum richtigen Fenster navigieren?") is True


def test_should_not_use_screen_context_for_plain_chat() -> None:
    assert should_use_screen_context("Fasse mir den Plan kurz zusammen.") is False
    assert should_use_screen_context("Was haben wir zuletzt committed?") is False


def test_build_screen_context_prompt_includes_user_question() -> None:
    prompt = build_screen_context_prompt("Wo ist StepStack?")

    assert VISION_CONTEXT_PROMPT in prompt
    assert "Wo ist StepStack?" in prompt
    assert "gesuchte Ziel sichtbar" in prompt
    assert "semantic_label" in prompt
    assert "approximate_position" in prompt
    assert "confidence" in prompt


def test_screen_context_fallback_response_handles_uncertain_context() -> None:
    response = build_screen_context_fallback_response("Codex (visible_desktop): uncertain bei unknown.")

    assert response == "Nicht sicher gesehen: Ziel ist nicht klar erkennbar."


def test_screen_context_fallback_response_uses_context_when_clear() -> None:
    response = build_screen_context_fallback_response("Desktop: StepStack Ordner links oben sichtbar.")

    assert response == "Gesehen: Desktop: StepStack Ordner links oben sichtbar."


def test_screen_context_fallback_response_cleans_summary_when_clear() -> None:
    response = build_screen_context_fallback_response(
        "Explorer (visible_desktop): StepStack Ordner links oben sichtbar. Vertrauen 0.82, 300ms via gemini_flash_lite."
    )

    assert response == "Gesehen: StepStack Ordner links oben sichtbar."


def test_screen_context_display_status_is_compact() -> None:
    assert build_screen_context_display_status("Codex: uncertain bei unknown. Vertrauen 0.00.") == "Bildschirm: Ziel nicht sicher gesehen"
    assert build_screen_context_display_status("Explorer: StepStack sichtbar. Vertrauen 0.82.") == "Bildschirm: Ziel gesehen"


def test_unavailable_chat_response_detection() -> None:
    assert is_unavailable_chat_response("Maya-KI ist im Builder gerade nicht erreichbar.") is True
    assert is_unavailable_chat_response("GOAT_BUILDER_URL and GOAT_BUILDER_TOKEN are required") is True
    assert is_unavailable_chat_response("Der Ordner ist links oben sichtbar.") is False


def test_build_screen_marker_from_hint_maps_rough_position() -> None:
    marker = build_screen_marker_from_hint(
        {"capture": {"left": 0, "top": 0, "width": 1000, "height": 800}},
        Hint(),
    )

    assert marker is not None
    assert marker["label"] == "Senden-Button und Texteingabe sichtbar"
    assert marker["region"] == {"x": 740.0, "y": 600.0, "width": 120.0, "height": 80.0}
    assert marker["source"] == "vision_rough_position"


def test_build_screen_marker_from_hint_requires_confidence() -> None:
    class LowConfidenceHint(Hint):
        confidence = 0.0

    marker = build_screen_marker_from_hint(
        {"capture": {"left": 0, "top": 0, "width": 1000, "height": 800}},
        LowConfidenceHint(),
    )

    assert marker is None
