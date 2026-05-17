from __future__ import annotations

import asyncio
import json
import time
from threading import Event, Thread
from typing import Any

from PyQt6.QtCore import QObject, pyqtSignal


class BuilderBridgeClient(QObject):
    """Outbound-only WebSocket client for Builder cues.

    Run D deliberately keeps this as a proposal channel. Incoming Builder
    messages can request a cue preview, but cannot execute actions directly.
    """

    status_changed = pyqtSignal(str)
    cue_received = pyqtSignal(dict)

    def __init__(self, url: str, token: str, reconnect_seconds: float = 1.0) -> None:
        super().__init__()
        self.url = url
        self.token = token
        self.reconnect_seconds = reconnect_seconds
        self._stop = Event()
        self._thread: Thread | None = None
        self.last_message: dict[str, Any] | None = None
        self.last_error: str | None = None

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = Thread(target=self._run_loop, name="goat-builder-bridge", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()

    def _run_loop(self) -> None:
        asyncio.run(self._connect_forever())

    async def _connect_forever(self) -> None:
        while not self._stop.is_set():
            try:
                await self._connect_once()
            except Exception as exc:  # noqa: BLE001 - surfaced in status for diagnostics
                self.last_error = repr(exc)
                self.status_changed.emit("builder: reconnecting")
                await asyncio.sleep(self.reconnect_seconds)

    async def _connect_once(self) -> None:
        import websockets

        headers = {"Authorization": f"Bearer {self.token}"}
        async with websockets.connect(
            self.url,
            additional_headers=headers,
            open_timeout=5,
            ping_interval=15,
            close_timeout=2,
        ) as websocket:
            self.status_changed.emit("builder: connected")
            await asyncio.wait_for(
                websocket.send(
                    json.dumps(
                        {
                            "type": "hello",
                            "client": "goat-desktop",
                            "capabilities": ["screen_cue_preview", "user_approval_required"],
                            "ts": time.time(),
                        }
                    )
                ),
                timeout=3,
            )
            async for raw_message in websocket:
                if self._stop.is_set():
                    break
                message = json.loads(raw_message)
                self.last_message = message
                if message.get("type") in {"test_cue", "screen_cue"}:
                    self.cue_received.emit(message)
