from __future__ import annotations

from dataclasses import asdict, dataclass
from time import perf_counter
from typing import Any


@dataclass(frozen=True)
class UiaElementInfo:
    name: str
    control_type: str
    rect: dict[str, float]
    source: str = "uia"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def collect_visible_uia_elements(limit: int = 160) -> dict[str, Any]:
    started = perf_counter()
    try:
        from pywinauto import Desktop

        desktop = Desktop(backend="uia")
        windows = desktop.windows(visible_only=True)
        elements: list[UiaElementInfo] = []
        for window in windows[:20]:
            _append_element(elements, window)
            for child in window.descendants()[:80]:
                _append_element(elements, child)
                if len(elements) >= limit:
                    break
            if len(elements) >= limit:
                break
        return {
            "ok": True,
            "elements": [element.to_dict() for element in elements],
            "time_ms": round((perf_counter() - started) * 1000, 2),
            "effects": _no_action_effects(),
        }
    except Exception as exc:  # noqa: BLE001 - UIA is an optional read-only hint
        return {
            "ok": False,
            "error": type(exc).__name__,
            "elements": [],
            "time_ms": round((perf_counter() - started) * 1000, 2),
            "effects": _no_action_effects(),
        }


def find_best_uia_match(elements: list[dict[str, Any]], message: str, min_score: float = 0.58) -> dict[str, Any] | None:
    target_terms = _target_terms(message)
    if not target_terms:
        return None
    best: tuple[float, dict[str, Any]] | None = None
    for element in elements:
        name = str(element.get("name") or "").strip()
        if not name:
            continue
        score = _match_score(target_terms, name)
        if best is None or score > best[0]:
            best = (score, element)
    if best is None or best[0] < min_score:
        return None
    return {
        "element": best[1],
        "score": round(best[0], 3),
        "target_terms": target_terms,
    }


def build_uia_screen_context(match: dict[str, Any]) -> str:
    element = match.get("element") if isinstance(match.get("element"), dict) else {}
    name = str(element.get("name") or "Ziel").strip() or "Ziel"
    control_type = str(element.get("control_type") or "UI-Element").strip() or "UI-Element"
    score = float(match.get("score") or 0.0)
    return f"Lokales UIA: {name} ({control_type}) sichtbar. Vertrauen {score:.2f} via uia."


def build_uia_marker(match: dict[str, Any]) -> dict[str, Any] | None:
    element = match.get("element") if isinstance(match.get("element"), dict) else {}
    rect = element.get("rect") if isinstance(element.get("rect"), dict) else {}
    try:
        left = float(rect.get("left"))
        top = float(rect.get("top"))
        right = float(rect.get("right"))
        bottom = float(rect.get("bottom"))
    except (TypeError, ValueError):
        return None
    width = right - left
    height = bottom - top
    if width <= 0 or height <= 0:
        return None
    return {
        "available": True,
        "label": str(element.get("name") or "UIA-Ziel"),
        "region": {
            "x": round(left, 2),
            "y": round(top, 2),
            "width": round(width, 2),
            "height": round(height, 2),
        },
        "confidence": float(match.get("score") or 0.0),
        "source": "uia",
    }


def _append_element(elements: list[UiaElementInfo], wrapper) -> None:
    try:
        info = wrapper.element_info
        name = str(getattr(info, "name", "") or "").strip()
        rect = getattr(info, "rectangle", None)
        control_type = str(getattr(info, "control_type", "") or "").strip()
        if not name or rect is None:
            return
        left = float(rect.left)
        top = float(rect.top)
        right = float(rect.right)
        bottom = float(rect.bottom)
        if right <= left or bottom <= top:
            return
        elements.append(
            UiaElementInfo(
                name=name,
                control_type=control_type,
                rect={"left": left, "top": top, "right": right, "bottom": bottom},
            )
        )
    except Exception:
        return


def _target_terms(message: str) -> list[str]:
    normalized = _normalize(message)
    stopwords = {
        "siehst",
        "du",
        "den",
        "die",
        "das",
        "der",
        "wo",
        "ist",
        "finde",
        "zeig",
        "mir",
        "auf",
        "meinem",
        "mein",
        "desktop",
        "bildschirm",
        "ordner",
        "button",
        "schaltflaeche",
        "schaltfläche",
        "kannst",
        "mich",
        "zum",
        "zur",
        "navigieren",
        "navigiere",
    }
    return [part for part in normalized.split() if len(part) >= 3 and part not in stopwords]


def _match_score(target_terms: list[str], name: str) -> float:
    normalized_name = _normalize(name)
    if not normalized_name:
        return 0.0
    hits = 0.0
    for term in target_terms:
        if term in normalized_name:
            hits += 1.0
        elif any(part.startswith(term) or term.startswith(part) for part in normalized_name.split()):
            hits += 0.6
    coverage = hits / max(1, len(target_terms))
    compact_target = "".join(target_terms)
    compact_name = normalized_name.replace(" ", "")
    if compact_target and compact_target in compact_name:
        coverage = max(coverage, 0.95)
    return min(1.0, coverage)


def _normalize(text: str) -> str:
    return (
        text.lower()
        .replace("ä", "ae")
        .replace("ö", "oe")
        .replace("ü", "ue")
        .replace("ß", "ss")
        .replace("-", " ")
        .replace("_", " ")
        .replace(".", " ")
        .replace("?", " ")
        .replace("!", " ")
        .strip()
    )


def _no_action_effects() -> dict[str, Any]:
    return {
        "providerCallsMade": 0,
        "desktopActionsExecuted": False,
        "mouseActionsExecuted": False,
        "keyboardActionsExecuted": False,
        "tradingActionsExecuted": False,
        "mayExecuteRealAction": False,
    }
