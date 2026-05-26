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
    "sichtbar",
    "navigier",
)

_VISION_FALLBACK_TRIGGERS = (
    "pruef genau",
    "genau pruefen",
    "genauer hinsehen",
    "mit vision",
    "per vision",
    "visuell pruefen",
    "screenshot",
    "bildschirm pruefen",
    "langsamer fallback",
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
    normalized = _normalized_message(message)
    return any(trigger in normalized for trigger in _SCREEN_CONTEXT_TRIGGERS)


def should_use_vision_fallback(message: str) -> bool:
    normalized = _normalized_message(message)
    return _looks_like_screen_request(normalized) and any(trigger in normalized for trigger in _VISION_FALLBACK_TRIGGERS)


def build_local_screen_miss_summary(message: str, resolution: dict[str, Any] | None = None) -> str:
    data = resolution if isinstance(resolution, dict) else {}
    source_path = str(data.get("source_path") or "local_screen").strip() or "local_screen"
    scanned = data.get("elements_scanned")
    scan_note = f", {int(scanned)} Elemente gelesen" if isinstance(scanned, int) and scanned > 0 else ""
    target = _screen_question_target(message)
    target_note = f" fuer '{target}'" if target else ""
    return f"Lokaler Screen: Ziel{target_note} nicht sicher gesehen{scan_note}. Vertrauen 0.00 via {source_path}."


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
    if is_unavailable_screen_context(context):
        reason = _unavailable_reason_for_context(context)
        reason_suffix = f" Grund: {reason}." if reason else ""
        return f"Nicht sicher gesehen: Bildschirm konnte nicht gelesen werden.{reason_suffix}"
    if is_local_screen_miss_context(context):
        source_label = _source_label_for_context(context)
        source_suffix = f" Quelle: {source_label}." if source_label else ""
        return f"Nicht gefunden: Ich habe lokal geprueft, aber keinen passenden Treffer gesehen.{source_suffix}"
    if is_uncertain_screen_context(context):
        reason = _uncertain_reason_for_context(context)
        reason_suffix = f" Grund: {reason}." if reason else ""
        return f"Nicht sicher gesehen: Ziel ist im aktuellen Bildschirmbild nicht klar erkennbar.{reason_suffix}"
    source_label = _source_label_for_context(context)
    source_suffix = f" Quelle: {source_label}." if source_label else ""
    return f"Gesehen: {_clean_seen_context(context)}{source_suffix}"


def build_screen_context_display_status(screen_context: str) -> str:
    context = screen_context.strip()
    if not context or context == "-":
        return "Bildschirm: noch nicht geprueft"
    if is_local_screen_miss_context(context):
        source_label = _source_label_for_context(context)
        return f"Nicht gefunden ({source_label})" if source_label else "Nicht gefunden"
    if is_uncertain_screen_context(context):
        return "Nicht sicher gesehen"
    if _is_win32_window_context(context):
        return "Fenster gefunden"
    if _is_uia_taskbar_context(context):
        return "Taskleiste gefunden"
    if _is_win32_desktop_context(context):
        return "Desktop gefunden"
    if _is_uia_context(context):
        return "Bildschirm gefunden"
    return "Bildschirm gefunden"


def is_clear_screen_context(screen_context: str) -> bool:
    context = screen_context.strip()
    return bool(context) and context != "-" and not is_uncertain_screen_context(context) and not is_unavailable_screen_context(context)


def should_answer_screen_question_locally(message: str, screen_context: str) -> bool:
    return should_use_screen_context(message) and _has_screen_context_result(screen_context)


def is_uncertain_screen_context(screen_context: str) -> bool:
    normalized = screen_context.strip().lower()
    return "uncertain" in normalized or "kein klarer" in normalized or "vertrauen 0.00" in normalized


def is_local_screen_miss_context(screen_context: str) -> bool:
    normalized = screen_context.strip().lower()
    return (
        normalized.startswith("lokaler screen:")
        and "nicht sicher gesehen" in normalized
        and any(
            marker in normalized
            for marker in (
                "via win32_desktop_miss",
                "via win32_window_miss",
                "via uia_taskbar_miss",
                "via uia_scan",
                "via local_screen",
            )
        )
    )


def is_unavailable_screen_context(screen_context: str) -> bool:
    normalized = screen_context.strip().lower()
    return (
        not normalized
        or normalized == "-"
        or "bildschirm-kontext nicht verfuegbar" in normalized
        or "bildschirm-kontext fehlgeschlagen" in normalized
        or "bildschirm konnte nicht gelesen werden" in normalized
        or "screen capture failed" in normalized
        or "vision failed" in normalized
    )


def _clean_seen_context(screen_context: str) -> str:
    context = screen_context.strip()
    if context.startswith("Lokales UIA: "):
        context = context.removeprefix("Lokales UIA: ").strip()
    if context.startswith("Lokaler Screen: "):
        context = context.removeprefix("Lokaler Screen: ").strip()
    if context.startswith("Lokales Fenster: "):
        context = context.removeprefix("Lokales Fenster: ").strip()
    if context.startswith("Lokale Taskleiste: "):
        context = context.removeprefix("Lokale Taskleiste: ").strip()
    if "): " in context:
        context = context.split("): ", 1)[1]
    if ". Vertrauen " in context:
        context = context.split(". Vertrauen ", 1)[0].strip()
    context = _strip_control_type_hints(context)
    return context.rstrip(".") + "."


def _source_label_for_context(screen_context: str) -> str:
    if "via win32_desktop_miss" in screen_context:
        return "Desktop"
    if "via win32_window_miss" in screen_context:
        return "Fenster"
    if "via uia_taskbar_miss" in screen_context:
        return "Taskleiste"
    if _is_win32_window_context(screen_context):
        return "Fenster"
    if _is_uia_taskbar_context(screen_context):
        return "Taskleiste"
    if _is_win32_desktop_context(screen_context):
        return "Desktop"
    if _is_uia_context(screen_context):
        return "Bildschirm"
    return ""


def _has_screen_context_result(screen_context: str) -> bool:
    context = screen_context.strip()
    return bool(context) and context != "-"


def _unavailable_reason_for_context(screen_context: str) -> str:
    normalized = screen_context.strip().lower()
    if "goat_builder_url and goat_builder_token are required" in normalized:
        return "Vision-Builder ist nicht konfiguriert"
    if "screen capture failed" in normalized or "capture failed" in normalized:
        return "Screenshot-Erfassung fehlgeschlagen"
    if "missing dependency" in normalized:
        return "lokale Bildschirm-Erfassung ist unvollstaendig"
    if "timeout" in normalized:
        return "Vision-Builder antwortet zu langsam"
    if "http_401" in normalized or "unauthorized" in normalized:
        return "Vision-Builder hat die Anfrage abgelehnt"
    if "vision failed" in normalized or "vision fehlgeschlagen" in normalized:
        return "Vision-Auswertung fehlgeschlagen"
    return ""


def _uncertain_reason_for_context(screen_context: str) -> str:
    normalized = screen_context.strip().lower()
    if "unknown" in normalized:
        return "Position unklar"
    if "vertrauen 0.00" in normalized:
        return "kein verlaesslicher Treffer"
    if "kein klarer" in normalized:
        return "kein klarer Treffer"
    return ""


def _strip_control_type_hints(text: str) -> str:
    for control_type in (
        "Button",
        "ListItem",
        "Window",
        "Edit",
        "Text",
        "Pane",
        "MenuItem",
        "TabItem",
        "CheckBox",
        "ComboBox",
    ):
        text = text.replace(f" ({control_type})", "")
    return " ".join(text.split())


def _is_uia_context(screen_context: str) -> bool:
    normalized = screen_context.strip().lower()
    return normalized.startswith("lokales uia:") or " via uia" in normalized


def _is_win32_desktop_context(screen_context: str) -> bool:
    normalized = screen_context.strip().lower()
    return normalized.startswith("lokaler screen:") or " via win32_desktop" in normalized


def _is_win32_window_context(screen_context: str) -> bool:
    normalized = screen_context.strip().lower()
    return normalized.startswith("lokales fenster:") or " via win32_window" in normalized


def _is_uia_taskbar_context(screen_context: str) -> bool:
    normalized = screen_context.strip().lower()
    return normalized.startswith("lokale taskleiste:") or " via uia_taskbar" in normalized


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


def _normalized_message(message: str) -> str:
    return (
        " ".join(message.strip().lower().split())
        .replace("\u00e4", "ae")
        .replace("\u00f6", "oe")
        .replace("\u00fc", "ue")
        .replace("\u00df", "ss")
    )


def _looks_like_screen_request(normalized_message: str) -> bool:
    return should_use_screen_context(normalized_message) or any(
        token in normalized_message for token in ("desktop", "bildschirm", "screen", "vision", "screenshot")
    )


def _screen_question_target(message: str) -> str:
    normalized = _normalized_message(message)
    for token in (
        "siehst du",
        "wo ist",
        "wo finde",
        "finde",
        "zeig mir",
        "auf meinem desktop",
        "auf dem desktop",
        "auf dem bildschirm",
        "im fenster",
        "bitte",
        "pruef genau",
        "genau pruefen",
        "mit vision",
        "per vision",
        "visuell pruefen",
        "screenshot",
        "taskleiste",
        "taskbar",
        "fenster",
        "window",
    ):
        normalized = normalized.replace(token, " ")
    for token in (" den ", " die ", " das ", " der ", " ordner ", " button ", " schaltflaeche "):
        normalized = normalized.replace(token, " ")
    target = " ".join(part for part in normalized.replace("?", " ").replace("!", " ").split() if len(part) >= 3)
    return target[:80]


def build_chat_context(screen_context: str, target: str) -> dict[str, str]:
    return {
        "screen_context": screen_context.strip() or "-",
        "target": target.strip() or "Kein Ziel markiert",
        "safety_rule": "desktop actions require explicit user approval",
    }
