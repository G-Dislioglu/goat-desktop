from __future__ import annotations

import base64
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from goat_desktop import livetalk
from goat_desktop.livetalk import LiveTalkSession
from goat_desktop.tts_hint import TtsMode, load_tts_config, synthesize_speech


WAV_BYTES = b"RIFF" + b"\0" * 256


class ChatOk:
    status = "ok"
    response_text = "Ich zeige das Suchfeld nur nach Freigabe."
    time_ms = 123.0


class TtsHandler(BaseHTTPRequestHandler):
    response_mode = "ok"
    last_request: dict | None = None

    def do_POST(self) -> None:  # noqa: N802
        auth = self.headers.get("Authorization")
        if self.path == "/api/goat/stt":
            return self._handle_stt(auth)
        if self.path == "/api/goat/tts":
            return self._handle_tts(auth)
        self.send_error(404)

    def _handle_stt(self, auth: str | None) -> None:
        if auth != "Bearer test-token":
            self.send_error(401)
            return
        self._send_json({"source": "test_stt", "transcript": "zeige das suchfeld", "confidence": 0.9, "latency_ms": 111})

    def _handle_tts(self, auth: str | None) -> None:
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
        TtsHandler.last_request = payload
        audio_base64 = "" if self.response_mode == "empty" else base64.b64encode(WAV_BYTES).decode("ascii")
        self._send_json(
            {
                "source": payload["provider"],
                "voice_used": payload["voice"],
                "language_used": payload["language"],
                "mime_type": "audio/wav",
                "audio_base64": audio_base64,
                "latency_ms": 222,
            }
        )

    def _send_json(self, body: dict) -> None:
        encoded = json.dumps(body).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, _format: str, *_args) -> None:
        return


@pytest.fixture
def mock_tts_server(monkeypatch):
    TtsHandler.response_mode = "ok"
    TtsHandler.last_request = None
    server = ThreadingHTTPServer(("127.0.0.1", 0), TtsHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    monkeypatch.setenv("GOAT_TTS_MODE", "builder_proxy")
    monkeypatch.setenv("GOAT_TTS_PROVIDER", "test_tts")
    monkeypatch.setenv("GOAT_TTS_VOICE", "maya_de")
    monkeypatch.setenv("GOAT_TTS_LANGUAGE", "de-DE")
    monkeypatch.setenv("GOAT_TTS_TIMEOUT_SECONDS", "0.2")
    monkeypatch.setenv("GOAT_STT_MODE", "builder_proxy")
    monkeypatch.setenv("GOAT_STT_PROVIDER", "test_stt")
    monkeypatch.setenv("GOAT_STT_TIMEOUT_SECONDS", "0.2")
    monkeypatch.setenv("GOAT_BUILDER_URL", f"http://127.0.0.1:{server.server_port}")
    monkeypatch.setenv("GOAT_BUILDER_TOKEN", "test-token")
    yield server
    server.shutdown()
    thread.join(timeout=2)


def test_builder_tts_success(mock_tts_server, tmp_path: Path) -> None:
    output = tmp_path / "response.wav"
    result = synthesize_speech("Ich helfe dir.", output)

    assert result.status == "ok"
    assert output.exists()
    assert result.provider == "test_tts"
    assert result.voice == "maya_de"
    assert result.language == "de-DE"
    assert result.http_status == 200
    assert TtsHandler.last_request is not None
    assert TtsHandler.last_request["pronunciation_hints"]["GOAT"] == "Goat"


def test_builder_tts_auto_enables_when_builder_credentials_exist(monkeypatch) -> None:
    monkeypatch.delenv("GOAT_TTS_MODE", raising=False)
    monkeypatch.setenv("GOAT_BUILDER_URL", "https://builder.example")
    monkeypatch.setenv("GOAT_BUILDER_TOKEN", "test-token")

    assert load_tts_config().mode == TtsMode.BUILDER_PROXY


def test_builder_tts_unauthorized_returns_uncertain(monkeypatch, mock_tts_server, tmp_path: Path) -> None:
    monkeypatch.setenv("GOAT_BUILDER_TOKEN", "bad-token")
    result = synthesize_speech("Ich helfe dir.", tmp_path / "response.wav")

    assert result.status == "uncertain"
    assert result.http_status == 401


def test_builder_tts_empty_audio_returns_uncertain(mock_tts_server, tmp_path: Path) -> None:
    TtsHandler.response_mode = "empty"
    result = synthesize_speech("Ich helfe dir.", tmp_path / "response.wav")

    assert result.status == "uncertain"
    assert result.error == "empty audio"


def test_livetalk_completion_requires_builder_tts(monkeypatch, mock_tts_server, tmp_path: Path) -> None:
    monkeypatch.setenv("GOAT_LIVETALK_PROVIDER", "windows_sapi")
    monkeypatch.setenv("GOAT_LIVETALK_AUDIO_DIR", str(tmp_path))
    monkeypatch.delenv("GOAT_LIVETALK_MANUAL_TRANSCRIPT", raising=False)
    monkeypatch.setattr(livetalk, "record_windows_wav", lambda output_path, seconds: _fake_wav(output_path))
    monkeypatch.setattr(livetalk, "signal_recording_start", lambda prepare_seconds: None)
    monkeypatch.setattr(livetalk, "request_chat_response", lambda message, context=None: ChatOk())
    monkeypatch.setattr(livetalk, "play_windows_wav", lambda audio_path: audio_path.exists())
    monkeypatch.setattr(livetalk, "speak_windows_sapi", lambda text: False)

    result = LiveTalkSession().run_once()

    assert result.transcript == "zeige das suchfeld"
    assert result.stt_provider == "test_stt"
    assert result.tts_provider == "test_tts"
    assert result.chat_time_ms == 123.0
    assert result.record_seconds == 3.0
    assert result.response_audio_path is not None
    assert result.completion_ready is True


def _fake_wav(path: Path) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(WAV_BYTES)
    return True
