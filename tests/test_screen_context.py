from __future__ import annotations

from goat_desktop.screen_context import build_chat_context, build_screen_context_summary


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
