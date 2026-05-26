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


def collect_visible_uia_elements(limit: int = 180) -> dict[str, Any]:
    started = perf_counter()
    try:
        from pywinauto import Desktop

        desktop = Desktop(backend="uia")
        roots = _collect_roots(desktop)
        elements: list[UiaElementInfo] = []
        seen: set[tuple[str, int, int, int, int]] = set()
        for root in roots[:30]:
            _append_element(elements, root, seen)
            for child in _iter_bounded_children(root, max_count=90, max_depth=4):
                _append_element(elements, child, seen)
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


def find_uia_match_for_message(
    message: str,
    min_score: float = 0.58,
    early_score: float = 0.95,
    scan_limit: int = 180,
) -> dict[str, Any]:
    started = perf_counter()
    try:
        from pywinauto import Desktop

        target_terms = _target_terms(message)
        if not target_terms:
            return {
                "ok": True,
                "match": None,
                "elements_scanned": 0,
                "time_ms": round((perf_counter() - started) * 1000, 2),
                "effects": _no_action_effects(),
            }
        if _message_mentions_taskbar(message):
            taskbar_match, taskbar_scanned = _find_taskbar_match_uia(target_terms, min_score=min_score, early_score=early_score)
            if taskbar_match is not None:
                return {
                    "ok": True,
                    "match": taskbar_match,
                    "elements_scanned": taskbar_scanned,
                    "time_ms": round((perf_counter() - started) * 1000, 2),
                    "source": "uia_taskbar",
                    "effects": _no_action_effects(),
                }
        if _message_mentions_window(message):
            window_match, window_scanned = _find_window_match_win32(target_terms, min_score=min_score, early_score=early_score)
            if window_match is not None:
                return {
                    "ok": True,
                    "match": window_match,
                    "elements_scanned": window_scanned,
                    "time_ms": round((perf_counter() - started) * 1000, 2),
                    "source": "win32_window",
                    "effects": _no_action_effects(),
                }
        if not _message_mentions_taskbar(message) and not _message_mentions_window(message):
            fast_match, fast_scanned = _find_desktop_icon_match_win32(target_terms, min_score=min_score, early_score=early_score)
            if fast_match is not None:
                return {
                    "ok": True,
                    "match": fast_match,
                    "elements_scanned": fast_scanned,
                    "time_ms": round((perf_counter() - started) * 1000, 2),
                    "source": "win32_desktop",
                    "effects": _no_action_effects(),
                }
        desktop = Desktop(backend="uia")
        roots = _collect_roots(desktop)
        match, scanned = _find_best_uia_match_in_wrappers(
            roots,
            target_terms,
            min_score=min_score,
            early_score=early_score,
            scan_limit=scan_limit,
        )
        return {
            "ok": True,
            "match": match,
            "elements_scanned": scanned,
            "time_ms": round((perf_counter() - started) * 1000, 2),
            "effects": _no_action_effects(),
        }
    except Exception as exc:  # noqa: BLE001 - UIA is an optional read-only hint
        return {
            "ok": False,
            "match": None,
            "error": type(exc).__name__,
            "elements_scanned": 0,
            "time_ms": round((perf_counter() - started) * 1000, 2),
            "effects": _no_action_effects(),
        }


def build_uia_screen_context(match: dict[str, Any]) -> str:
    element = match.get("element") if isinstance(match.get("element"), dict) else {}
    name = _display_name(str(element.get("name") or "Ziel"))
    control_type = str(element.get("control_type") or "UI-Element").strip() or "UI-Element"
    source = str(element.get("source") or "uia").strip() or "uia"
    prefix_by_source = {
        "uia": "Lokales UIA",
        "win32_desktop": "Lokaler Screen",
        "win32_window": "Lokales Fenster",
        "uia_taskbar": "Lokale Taskleiste",
    }
    prefix = prefix_by_source.get(source, "Lokaler Screen")
    score = float(match.get("score") or 0.0)
    return f"{prefix}: {name} ({control_type}) sichtbar. Vertrauen {score:.2f} via {source}."


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
    source = str(element.get("source") or "uia").strip() or "uia"
    return {
        "available": True,
        "label": _display_name(str(element.get("name") or "UIA-Ziel")),
        "region": {
            "x": round(left, 2),
            "y": round(top, 2),
            "width": round(width, 2),
            "height": round(height, 2),
        },
        "confidence": float(match.get("score") or 0.0),
        "source": source,
    }


def _collect_roots(desktop) -> list[Any]:
    roots: list[Any] = []
    seen_wrappers: set[int] = set()

    def add(wrapper) -> None:
        key = _wrapper_key(wrapper)
        if key not in seen_wrappers:
            seen_wrappers.add(key)
            roots.append(wrapper)

    for class_name in ("Progman", "WorkerW", "CabinetWClass", "Shell_TrayWnd"):
        try:
            for window in desktop.windows(class_name=class_name, visible_only=True):
                add(window)
        except Exception:
            continue

    try:
        for window in desktop.windows(visible_only=True):
            add(window)
    except Exception:
        pass

    return roots


def _find_best_uia_match_in_wrappers(
    roots: list[Any],
    target_terms: list[str],
    min_score: float,
    early_score: float,
    scan_limit: int,
) -> tuple[dict[str, Any] | None, int]:
    best: tuple[float, dict[str, Any]] | None = None
    seen: set[tuple[str, int, int, int, int]] = set()
    scanned = 0
    for root in roots[:30]:
        for wrapper in _iter_wrapper_with_children(root, max_count=90, max_depth=4):
            element = _read_element(wrapper, seen)
            if element is None:
                continue
            scanned += 1
            score = _match_score(target_terms, element.name)
            if best is None or score > best[0]:
                best = (score, element.to_dict())
                if score >= early_score:
                    return _build_match(best, target_terms), scanned
            if scanned >= scan_limit:
                break
        if scanned >= scan_limit:
            break
    if best is None or best[0] < min_score:
        return None, scanned
    return _build_match(best, target_terms), scanned


def _find_desktop_icon_match_win32(target_terms: list[str], min_score: float, early_score: float) -> tuple[dict[str, Any] | None, int]:
    try:
        from pywinauto import Desktop

        desktop = Desktop(backend="win32")
        list_view = desktop.window(class_name="Progman").child_window(class_name="SysListView32")
        if not list_view.exists(timeout=0.5):
            return None, 0
        item_count = int(list_view.item_count())
    except Exception:
        return None, 0

    best: tuple[float, dict[str, Any]] | None = None
    scanned = 0
    for index in range(max(0, item_count)):
        try:
            item = list_view.get_item(index)
            name = str(item.text() or "").strip()
            rect = item.rectangle()
        except Exception:
            continue
        if not name:
            continue
        scanned += 1
        score = _match_score(target_terms, name)
        element = UiaElementInfo(
            name=name,
            control_type="ListItem",
            rect={"left": float(rect.left), "top": float(rect.top), "right": float(rect.right), "bottom": float(rect.bottom)},
            source="win32_desktop",
        ).to_dict()
        if best is None or score > best[0]:
            best = (score, element)
            if score >= early_score:
                return _build_match(best, target_terms), scanned
    if best is None or best[0] < min_score:
        return None, scanned
    return _build_match(best, target_terms), scanned


def _find_window_match_win32(target_terms: list[str], min_score: float, early_score: float) -> tuple[dict[str, Any] | None, int]:
    try:
        from pywinauto import Desktop

        windows = Desktop(backend="win32").windows(visible_only=True)
    except Exception:
        return None, 0

    best: tuple[float, dict[str, Any]] | None = None
    scanned = 0
    for window in windows[:40]:
        try:
            name = str(window.window_text() or "").strip()
            rect = window.rectangle()
            control_type = "Window"
        except Exception:
            continue
        if not name:
            continue
        scanned += 1
        score = _match_score(target_terms, name)
        element = UiaElementInfo(
            name=name,
            control_type=control_type,
            rect={"left": float(rect.left), "top": float(rect.top), "right": float(rect.right), "bottom": float(rect.bottom)},
            source="win32_window",
        ).to_dict()
        if best is None or score > best[0]:
            best = (score, element)
            if score >= early_score:
                return _build_match(best, target_terms), scanned
    if best is None or best[0] < min_score:
        return None, scanned
    return _build_match(best, target_terms), scanned


def _find_taskbar_match_uia(target_terms: list[str], min_score: float, early_score: float) -> tuple[dict[str, Any] | None, int]:
    try:
        from pywinauto import Desktop

        taskbars = Desktop(backend="uia").windows(class_name="Shell_TrayWnd", visible_only=True)
    except Exception:
        return None, 0
    match, scanned = _find_best_uia_match_in_wrappers(taskbars, target_terms, min_score, early_score, scan_limit=100)
    if match is None:
        return None, scanned
    element = match.get("element") if isinstance(match.get("element"), dict) else {}
    element["source"] = "uia_taskbar"
    return match, scanned


def _display_name(name: str) -> str:
    clean = name.strip().replace("\u2013", "-").replace("\u2014", "-")
    if not clean:
        return "Ziel"
    known_names = {
        "stepstack": "StepStack",
    }
    if clean.lower() in known_names:
        return known_names[clean.lower()]
    if clean.islower() and any(char.isalpha() for char in clean):
        return clean[:1].upper() + clean[1:]
    return clean


def _build_match(best: tuple[float, dict[str, Any]], target_terms: list[str]) -> dict[str, Any]:
    return {
        "element": best[1],
        "score": round(best[0], 3),
        "target_terms": target_terms,
    }


def _iter_wrapper_with_children(root, max_count: int, max_depth: int):
    yield root
    yield from _iter_bounded_children(root, max_count=max_count, max_depth=max_depth)


def _iter_bounded_children(root, max_count: int, max_depth: int):
    queue: list[tuple[Any, int]] = [(root, 0)]
    yielded = 0
    while queue and yielded < max_count:
        parent, depth = queue.pop(0)
        if depth >= max_depth:
            continue
        try:
            children = parent.children()
        except Exception:
            continue
        for child in children:
            yield child
            yielded += 1
            if yielded >= max_count:
                break
            queue.append((child, depth + 1))


def _append_element(elements: list[UiaElementInfo], wrapper, seen: set[tuple[str, int, int, int, int]] | None = None) -> None:
    element = _read_element(wrapper, seen)
    if element is not None:
        elements.append(element)


def _read_element(wrapper, seen: set[tuple[str, int, int, int, int]] | None = None) -> UiaElementInfo | None:
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
        dedupe_key = (name.lower(), round(left), round(top), round(right), round(bottom))
        if seen is not None:
            if dedupe_key in seen:
                return None
            seen.add(dedupe_key)
        return UiaElementInfo(
            name=name,
            control_type=control_type,
            rect={"left": left, "top": top, "right": right, "bottom": bottom},
        )
    except Exception:
        return None


def _wrapper_key(wrapper) -> int:
    try:
        return int(wrapper.handle)
    except Exception:
        return id(wrapper)


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
        "taskleiste",
        "taskbar",
        "fenster",
        "window",
        "app",
        "programm",
        "anwendung",
        "in",
        "kannst",
        "mich",
        "zum",
        "zur",
        "navigieren",
        "navigiere",
    }
    terms = [part for part in normalized.split() if len(part) >= 3 and part not in stopwords]
    if "goat desktop" in normalized and "desktop" not in terms:
        terms.append("desktop")
    return terms


def _message_mentions_taskbar(message: str) -> bool:
    normalized = _normalize(message)
    return "taskleiste" in normalized.split() or "taskbar" in normalized.split()


def _message_mentions_window(message: str) -> bool:
    normalized = _normalize(message)
    parts = normalized.split()
    return "fenster" in parts or "window" in parts


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
        .replace("\u00e4", "ae")
        .replace("\u00f6", "oe")
        .replace("\u00fc", "ue")
        .replace("\u00df", "ss")
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
