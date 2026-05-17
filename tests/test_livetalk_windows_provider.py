from __future__ import annotations

from pathlib import Path

from goat_desktop import livetalk
from goat_desktop.livetalk import LiveTalkSession


def test_mock_livetalk_remains_not_completion_ready(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("GOAT_LIVETALK_PROVIDER", "mock")
    monkeypatch.setenv("GOAT_LIVETALK_AUDIO_DIR", str(tmp_path))

    result = LiveTalkSession().run_once()

    assert result.provider == "mock"
    assert result.audio_recorded is False
    assert result.audio_played is False
    assert result.completion_ready is False


def test_windows_sapi_provider_records_and_speaks_with_manual_transcript_but_is_not_complete(
    monkeypatch,
    tmp_path: Path,
) -> None:
    class DisabledStt:
        status = "uncertain"
        transcript = ""
        provider = "none"
        error = "STT mode disabled"

    monkeypatch.setenv("GOAT_LIVETALK_PROVIDER", "windows_sapi")
    monkeypatch.setenv("GOAT_LIVETALK_AUDIO_DIR", str(tmp_path))
    monkeypatch.setenv("GOAT_LIVETALK_MANUAL_TRANSCRIPT", "zeige das suchfeld")
    monkeypatch.setattr(livetalk, "record_windows_wav", lambda output_path, seconds: _fake_wav(output_path))
    monkeypatch.setattr(livetalk, "signal_recording_start", lambda prepare_seconds: None)
    monkeypatch.setattr(livetalk, "transcribe_audio", lambda audio_path: DisabledStt())
    monkeypatch.setattr(livetalk, "speak_windows_sapi", lambda text: "zeige das suchfeld" in text.casefold())

    result = LiveTalkSession().run_once()

    assert result.provider == "windows_sapi"
    assert result.audio_recorded is True
    assert result.audio_played is True
    assert result.stt_provider == "manual"
    assert result.tts_provider == "windows_sapi"
    assert result.completion_ready is False
    assert result.audio_path is not None


def test_windows_sapi_provider_without_transcript_is_not_completion_ready(monkeypatch, tmp_path: Path) -> None:
    class DisabledStt:
        status = "uncertain"
        transcript = ""
        provider = "none"
        error = "STT mode disabled"

    monkeypatch.setenv("GOAT_LIVETALK_PROVIDER", "windows_sapi")
    monkeypatch.setenv("GOAT_LIVETALK_AUDIO_DIR", str(tmp_path))
    monkeypatch.delenv("GOAT_LIVETALK_MANUAL_TRANSCRIPT", raising=False)
    monkeypatch.setattr(livetalk, "record_windows_wav", lambda output_path, seconds: _fake_wav(output_path))
    monkeypatch.setattr(livetalk, "signal_recording_start", lambda prepare_seconds: None)
    monkeypatch.setattr(livetalk, "transcribe_audio", lambda audio_path: DisabledStt())
    monkeypatch.setattr(livetalk, "speak_windows_sapi", lambda text: True)

    result = LiveTalkSession().run_once()

    assert result.audio_recorded is True
    assert result.audio_played is True
    assert result.transcript == ""
    assert result.stt_provider == "none"
    assert result.completion_ready is False


def test_windows_sapi_provider_reports_empty_builder_transcript_clearly(monkeypatch, tmp_path: Path) -> None:
    class EmptyStt:
        status = "uncertain"
        transcript = ""
        provider = "builder_default"
        error = "empty transcript"

    monkeypatch.setenv("GOAT_LIVETALK_PROVIDER", "windows_sapi")
    monkeypatch.setenv("GOAT_LIVETALK_AUDIO_DIR", str(tmp_path))
    monkeypatch.delenv("GOAT_LIVETALK_MANUAL_TRANSCRIPT", raising=False)
    monkeypatch.setattr(livetalk, "record_windows_wav", lambda output_path, seconds: _fake_wav(output_path))
    monkeypatch.setattr(livetalk, "signal_recording_start", lambda prepare_seconds: None)
    monkeypatch.setattr(livetalk, "transcribe_audio", lambda audio_path: EmptyStt())
    monkeypatch.setattr(livetalk, "speak_windows_sapi", lambda text: True)

    result = LiveTalkSession().run_once()

    assert result.transcript == ""
    assert result.stt_provider == "builder_default"
    assert result.response_text == "Audio wurde aufgenommen, aber Builder-STT hat keinen Text erkannt."
    assert result.completion_ready is False


def test_unsupported_livetalk_provider_raises(monkeypatch) -> None:
    monkeypatch.setenv("GOAT_LIVETALK_PROVIDER", "unknown")

    try:
        LiveTalkSession().run_once()
    except RuntimeError as exc:
        assert "unsupported LiveTalk provider" in str(exc)
    else:  # pragma: no cover - explicit assertion path
        raise AssertionError("unsupported provider did not raise")


def test_windows_sapi_provider_defaults_to_five_second_recording_and_status_cue(
    monkeypatch,
    tmp_path: Path,
) -> None:
    recorded_seconds: list[float] = []
    states: list[str] = []

    monkeypatch.setenv("GOAT_LIVETALK_PROVIDER", "windows_sapi")
    monkeypatch.setenv("GOAT_LIVETALK_AUDIO_DIR", str(tmp_path))
    monkeypatch.delenv("GOAT_LIVETALK_RECORD_SECONDS", raising=False)
    monkeypatch.setenv("GOAT_LIVETALK_MANUAL_TRANSCRIPT", "zeige das suchfeld")
    monkeypatch.setattr(livetalk, "record_windows_wav", lambda output_path, seconds: recorded_seconds.append(seconds) or _fake_wav(output_path))
    monkeypatch.setattr(livetalk, "signal_recording_start", lambda prepare_seconds: states.append("cue"))
    monkeypatch.setattr(livetalk, "speak_windows_sapi", lambda text: True)

    LiveTalkSession(status_callback=states.append).run_once()

    assert recorded_seconds == [5.0]
    assert states[:3] == ["prepare", "cue", "listening"]


def _fake_wav(path: Path) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"RIFF" + b"\0" * 64)
    return True
