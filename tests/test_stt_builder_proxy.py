from __future__ import annotations

import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from goat_desktop import livetalk
from goat_desktop.livetalk import LiveTalkSession
from goat_desktop.stt_hint import SttMode, load_stt_config, transcribe_audio


class ChatOk:
    status = "ok"
    response_text = "Ich zeige das Suchfeld nur nach Freigabe."
    time_ms = 123.0


class SttHandler(BaseHTTPRequestHandler):
    response_mode = "ok"
    last_request: dict | None = None

    def do_POST(self) -> None:  # noqa: N802
        auth = self.headers.get("Authorization")
        if self.path != "/api/goat/stt":
            self.send_error(404)
            return
        if auth != "Bearer test-token":
            self.send_error(401)
            return
        if self.response_mode == "timeout":
            time.sleep(1.0)
            return
        if self.response_mode == "error":
            self.send_error(500)
            return

        length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(length).decode("utf-8"))
        SttHandler.last_request = payload
        transcript = "" if self.response_mode == "empty" else "zeige das suchfeld"
        body = {
            "source": payload["provider"],
            "transcript": transcript,
            "confidence": 0.91,
            "latency_ms": 456,
        }
        encoded = json.dumps(body).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, _format: str, *_args) -> None:
        return


@pytest.fixture
def audio_path(tmp_path: Path) -> Path:
    path = tmp_path / "sample.wav"
    path.write_bytes(b"RIFF" + b"\0" * 256)
    return path


@pytest.fixture
def mock_stt_server(monkeypatch):
    SttHandler.response_mode = "ok"
    SttHandler.last_request = None
    server = ThreadingHTTPServer(("127.0.0.1", 0), SttHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    monkeypatch.setenv("GOAT_STT_MODE", "builder_proxy")
    monkeypatch.setenv("GOAT_STT_PROVIDER", "test_stt")
    monkeypatch.setenv("GOAT_BUILDER_URL", f"http://127.0.0.1:{server.server_port}")
    monkeypatch.setenv("GOAT_BUILDER_TOKEN", "test-token")
    monkeypatch.setenv("GOAT_STT_TIMEOUT_SECONDS", "0.2")
    yield server
    server.shutdown()
    thread.join(timeout=2)


def test_builder_stt_success(mock_stt_server, audio_path: Path) -> None:
    result = transcribe_audio(audio_path)

    assert result.status == "ok"
    assert result.transcript == "zeige das suchfeld"
    assert result.provider == "test_stt"
    assert result.http_status == 200
    assert SttHandler.last_request is not None
    assert SttHandler.last_request["mime_type"] == "audio/wav"


def test_builder_stt_auto_enables_when_builder_credentials_exist(monkeypatch) -> None:
    monkeypatch.delenv("GOAT_STT_MODE", raising=False)
    monkeypatch.setenv("GOAT_BUILDER_URL", "https://builder.example")
    monkeypatch.setenv("GOAT_BUILDER_TOKEN", "test-token")

    assert load_stt_config().mode == SttMode.BUILDER_PROXY


def test_builder_stt_http_500_returns_uncertain(mock_stt_server, audio_path: Path) -> None:
    SttHandler.response_mode = "error"
    result = transcribe_audio(audio_path)

    assert result.status == "uncertain"
    assert result.http_status == 500


def test_builder_stt_invalid_token_returns_uncertain(monkeypatch, mock_stt_server, audio_path: Path) -> None:
    monkeypatch.setenv("GOAT_BUILDER_TOKEN", "bad-token")
    result = transcribe_audio(audio_path)

    assert result.status == "uncertain"
    assert result.http_status == 401


def test_builder_stt_empty_transcript_returns_uncertain(mock_stt_server, audio_path: Path) -> None:
    SttHandler.response_mode = "empty"
    result = transcribe_audio(audio_path)

    assert result.status == "uncertain"
    assert result.error == "empty transcript"


def test_livetalk_uses_builder_stt_when_available(monkeypatch, mock_stt_server, tmp_path: Path) -> None:
    monkeypatch.setenv("GOAT_LIVETALK_PROVIDER", "windows_sapi")
    monkeypatch.setenv("GOAT_LIVETALK_AUDIO_DIR", str(tmp_path))
    monkeypatch.delenv("GOAT_LIVETALK_MANUAL_TRANSCRIPT", raising=False)
    monkeypatch.setattr(livetalk, "record_windows_wav", lambda output_path, seconds: _fake_wav(output_path))
    monkeypatch.setattr(livetalk, "signal_recording_start", lambda prepare_seconds: None)
    monkeypatch.setattr(livetalk, "request_chat_response", lambda message, context=None: ChatOk())
    monkeypatch.setattr(livetalk, "speak_windows_sapi", lambda text: "zeige das suchfeld" in text.casefold())

    result = LiveTalkSession().run_once()

    assert result.transcript == "zeige das suchfeld"
    assert result.stt_provider == "test_stt"
    assert result.audio_recorded is True
    assert result.audio_played is True
    assert result.tts_provider == "windows_sapi"
    assert result.completion_ready is False


def _fake_wav(path: Path) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"RIFF" + b"\0" * 256)
    return True
