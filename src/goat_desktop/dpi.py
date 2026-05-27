from __future__ import annotations


def enable_dpi_awareness() -> bool:
    try:
        from ctypes import HRESULT, windll

        try:
            result = windll.shcore.SetProcessDpiAwareness(2)
            return int(result) in {0, int(HRESULT(0x80070005).value)}
        except Exception:
            return bool(windll.user32.SetProcessDPIAware())
    except Exception:
        return False
