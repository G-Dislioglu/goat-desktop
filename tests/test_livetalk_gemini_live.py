from __future__ import annotations

import wave
from pathlib import Path

from goat_desktop import livetalk
from goat_desktop.livetalk import LiveTalkSession
from goat_desktop.livetalk_live import (
    DEFAULT_GOAT_VOICE_INSTRUCTIONS,
    GeminiLiveConfig,
    GeminiLiveResult,
    _parse_json_bytes,
    build_goat_voice_ws_url,
    iter_wav_pcm_chunks,
    load_gemini_live_config,
    request_gemini_live_turn,
    read_wav_as_16khz_pcm,
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


def _fake_wav(path: Path) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"RIFF" + b"\0" * 64)
    return True
