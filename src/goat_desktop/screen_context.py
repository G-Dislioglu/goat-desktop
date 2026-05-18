from __future__ import annotations

from typing import Any


VISION_CONTEXT_PROMPT = (
    "Beschreibe den sichtbaren Desktop-Kontext fuer Maya in GOAT Desktop. "
    "Fokus: sichtbare App, wichtigste Bedienelemente, moegliche naechste Aktion. "
    "Keine sensiblen Inhalte abschreiben; nur UI-Kontext kurz zusammenfassen."
)


def build_screen_context_summary(capture: dict[str, Any], hint: Any) -> str:
    window = capture.get("active_window") or {}
    title = str(window.get("title") or "Aktives Fenster").strip() or "Aktives Fenster"
    label = str(getattr(hint, "label", "") or "").strip()
    position = str(getattr(hint, "rough_position", "") or "").strip()
    provider = str(getattr(hint, "provider", "") or "").strip()
    confidence = float(getattr(hint, "confidence", 0.0) or 0.0)
    time_ms = float(getattr(hint, "time_ms", 0.0) or 0.0)

    if not label:
        label = "kein klarer UI-Hinweis erkannt"
    where = f" bei {position}" if position else ""
    source = f" via {provider}" if provider else ""
    return f"{title}: {label}{where}. Vertrauen {confidence:.2f}, {time_ms:.0f}ms{source}."


def build_chat_context(screen_context: str, target: str) -> dict[str, str]:
    return {
        "screen_context": screen_context.strip() or "-",
        "target": target.strip() or "Kein Ziel markiert",
        "safety_rule": "desktop actions require explicit user approval",
    }
