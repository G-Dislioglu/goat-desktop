from __future__ import annotations

import json
import wave
from pathlib import Path
from time import perf_counter

from goat_desktop import livetalk
from goat_desktop import livetalk_live
from goat_desktop.livetalk import LiveTalkSession
from goat_desktop.livetalk_live import (
    DEFAULT_GOAT_VOICE_INSTRUCTIONS,
    GeminiLiveConfig,
    GeminiLiveResult,
    _parse_json_bytes,
    _send_audio_and_video_loop,
    build_goat_voice_ws_url,
    iter_wav_pcm_chunks,
    load_gemini_live_config,
    request_gemini_live_turn,
    read_wav_as_16khz_pcm,
    with_screen_context,
    wav_signal_stats,
    write_pcm_wav,
)


def test_build_goat_voice_ws_url() -> None:
    assert build_goat_voice_ws_url("https://soulmatch-1.onrender.com") == "wss://soulmatch-1.onrender.com/api/goat/voice"
    assert build_goat_voice_ws_url("http://127.0.0.1:3001/") == "ws://127.0.0.1:3001/api/goat/voice"


def test_default_instructions_describe_goat_desktop_capabilities(monkeypatch) -> None:
    monkeypatch.delenv("GOAT_VOICE_INSTRUCTIONS", raising=False)
    config = load_gemini_live_config()

    assert config.instructions == DEFAULT_GOAT_VOICE_INSTRUCTIONS
    assert "GOAT Desktop" in config.instructions
    assert "gelben Cue-Ball" in config.instructions
    assert "sicher gegateten Aktionen" in config.instructions
    assert "allgemeine KI-Faehigkeiten" in config.instructions
    assert "kontinuierlich den Bildschirm ueber Video-Frames" in config.instructions


def test_default_live_timeout_is_not_twenty_seconds(monkeypatch) -> None:
    monkeypatch.delenv("GOAT_VOICE_TIMEOUT_SECONDS", raising=False)
    config = load_gemini_live_config()

    assert config.timeout_seconds == 10.0


def test_screen_context_is_added_to_gemini_live_instructions() -> None:
    config = GeminiLiveConfig(
        builder_url="https://builder.example",
        builder_token="token",
        timeout_seconds=10.0,
        model="gemini-3.1-flash-live-preview",
        voice="Kore",
        instructions="Basis.",
    )

    updated = with_screen_context(config, "Chrome: StepStack Ordner sichtbar.")

    assert "Aktueller gepruefter Bildschirm-Kontext" in updated.instructions
    assert "StepStack" in updated.instructions
    assert updated.builder_url == config.builder_url


def test_wav_pcm_chunks_and_writer(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "input.wav"
    with wave.open(str(source), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(16000)
        wav.writeframes(b"\x01\x02" * 4096)

    chunks = list(iter_wav_pcm_chunks(source, chunk_frames=1024))

    assert len(chunks) == 4
    assert b"".join(chunks) == b"\x01\x02" * 4096

    monkeypatch.setenv("GOAT_VOICE_OUTPUT_SAMPLE_RATE", "24000")
    output = tmp_path / "output.wav"
    write_pcm_wav(output, b"\x03\x04" * 16)

    with wave.open(str(output), "rb") as wav:
        assert wav.getframerate() == 24000
        assert wav.getnchannels() == 1
        assert wav.getsampwidth() == 2
        assert wav.readframes(16) == b"\x03\x04" * 16


def test_wav_input_is_normalized_for_gemini_live(tmp_path: Path) -> None:
    source = tmp_path / "windows-mci-default.wav"
    with wave.open(str(source), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(1)
        wav.setframerate(11025)
        wav.writeframes(b"\x80" * 11025)

    pcm = read_wav_as_16khz_pcm(source)

    assert len(pcm) in range(31900, 32100)


def test_low_signal_audio_fails_fast(tmp_path: Path) -> None:
    source = tmp_path / "quiet.wav"
    with wave.open(str(source), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(1)
        wav.setframerate(11025)
        wav.writeframes(b"\x80" * 11025)

    stats = wav_signal_stats(source)
    result = request_gemini_live_turn(
        source,
        tmp_path / "response.wav",
        config=GeminiLiveConfig(
            builder_url="https://builder.example",
            builder_token="token",
            timeout_seconds=1.0,
            model="gemini-3.1-flash-live-preview",
            voice="Kore",
            instructions="test",
        ),
    )

    assert stats["rms"] == 0.0
    assert result.status == "uncertain"
    assert result.error == "low_input_signal"
    assert result.response_text == "Keine Sprache erkannt. Bitte nach dem Ton sprechen."


def test_binary_json_message_is_not_treated_as_audio() -> None:
    assert _parse_json_bytes(b'{\n  "setupComplete": {}\n}\n') == {"setupComplete": {}}
    assert _parse_json_bytes(b"\x01\x02\x03\x04") is None


def test_video_frame_messages_are_sent_between_audio_chunks(monkeypatch) -> None:
    class FakeSocket:
        def __init__(self) -> None:
            self.sent = []

        def send(self, payload) -> None:
            self.sent.append(payload)

    socket = FakeSocket()
    monkeypatch.setattr(livetalk_live, "capture_visible_desktop_jpeg", lambda quality=None: b"jpeg-frame")

    sent_audio, sent_video = _send_audio_and_video_loop(socket, [b"audio-1", b"audio-2"], perf_counter())

    assert sent_audio == 2
    assert sent_video == 1
    assert socket.sent[0] == b"audio-1"
    frame_message = json.loads(socket.sent[1])
    assert frame_message["type"] == "video.frame"
    assert frame_message["mime_type"] == "image/jpeg"
    assert socket.sent[2] == b"audio-2"


def test_builder_offline_returns_clear_live_error_without_legacy_fallback(tmp_path: Path) -> None:
    result = request_gemini_live_turn(
        tmp_path / "missing.wav",
        tmp_path / "response.wav",
        config=GeminiLiveConfig(
            builder_url=None,
            builder_token=None,
            timeout_seconds=1.0,
            model="gemini-3.1-flash-live-preview",
            voice="Kore",
            instructions="test",
        ),
    )

    assert result.status == "uncertain"
    assert result.error == "GOAT_BUILDER_URL and GOAT_BUILDER_TOKEN are required"
    assert result.raw_evidence["mode"] == "gemini_live"


def test_livetalk_gemini_live_records_sends_and_plays(monkeypatch, tmp_path: Path) -> None:
    calls: list[Path] = []

    def fake_live_turn(audio_path: Path, output_path: Path):
        calls.append(audio_path)
        output_path.write_bytes(b"RIFF" + b"\0" * 64)
        return GeminiLiveResult(
            status="ok",
            transcript="hallo maya",
            response_text="Hallo, ich bin live.",
            audio_path=str(output_path),
            time_ms=321.0,
            raw_evidence={"mode": "gemini_live"},
        )

    monkeypatch.setenv("GOAT_LIVETALK_PROVIDER", "gemini_live")
    monkeypatch.setenv("GOAT_LIVETALK_AUDIO_DIR", str(tmp_path))
    monkeypatch.setattr(livetalk, "record_windows_wav", lambda output_path, seconds: _fake_wav(output_path))
    monkeypatch.setattr(livetalk, "signal_recording_start", lambda prepare_seconds: None)
    monkeypatch.setattr(livetalk, "request_gemini_live_turn", fake_live_turn)
    monkeypatch.setattr(livetalk, "play_windows_wav", lambda audio_path: audio_path.exists())

    result = LiveTalkSession().run_once()

    assert calls == [tmp_path / "livetalk-last-recording.wav"]
    assert result.provider == "gemini_live"
    assert result.transcript == "hallo maya"
    assert result.response_text == "Hallo, ich bin live."
    assert result.audio_recorded is True
    assert result.audio_played is True
    assert result.completion_ready is True


def test_livetalk_gemini_live_uncertain_result_shows_clear_transcript(monkeypatch, tmp_path: Path) -> None:
    def fake_live_turn(audio_path: Path, output_path: Path):
        return GeminiLiveResult(
            status="uncertain",
            transcript="",
            response_text="Keine Sprache erkannt. Bitte nach dem Ton sprechen.",
            audio_path=None,
            time_ms=12.0,
            raw_evidence={"error": "low_input_signal"},
            error="low_input_signal",
        )

    stale_audio = tmp_path / "livetalk-live-response.wav"
    stale_audio.write_bytes(b"old")
    monkeypatch.setenv("GOAT_LIVETALK_PROVIDER", "gemini_live")
    monkeypatch.setenv("GOAT_LIVETALK_AUDIO_DIR", str(tmp_path))
    monkeypatch.setattr(livetalk, "record_windows_wav", lambda output_path, seconds: _fake_wav(output_path))
    monkeypatch.setattr(livetalk, "signal_recording_start", lambda prepare_seconds: None)
    monkeypatch.setattr(livetalk, "request_gemini_live_turn", fake_live_turn)
    monkeypatch.setattr(livetalk, "play_windows_wav", lambda audio_path: False)

    result = LiveTalkSession().run_once()

    assert stale_audio.exists() is False
    assert result.transcript == "Keine Sprache erkannt"
    assert result.response_text == "Keine Sprache erkannt. Bitte nach dem Ton sprechen."
    assert result.audio_played is False
    assert result.completion_ready is False


def test_livetalk_gemini_live_recorded_uses_push_to_talk_mode(monkeypatch, tmp_path: Path) -> None:
    audio_path = tmp_path / "held-input.wav"
    _fake_wav(audio_path)

    seen_config: list[GeminiLiveConfig | None] = []

    def fake_live_turn(input_path: Path, output_path: Path, config=None):
        assert input_path == audio_path
        seen_config.append(config)
        output_path.write_bytes(b"RIFF" + b"\0" * 64)
        return GeminiLiveResult(
            status="ok",
            transcript="lange frage",
            response_text="Push-to-talk Antwort.",
            audio_path=str(output_path),
            time_ms=456.0,
            raw_evidence={"mode": "gemini_live"},
        )

    monkeypatch.setenv("GOAT_LIVETALK_PROVIDER", "gemini_live")
    monkeypatch.setenv("GOAT_LIVETALK_AUDIO_DIR", str(tmp_path))
    monkeypatch.setattr(livetalk, "request_gemini_live_turn", fake_live_turn)
    monkeypatch.setattr(livetalk, "play_windows_wav", lambda path: path.exists())

    result = LiveTalkSession().run_gemini_live_recorded(
        audio_path,
        started=perf_counter(),
        record_seconds=7.5,
        audio_recorded=True,
        screen_context="Explorer: StepStack sichtbar.",
    )

    assert result.mode == "push_to_talk_proxy"
    assert result.transcript == "lange frage"
    assert result.response_text == "Push-to-talk Antwort."
    assert result.record_seconds == 7.5
    assert result.audio_played is True
    assert seen_config and seen_config[0] is not None
    assert "StepStack" in seen_config[0].instructions


def _fake_wav(path: Path) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"RIFF" + b"\0" * 64)
    return True
