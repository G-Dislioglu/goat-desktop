from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from time import perf_counter
from typing import Any

from ctypes import byref, create_unicode_buffer, windll, wintypes


@dataclass(frozen=True)
class WindowInfo:
    hwnd: int
    title: str
    rect: list[int]
    foreground: bool

    @property
    def width(self) -> int:
        return max(0, self.rect[2] - self.rect[0])

    @property
    def height(self) -> int:
        return max(0, self.rect[3] - self.rect[1])

    @property
    def center(self) -> tuple[int, int]:
        return ((self.rect[0] + self.rect[2]) // 2, (self.rect[1] + self.rect[3]) // 2)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["width"] = self.width
        data["height"] = self.height
        data["center"] = list(self.center)
        return data


def get_active_window() -> WindowInfo:
    hwnd = int(windll.user32.GetForegroundWindow())
    rect = wintypes.RECT()
    if hwnd:
        windll.user32.GetWindowRect(hwnd, byref(rect))
    title = create_unicode_buffer(512)
    if hwnd:
        windll.user32.GetWindowTextW(hwnd, title, len(title))
    return WindowInfo(
        hwnd=hwnd,
        title=title.value,
        rect=[int(rect.left), int(rect.top), int(rect.right), int(rect.bottom)],
        foreground=bool(hwnd),
    )


def capture_active_window(output_path: Path | None = None) -> dict[str, Any]:
    try:
        import mss
        from PIL import Image
    except ImportError as exc:  # pragma: no cover - exercised by runtime health only
        return {
            "ok": False,
            "error": f"missing dependency: {exc.name}",
            "active_window": get_active_window().to_dict(),
        }

    window = get_active_window()
    left, top, right, bottom = window.rect
    width = max(1, right - left)
    height = max(1, bottom - top)
    started = perf_counter()
    with mss.mss() as sct:
        raw = sct.grab({"left": left, "top": top, "width": width, "height": height})
        image = Image.frombytes("RGB", raw.size, raw.rgb)
    elapsed_ms = round((perf_counter() - started) * 1000, 2)

    saved_to: str | None = None
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        image.save(output_path, optimize=True)
        saved_to = str(output_path)

    return {
        "ok": True,
        "active_window": window.to_dict(),
        "capture": {
            "source": "mss",
            "scope": "active_window",
            "width": image.width,
            "height": image.height,
            "time_ms": elapsed_ms,
            "saved_to": saved_to,
        },
    }


def capture_visible_desktop(output_path: Path | None = None) -> dict[str, Any]:
    try:
        import mss
        from PIL import Image
    except ImportError as exc:  # pragma: no cover - exercised by runtime health only
        return {
            "ok": False,
            "error": f"missing dependency: {exc.name}",
            "active_window": get_active_window().to_dict(),
        }

    started = perf_counter()
    with mss.mss() as sct:
        monitor = sct.monitors[0]
        raw = sct.grab(monitor)
        image = Image.frombytes("RGB", raw.size, raw.rgb)
        scope = {
            "left": int(monitor["left"]),
            "top": int(monitor["top"]),
            "width": int(monitor["width"]),
            "height": int(monitor["height"]),
        }
    elapsed_ms = round((perf_counter() - started) * 1000, 2)

    saved_to: str | None = None
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        image.save(output_path, optimize=True)
        saved_to = str(output_path)

    return {
        "ok": True,
        "active_window": get_active_window().to_dict(),
        "capture": {
            "source": "mss",
            "scope": "visible_desktop",
            "left": scope["left"],
            "top": scope["top"],
            "width": image.width,
            "height": image.height,
            "time_ms": elapsed_ms,
            "saved_to": saved_to,
        },
    }
