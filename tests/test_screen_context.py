from __future__ import annotations

from goat_desktop.screen_context import (
    VISION_CONTEXT_PROMPT,
    build_chat_context,
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


def test_screen_context_fallback_response_handles_uncertain_context() -> None:
    response = build_screen_context_fallback_response("Codex (visible_desktop): uncertain bei unknown.")

    assert response == "Ich sehe das gesuchte Ziel nicht sicher. Bitte freier sichtbar machen."


def test_screen_context_fallback_response_uses_context_when_clear() -> None:
    response = build_screen_context_fallback_response("Desktop: StepStack Ordner links oben sichtbar.")

    assert "StepStack" in response


def test_unavailable_chat_response_detection() -> None:
    assert is_unavailable_chat_response("Maya-KI ist im Builder gerade nicht erreichbar.") is True
    assert is_unavailable_chat_response("GOAT_BUILDER_URL and GOAT_BUILDER_TOKEN are required") is True
    assert is_unavailable_chat_response("Der Ordner ist links oben sichtbar.") is False
