from __future__ import annotations

from typing import Any


VISION_CONTEXT_PROMPT = (
    "Beschreibe den gesamten sichtbaren Windows-Desktop fuer Maya in GOAT Desktop. "
    "Fokus: sichtbare Fenster, Desktop-Ordner/Icons, wichtigste Bedienelemente und moegliche naechste Aktion. "
    "Keine sensiblen Inhalte abschreiben; nur UI-Kontext kurz zusammenfassen."
)

_SCREEN_CONTEXT_TRIGGERS = (
    "siehst du",
    "siehst du den",
    "siehst du die",
    "wo ist",
    "wo finde",
    "finde",
    "zeig mir",
    "welcher button",
    "welche schaltflaeche",
    "ist der ordner",
    "ist die datei",
    "auf meinem desktop",
    "auf dem desktop",
    "auf dem bildschirm",
    "im fenster",
    "navigier",
)


def build_screen_context_summary(capture: dict[str, Any], hint: Any) -> str:
    window = capture.get("active_window") or {}
    title = str(window.get("title") or "Aktives Fenster").strip() or "Aktives Fenster"
    label = str(getattr(hint, "label", "") or "").strip()
    position = str(getattr(hint, "rough_position", "") or "").strip()
    provider = str(getattr(hint, "provider", "") or "").strip()
    confidence = float(getattr(hint, "confidence", 0.0) or 0.0)
    time_ms = float(getattr(hint, "time_ms", 0.0) or 0.0)
    scope = str((capture.get("capture") or {}).get("scope") or "screen").strip()

    if not label:
        label = "kein klarer UI-Hinweis erkannt"
    where = f" bei {position}" if position else ""
    source = f" via {provider}" if provider else ""
    return f"{title} ({scope}): {label}{where}. Vertrauen {confidence:.2f}, {time_ms:.0f}ms{source}."


def should_use_screen_context(message: str) -> bool:
    normalized = " ".join(message.strip().lower().split())
    return any(trigger in normalized for trigger in _SCREEN_CONTEXT_TRIGGERS)


def build_screen_context_prompt(message: str) -> str:
    clean_message = message.strip()
    if not clean_message:
        return VISION_CONTEXT_PROMPT
    return (
        f"{VISION_CONTEXT_PROMPT} "
        f"User-Frage: {clean_message}. "
        "Erkenne besonders, ob das gesuchte Ziel sichtbar ist und wo es grob liegt."
    )


def build_screen_context_fallback_response(screen_context: str) -> str:
    context = screen_context.strip()
    if not context or context == "-":
        return "Ich kann den Bildschirm gerade nicht sicher lesen."
    if "uncertain" in context.lower() or "kein klarer" in context.lower():
        return "Ich sehe das gesuchte Ziel nicht sicher. Bitte freier sichtbar machen."
    return context


def is_unavailable_chat_response(response_text: str) -> bool:
    normalized = response_text.strip().lower()
    return (
        "maya-ki ist im builder gerade nicht erreichbar" in normalized
        or "maya-ki ist noch nicht live angebunden" in normalized
        or "goat_builder_url and goat_builder_token are required" in normalized
    )


def build_chat_context(screen_context: str, target: str) -> dict[str, str]:
    return {
        "screen_context": screen_context.strip() or "-",
        "target": target.strip() or "Kein Ziel markiert",
        "safety_rule": "desktop actions require explicit user approval",
    }
