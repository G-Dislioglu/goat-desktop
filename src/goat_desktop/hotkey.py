from __future__ import annotations

from ctypes import wintypes, windll
from typing import Callable

from PyQt6.QtCore import QAbstractNativeEventFilter, QByteArray
from PyQt6.QtWidgets import QApplication


WM_HOTKEY = 0x0312
MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
VK_ESCAPE = 0x1B
VK_G = 0x47


class EmergencyHotkey(QAbstractNativeEventFilter):
    """Global Ctrl+Alt+Esc emergency stop."""

    def __init__(
        self,
        callback: Callable[[], None],
        hotkey_id: int = 0x470A,
        modifiers: int = MOD_CONTROL | MOD_ALT,
        virtual_key: int = VK_ESCAPE,
    ) -> None:
        super().__init__()
        self.callback = callback
        self.hotkey_id = hotkey_id
        self.registered = bool(windll.user32.RegisterHotKey(None, hotkey_id, modifiers, virtual_key))
        QApplication.instance().installNativeEventFilter(self)

    def nativeEventFilter(self, event_type: QByteArray, message) -> tuple[bool, int]:
        msg = wintypes.MSG.from_address(int(message))
        if msg.message == WM_HOTKEY and msg.wParam == self.hotkey_id:
            self.callback()
            return True, 0
        return False, 0

    def unregister(self) -> None:
        if self.registered:
            windll.user32.UnregisterHotKey(None, self.hotkey_id)
            self.registered = False
