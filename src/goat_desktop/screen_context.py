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


def build_screen_marker_from_hint(capture: dict[str, Any], hint: Any, min_confidence: float = 0.35) -> dict[str, Any] | None:
    label = str(getattr(hint, "label", "") or "").strip()
    position = str(getattr(hint, "rough_position", "") or "").strip()
    confidence = float(getattr(hint, "confidence", 0.0) or 0.0)
    if not label or not position or confidence < min_confidence:
        return None
    if is_uncertain_screen_context(label):
        return None
    capture_info = capture.get("capture") if isinstance(capture.get("capture"), dict) else {}
    width = float(capture_info.get("width") or 0.0)
    height = float(capture_info.get("height") or 0.0)
    left = float(capture_info.get("left") or 0.0)
    top = float(capture_info.get("top") or 0.0)
    if width <= 0 or height <= 0:
        return None
    center_x, center_y = _rough_position_to_center(position, left, top, width, height)
    region_width = max(80.0, width * 0.12)
    region_height = max(60.0, height * 0.10)
    return {
        "available": True,
        "label": label,
        "region": {
            "x": round(center_x - region_width / 2, 2),
            "y": round(center_y - region_height / 2, 2),
            "width": round(region_width, 2),
            "height": round(region_height, 2),
        },
        "confidence": confidence,
        "source": "vision_rough_position",
    }


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
        "Erkenne besonders, ob das gesuchte Ziel sichtbar ist und wo es grob liegt. "
        "Antworte fuer GOAT maschinenlesbar mit: semantic_label, approximate_position, confidence. "
        "semantic_label soll das sichtbare Ziel konkret benennen oder `uncertain` sein. "
        "approximate_position soll eine grobe Lage sein: oben links, oben, oben rechts, links, mitte, rechts, unten links, unten, unten rechts oder unknown. "
        "confidence: 0.0 wenn nicht sichtbar/unsicher, sonst 0.35 bis 1.0. Keine Pixelkoordinaten."
    )


def build_screen_context_fallback_response(screen_context: str) -> str:
    context = screen_context.strip()
    if not context or context == "-":
        return "Nicht sicher gesehen: Bildschirm konnte nicht gelesen werden."
    if is_uncertain_screen_context(context):
        return "Nicht sicher gesehen: Ziel ist nicht klar erkennbar."
    return f"Gesehen: {_clean_seen_context(context)}"


def build_screen_context_display_status(screen_context: str) -> str:
    context = screen_context.strip()
    if not context or context == "-":
        return "Bildschirm: nicht gelesen"
    if is_uncertain_screen_context(context):
        return "Bildschirm: Ziel nicht sicher gesehen"
    return "Bildschirm: Ziel gesehen"


def is_uncertain_screen_context(screen_context: str) -> bool:
    normalized = screen_context.strip().lower()
    return "uncertain" in normalized or "kein klarer" in normalized or "vertrauen 0.00" in normalized


def _clean_seen_context(screen_context: str) -> str:
    context = screen_context.strip()
    if "): " in context:
        context = context.split("): ", 1)[1]
    if ". Vertrauen " in context:
        context = context.split(". Vertrauen ", 1)[0].strip()
    return context.rstrip(".") + "."


def _rough_position_to_center(position: str, left: float, top: float, width: float, height: float) -> tuple[float, float]:
    normalized = position.strip().lower()
    x_fraction = 0.5
    y_fraction = 0.5
    if "links" in normalized or "left" in normalized:
        x_fraction = 0.2
    elif "rechts" in normalized or "right" in normalized:
        x_fraction = 0.8
    if "oben" in normalized or "top" in normalized:
        y_fraction = 0.2
    elif "unten" in normalized or "bottom" in normalized:
        y_fraction = 0.8
    return left + width * x_fraction, top + height * y_fraction


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
