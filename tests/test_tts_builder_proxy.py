from __future__ import annotations

import base64
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from goat_desktop import livetalk
from goat_desktop.livetalk import LiveTalkSession, read_response_aloud
from goat_desktop.stt_hint import SttResult
from goat_desktop.tts_hint import TtsMode, load_tts_config, synthesize_speech


WAV_BYTES = b"RIFF" + b"\0" * 256


class ChatOk:
    status = "ok"
    response_text = "Ich zeige das Suchfeld nur nach Freigabe."
    time_ms = 123.0


class TtsOk:
    status = "ok"
    audio_path: str | None = None
    provider = "test_tts"
    time_ms = 222.0
    error = None


class TtsError:
    status = "uncertain"
    audio_path = None
    provider = "test_tts"
    time_ms = 111.0
    error = "http_500"


class TtsHandler(BaseHTTPRequestHandler):
    response_mode = "ok"
    last_request: dict | None = None

    def do_POST(self) -> None:  # noqa: N802
        auth = self.headers.get("Authorization")
        if self.path == "/api/goat/stt":
            return self._handle_stt(auth)
        if self.path == "/api/goat/tts":
            return self._handle_tts(auth)
        self._send_json({}, 404)

    def _handle_stt(self, auth: str | None) -> None:
        if auth != "Bearer test-token":
            self._send_json({}, 401)
            return
        self._send_json({"source": "test_stt", "transcript": "zeige das suchfeld", "confidence": 0.9, "latency_ms": 111})

    def _handle_tts(self, auth: str | None) -> None:
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

    def _send_json(self, body: dict, status: int = 200) -> None:
        encoded = json.dumps(body).encode("utf-8")
        self.send_response(status)
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


def test_builder_tts_default_timeout_is_short_enough(monkeypatch) -> None:
    monkeypatch.delenv("GOAT_TTS_TIMEOUT_SECONDS", raising=False)
    monkeypatch.setenv("GOAT_BUILDER_URL", "https://builder.example")
    monkeypatch.setenv("GOAT_BUILDER_TOKEN", "test-token")

    assert load_tts_config().timeout_seconds == 8.0


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
    monkeypatch.setenv("GOAT_LIVETALK_AUTO_TTS", "1")
    monkeypatch.setenv("GOAT_LIVETALK_AUDIO_DIR", str(tmp_path))
    monkeypatch.delenv("GOAT_LIVETALK_MANUAL_TRANSCRIPT", raising=False)
    monkeypatch.setattr(livetalk, "record_windows_wav", lambda output_path, seconds: _fake_wav(output_path))
    monkeypatch.setattr(livetalk, "signal_recording_start", lambda prepare_seconds: None)
    monkeypatch.setattr(
        livetalk,
        "transcribe_audio",
        lambda audio_path: SttResult(
            status="ok",
            transcript="zeige das suchfeld",
            confidence=0.9,
            provider="test_stt",
            time_ms=111.0,
            raw_evidence={},
            http_status=200,
        ),
    )
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


def test_livetalk_default_returns_after_chat_without_blocking_tts(monkeypatch, mock_tts_server, tmp_path: Path) -> None:
    monkeypatch.setenv("GOAT_LIVETALK_PROVIDER", "windows_sapi")
    monkeypatch.delenv("GOAT_LIVETALK_AUTO_TTS", raising=False)
    monkeypatch.setenv("GOAT_LIVETALK_AUDIO_DIR", str(tmp_path))
    monkeypatch.delenv("GOAT_LIVETALK_MANUAL_TRANSCRIPT", raising=False)
    monkeypatch.setattr(livetalk, "record_windows_wav", lambda output_path, seconds: _fake_wav(output_path))
    monkeypatch.setattr(livetalk, "signal_recording_start", lambda prepare_seconds: None)
    monkeypatch.setattr(
        livetalk,
        "transcribe_audio",
        lambda audio_path: SttResult(
            status="ok",
            transcript="zeige das suchfeld",
            confidence=0.9,
            provider="test_stt",
            time_ms=111.0,
            raw_evidence={},
            http_status=200,
        ),
    )
    monkeypatch.setattr(livetalk, "request_chat_response", lambda message, context=None: ChatOk())
    monkeypatch.setattr(livetalk, "synthesize_speech", lambda text, output_path: (_ for _ in ()).throw(AssertionError("TTS should not block default LiveTalk")))

    result = LiveTalkSession().run_once()

    assert result.response_text == "Ich zeige das Suchfeld nur nach Freigabe."
    assert result.tts_provider == "not_requested"
    assert result.audio_pending is True
    assert result.completion_ready is True


def test_read_response_aloud_uses_builder_tts_and_plays_wav(monkeypatch, tmp_path: Path) -> None:
    output_paths: list[Path] = []

    def fake_synthesize(text: str, output_path: Path):
        output_path.write_bytes(WAV_BYTES)
        output_paths.append(output_path)
        result = TtsOk()
        result.audio_path = str(output_path)
        return result

    monkeypatch.setattr(livetalk, "synthesize_speech", fake_synthesize)
    monkeypatch.setattr(livetalk, "play_windows_wav", lambda audio_path: audio_path.exists())
    monkeypatch.setattr(livetalk, "speak_windows_sapi", lambda text: (_ for _ in ()).throw(AssertionError("SAPI fallback must not run")))

    result = read_response_aloud("Ich helfe dir.", tmp_path)

    assert result.status == "ok"
    assert result.audio_played is True
    assert result.tts_provider == "test_tts"
    assert output_paths == [tmp_path / "livetalk-read-aloud.wav"]


def test_read_response_aloud_reports_tts_error_without_sapi_fallback(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(livetalk, "synthesize_speech", lambda text, output_path: TtsError())
    monkeypatch.setattr(livetalk, "play_windows_wav", lambda audio_path: (_ for _ in ()).throw(AssertionError("No audio should play")))
    monkeypatch.setattr(livetalk, "speak_windows_sapi", lambda text: (_ for _ in ()).throw(AssertionError("SAPI fallback must not run")))

    result = read_response_aloud("Ich helfe dir.", tmp_path)

    assert result.status == "error"
    assert result.audio_played is False
    assert result.error == "http_500"


def _fake_wav(path: Path) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(WAV_BYTES)
    return True
