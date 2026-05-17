from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import time
import winsound
from collections.abc import Callable
from ctypes import create_unicode_buffer, windll
from dataclasses import asdict, dataclass
from pathlib import Path
from time import perf_counter

from goat_desktop.chat_hint import request_chat_response
from goat_desktop.stt_hint import transcribe_audio
from goat_desktop.tts_hint import synthesize_speech


@dataclass(frozen=True)
class LiveTalkResult:
    provider: str
    mode: str
    transcript: str
    response_text: str
    time_ms: float
    audio_recorded: bool
    audio_played: bool
    stt_provider: str = "none"
    tts_provider: str = "none"
    stt_time_ms: float = 0.0
    chat_time_ms: float = 0.0
    tts_time_ms: float = 0.0
    record_seconds: float = 0.0
    audio_path: str | None = None
    response_audio_path: str | None = None
    completion_ready: bool = False
    audio_pending: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class ReadAloudResult:
    status: str
    audio_played: bool
    tts_provider: str
    tts_time_ms: float
    audio_path: str | None = None
    error: str | None = None


class LiveTalkSession:
    """Half-duplex LiveTalk shell.

    The mock path is deterministic. The Windows SAPI path can record audio and
    play speech locally, but still needs a real STT provider before Run F can be
    marked completed.
    """

    def __init__(
        self,
        status_callback: Callable[[str], None] | None = None,
        response_callback: Callable[[str, str], None] | None = None,
    ) -> None:
        self.provider = os.environ.get("GOAT_LIVETALK_PROVIDER", "mock").strip().lower() or "mock"
        self.audio_dir = Path(os.environ.get("GOAT_LIVETALK_AUDIO_DIR", Path.home() / "AppData" / "Roaming" / "GoatDesktop"))
        self.state = "idle"
        self.last_result: LiveTalkResult | None = None
        self.status_callback = status_callback
        self.response_callback = response_callback

    def run_once(self) -> LiveTalkResult:
        started = perf_counter()
        if self.provider == "windows_sapi":
            result = self._run_windows_sapi(started)
            self.last_result = result
            self._set_state("idle")
            return result

        if self.provider != "mock":
            raise RuntimeError(f"unsupported LiveTalk provider: {self.provider}")

        self._set_state("listening")
        transcript = "zeig mir das Suchfeld"
        self._set_state("thinking")
        response_text = "Ich zeige das Suchfeld nur nach Freigabe."
        self._set_state("speaking")
        result = LiveTalkResult(
            provider="mock",
            mode="half_duplex",
            transcript=transcript,
            response_text=response_text,
            time_ms=round((perf_counter() - started) * 1000, 2),
            audio_recorded=False,
            audio_played=False,
            stt_provider="mock",
            tts_provider="mock",
            completion_ready=False,
        )
        self.last_result = result
        self._set_state("idle")
        return result

    def _run_windows_sapi(self, started: float) -> LiveTalkResult:
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        audio_path = self.audio_dir / "livetalk-last-recording.wav"
        record_seconds = float(os.environ.get("GOAT_LIVETALK_RECORD_SECONDS", "3.0"))
        prepare_seconds = float(os.environ.get("GOAT_LIVETALK_PREPARE_SECONDS", "0.35"))
        manual_transcript = os.environ.get("GOAT_LIVETALK_MANUAL_TRANSCRIPT", "").strip()

        self._set_state("prepare")
        signal_recording_start(prepare_seconds)
        self._set_state("listening")
        audio_recorded = record_windows_wav(audio_path, record_seconds)
        self._set_state("thinking")
        stt_result = transcribe_audio(audio_path)
        transcript = stt_result.transcript or manual_transcript
        chat_ok = False
        if transcript:
            chat_result = request_chat_response(
                transcript,
                context={
                    "source": "livetalk_audio",
                    "safety_rule": "desktop actions require explicit user approval",
                },
            )
            chat_ok = chat_result.status == "ok"
            response_text = chat_result.response_text
            chat_time_ms = chat_result.time_ms
            self._publish_response(transcript, response_text)
        elif stt_result.status == "uncertain":
            response_text = _stt_uncertain_response(stt_result.error)
            chat_time_ms = 0.0
            self._publish_response(transcript, response_text)
        else:
            response_text = "Audio wurde aufgenommen. STT ist noch nicht konfiguriert."
            chat_time_ms = 0.0
            self._publish_response(transcript, response_text)
        self._set_state("speaking")
        response_audio_path = self.audio_dir / "livetalk-last-response.wav"
        audio_pending = False
        if _auto_tts_enabled():
            tts_result = synthesize_speech(response_text, response_audio_path)
            if tts_result.status == "ok" and tts_result.audio_path:
                audio_played = play_windows_wav(Path(tts_result.audio_path))
                tts_provider = tts_result.provider
                final_response_audio_path = tts_result.audio_path
            else:
                audio_played = False
                tts_provider = tts_result.provider
                final_response_audio_path = None
                if _sapi_fallback_enabled():
                    audio_played = speak_windows_sapi(response_text)
                    tts_provider = "windows_sapi"
            tts_time_ms = float(getattr(tts_result, "time_ms", 0.0) or 0.0)
        else:
            tts_result = None
            audio_played = False
            tts_provider = "not_requested"
            final_response_audio_path = None
            audio_pending = bool(chat_ok and response_text.strip())
            tts_time_ms = 0.0
        return LiveTalkResult(
            provider="windows_sapi",
            mode="half_duplex",
            transcript=transcript,
            response_text=response_text,
            time_ms=round((perf_counter() - started) * 1000, 2),
            audio_recorded=audio_recorded,
            audio_played=audio_played,
            stt_provider=_stt_provider_name(stt_result, bool(manual_transcript)),
            tts_provider=tts_provider,
            stt_time_ms=float(getattr(stt_result, "time_ms", 0.0) or 0.0),
            chat_time_ms=float(chat_time_ms),
            tts_time_ms=tts_time_ms,
            record_seconds=record_seconds,
            audio_path=str(audio_path),
            response_audio_path=final_response_audio_path,
            completion_ready=bool(
                audio_recorded
                and stt_result.status == "ok"
                and chat_ok
                and transcript
                and (_auto_tts_enabled() is False or (tts_result is not None and tts_result.status == "ok" and audio_played))
            ),
            audio_pending=audio_pending,
        )

    def _set_state(self, state: str) -> None:
        self.state = state
        if self.status_callback is not None:
            self.status_callback(state)

    def _publish_response(self, transcript: str, response_text: str) -> None:
        if self.response_callback is not None:
            self.response_callback(transcript, response_text)


def read_response_aloud(text: str, audio_dir: Path | str | None = None) -> ReadAloudResult:
    target_dir = Path(audio_dir or os.environ.get("GOAT_LIVETALK_AUDIO_DIR", Path.home() / "AppData" / "Roaming" / "GoatDesktop"))
    response_audio_path = target_dir / "livetalk-read-aloud.wav"
    tts_result = synthesize_speech(text, response_audio_path)
    if tts_result.status != "ok" or not tts_result.audio_path:
        return ReadAloudResult(
            status="error",
            audio_played=False,
            tts_provider=tts_result.provider,
            tts_time_ms=float(getattr(tts_result, "time_ms", 0.0) or 0.0),
            error=tts_result.error or tts_result.status,
        )
    audio_played = play_windows_wav(Path(tts_result.audio_path))
    return ReadAloudResult(
        status="ok" if audio_played else "error",
        audio_played=audio_played,
        tts_provider=tts_result.provider,
        tts_time_ms=float(getattr(tts_result, "time_ms", 0.0) or 0.0),
        audio_path=tts_result.audio_path,
        error=None if audio_played else "playback failed",
    )


def signal_recording_start(prepare_seconds: float = 0.8) -> None:
    """Give the user a clear cue before microphone recording starts."""
    time.sleep(max(0.0, prepare_seconds))
    winsound.Beep(880, 180)


def _stt_uncertain_response(error: str | None) -> str:
    if error == "empty transcript":
        return "Audio wurde aufgenommen, aber Builder-STT hat keinen Text erkannt."
    if error:
        return f"Audio wurde aufgenommen, aber Builder-STT meldet: {error}."
    return "Audio wurde aufgenommen, aber Builder-STT konnte keinen sicheren Text liefern."


def _stt_provider_name(stt_result, has_manual_transcript: bool) -> str:
    if stt_result.status == "ok":
        return stt_result.provider
    if has_manual_transcript:
        return "manual"
    return stt_result.provider or "none"


def _sapi_fallback_enabled() -> bool:
    value = os.environ.get("GOAT_LIVETALK_ALLOW_SAPI_FALLBACK", "").strip().lower()
    return value in {"1", "true", "yes", "on"}


def _auto_tts_enabled() -> bool:
    value = os.environ.get("GOAT_LIVETALK_AUTO_TTS", "").strip().lower()
    return value in {"1", "true", "yes", "on"}


def record_windows_wav(output_path: Path, seconds: float = 1.0) -> bool:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        output_path.unlink()
    temp_path = Path(tempfile.gettempdir()) / "goatlt.wav"
    if temp_path.exists():
        temp_path.unlink()
    _mci("open new type waveaudio alias goat_livetalk")
    try:
        _mci("record goat_livetalk")
        time.sleep(max(0.1, seconds))
        _mci("stop goat_livetalk")
        _mci(f'save goat_livetalk "{temp_path}"')
    finally:
        _mci("close goat_livetalk", raise_on_error=False)
    if temp_path.exists():
        shutil.copyfile(temp_path, output_path)
    return output_path.exists() and output_path.stat().st_size > 44


def speak_windows_sapi(text: str) -> bool:
    escaped = text.replace("'", "''")
    command = (
        "$voice = New-Object -ComObject SAPI.SpVoice; "
        "$germanVoice = $voice.GetVoices() | "
        "Where-Object { $_.GetDescription() -match 'German|Deutsch|Hedda' } | "
        "Select-Object -First 1; "
        "if ($null -ne $germanVoice) { $voice.Voice = $germanVoice }; "
        f"$null = $voice.Speak('{escaped}', 0)"
    )
    completed = subprocess.run(
        ["powershell", "-NoProfile", "-Command", command],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    return completed.returncode == 0


def play_windows_wav(audio_path: Path) -> bool:
    if not audio_path.exists():
        return False
    playable_path = Path(tempfile.gettempdir()) / "goatplay.wav"
    shutil.copyfile(audio_path, playable_path)
    alias = "goat_tts_playback"
    _mci(f'open "{playable_path}" type waveaudio alias {alias}')
    try:
        _mci(f"play {alias} wait")
    finally:
        _mci(f"close {alias}", raise_on_error=False)
        if playable_path.exists():
            playable_path.unlink()
    return True


def _mci(command: str, raise_on_error: bool = True) -> str:
    error = windll.winmm.mciSendStringW(command, None, 0, None)
    if error == 0:
        return ""
    buffer = create_unicode_buffer(256)
    windll.winmm.mciGetErrorStringW(error, buffer, len(buffer))
    message = buffer.value or f"MCI error {error}"
    if raise_on_error:
        raise RuntimeError(message)
    return message
