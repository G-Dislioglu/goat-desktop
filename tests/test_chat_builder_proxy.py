from __future__ import annotations

import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from goat_desktop.chat_hint import ChatMode, load_chat_config, request_chat_response


class ChatHandler(BaseHTTPRequestHandler):
    response_mode = "ok"
    last_request: dict | None = None

    def do_POST(self) -> None:  # noqa: N802
        auth = self.headers.get("Authorization")
        if self.path != "/api/goat/chat":
            self._send_json({}, 404)
            return
        if auth != "Bearer test-token":
            self._send_json({}, 401)
            return
        if self.response_mode == "timeout":
            time.sleep(1.0)
            return
        if self.response_mode == "error":
            self._send_json({}, 500)
            return

        length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(length).decode("utf-8"))
        ChatHandler.last_request = payload
        body = {
            "source": payload["provider"],
            "response_text": "Hallo, ich bin angebunden.",
            "confidence": 0.88,
            "latency_ms": 321,
            "reasoning_level_used": payload["reasoning_level"],
        }
        self._send_json(body, 200)

    def _send_json(self, body: dict, status: int) -> None:
        encoded = json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, _format: str, *_args) -> None:
        return


@pytest.fixture
def mock_chat_server(monkeypatch):
    ChatHandler.response_mode = "ok"
    ChatHandler.last_request = None
    server = ThreadingHTTPServer(("127.0.0.1", 0), ChatHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    monkeypatch.setenv("GOAT_CHAT_MODE", "builder_proxy")
    monkeypatch.setenv("GOAT_CHAT_PROVIDER", "test_chat")
    monkeypatch.setenv("GOAT_CHAT_REASONING", "minimal")
    monkeypatch.setenv("GOAT_BUILDER_URL", f"http://127.0.0.1:{server.server_port}")
    monkeypatch.setenv("GOAT_BUILDER_TOKEN", "test-token")
    monkeypatch.setenv("GOAT_CHAT_TIMEOUT_SECONDS", "0.2")
    yield server
    server.shutdown()
    thread.join(timeout=2)


def test_builder_chat_success(mock_chat_server) -> None:
    result = request_chat_response("hallo Maya", {"screen_context": "-"})

    assert result.status == "ok"
    assert result.response_text == "Hallo, ich bin angebunden."
    assert result.provider == "test_chat"
    assert result.http_status == 200
    assert ChatHandler.last_request is not None
    assert ChatHandler.last_request["message"] == "hallo Maya"
    assert ChatHandler.last_request["context"]["screen_context"] == "-"


def test_builder_chat_auto_enables_when_builder_credentials_exist(monkeypatch) -> None:
    monkeypatch.delenv("GOAT_CHAT_MODE", raising=False)
    monkeypatch.setenv("GOAT_BUILDER_URL", "https://builder.example")
    monkeypatch.setenv("GOAT_BUILDER_TOKEN", "test-token")

    assert load_chat_config().mode == ChatMode.BUILDER_PROXY


def test_builder_chat_http_500_returns_uncertain(mock_chat_server) -> None:
    ChatHandler.response_mode = "error"
    result = request_chat_response("hallo")

    assert result.status == "uncertain"
    assert result.http_status == 500


def test_builder_chat_invalid_token_returns_uncertain(monkeypatch, mock_chat_server) -> None:
    monkeypatch.setenv("GOAT_BUILDER_TOKEN", "bad-token")
    result = request_chat_response("hallo")

    assert result.status == "uncertain"
    assert result.http_status == 401


def test_builder_chat_timeout_returns_uncertain(mock_chat_server) -> None:
    ChatHandler.response_mode = "timeout"
    result = request_chat_response("hallo")

    assert result.status == "uncertain"


def test_disabled_chat_is_explicit_not_fake(monkeypatch) -> None:
    monkeypatch.setenv("GOAT_CHAT_MODE", "disabled")
    monkeypatch.delenv("GOAT_BUILDER_URL", raising=False)
    monkeypatch.delenv("GOAT_BUILDER_TOKEN", raising=False)

    result = request_chat_response("hallo")

    assert result.status == "uncertain"
    assert "Maya-KI" in result.response_text
