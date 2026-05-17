from __future__ import annotations

import base64
import json
import math
import os
import socket
import wave
import winreg
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from pathlib import Path
from time import perf_counter
from urllib.parse import urlparse, urlunparse


DEFAULT_GOAT_VOICE_INSTRUCTIONS = (
    "Du bist Maya, die Sprachassistenz im lokalen Windows-Programm GOAT Desktop. "
    "GOAT Desktop hilft dem User am PC mit Sprache, Textchat, Bildschirmkontext, Zielmarkierung und sicher gegateten Aktionen. "
    "Aktuell kannst du im LiveTalk-Modus Fragen beantworten, erkannte Sprache als Text anzeigen, per Gemini Live sprechen, "
    "den Kontext der GOAT-Desktop-Oberflaeche erklaeren und bei naechsten Schritten helfen. "
    "GOAT Desktop hat ausserdem einen gelben Cue-Ball fuer markierte Ziele, Builder-Proxy-Anbindung, Vision-Hints, "
    "lokale Sicherheitspruefungen und harte Freigaben fuer riskante Aktionen. "
    "Du darfst keine Desktop-Aktion behaupten oder ausfuehren, wenn der User sie nicht explizit freigegeben hat. "
    "Wenn der User nach deinen Faehigkeiten fragt, erklaere konkret deine GOAT-Desktop-Faehigkeiten, nicht nur allgemeine KI-Faehigkeiten. "
    "Antworte kurz, hilfreich und deutsch."
)


@dataclass(frozen=True)
class GeminiLiveConfig:
    builder_url: str | None
    builder_token: str | None
    timeout_seconds: float
    model: str
    voice: str
    instructions: str


@dataclass(frozen=True)
class GeminiLiveResult:
    status: str
    transcript: str
    response_text: str
    audio_path: str | None
    time_ms: float
    raw_evidence: dict
    error: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


def load_gemini_live_config() -> GeminiLiveConfig:
    timeout = float(_get_env("GOAT_VOICE_TIMEOUT_SECONDS", "20.0") or "20.0")
    return GeminiLiveConfig(
        builder_url=_get_env("GOAT_BUILDER_URL"),
        builder_token=_get_env("GOAT_BUILDER_TOKEN"),
        timeout_seconds=max(1.0, timeout),
        model=_get_env("GOAT_VOICE_MODEL", "gemini-3.1-flash-live-preview") or "gemini-3.1-flash-live-preview",
        voice=_get_env("GOAT_VOICE_VOICE", "Kore") or "Kore",
        instructions=_get_env(
            "GOAT_VOICE_INSTRUCTIONS",
            DEFAULT_GOAT_VOICE_INSTRUCTIONS,
        )
        or DEFAULT_GOAT_VOICE_INSTRUCTIONS,
    )


def request_gemini_live_turn(
    audio_path: Path,
    output_path: Path,
    config: GeminiLiveConfig | None = None,
) -> GeminiLiveResult:
    active_config = config or load_gemini_live_config()
    started = perf_counter()
    if not active_config.builder_url or not active_config.builder_token:
        return _uncertain_result("GOAT_BUILDER_URL and GOAT_BUILDER_TOKEN are required", active_config, started)
    if not audio_path.exists() or audio_path.stat().st_size <= 44:
        return _uncertain_result("audio file is empty", active_config, started)
    input_signal = wav_signal_stats(audio_path)
    if _is_low_input_signal(input_signal):
        return GeminiLiveResult(
            status="uncertain",
            transcript="",
            response_text="Keine Sprache erkannt. Bitte nach dem Ton sprechen.",
            audio_path=None,
            time_ms=round((perf_counter() - started) * 1000, 2),
            error="low_input_signal",
            raw_evidence={
                "mode": "gemini_live",
                "model": active_config.model,
                "voice": active_config.voice,
                "input_signal": input_signal,
            },
        )

    uri = build_goat_voice_ws_url(active_config.builder_url)
    headers = {"Authorization": f"Bearer {active_config.builder_token}"}
    output_audio_chunks: list[bytes] = []
    transcript_parts: list[str] = []
    response_text_parts: list[str] = []
    message_count = 0

    try:
        import websockets.sync.client

        with _temporary_resolve_override(active_config.builder_url):
            with websockets.sync.client.connect(
                uri,
                additional_headers=headers,
                open_timeout=min(8.0, active_config.timeout_seconds),
                close_timeout=2.0,
            ) as websocket:
                websocket.send(
                    json.dumps(
                        {
                            "type": "session.update",
                            "session": {
                                "model": active_config.model,
                                "voice": active_config.voice,
                                "instructions": active_config.instructions,
                            },
                        }
                    )
                )
                for chunk in iter_wav_pcm_chunks(audio_path):
                    websocket.send(chunk)
                websocket.send(json.dumps({"type": "audio.end"}))

                while (perf_counter() - started) < active_config.timeout_seconds:
                    try:
                        raw_message = websocket.recv(timeout=0.75)
                    except TimeoutError:
                        if response_text_parts or _has_playable_audio(output_audio_chunks):
                            break
                        continue
                    message_count += 1
                    if isinstance(raw_message, bytes):
                        parsed_bytes = _parse_json_bytes(raw_message)
                        if parsed_bytes is None:
                            output_audio_chunks.append(raw_message)
                            continue
                        parsed = parsed_bytes
                    else:
                        parsed = _parse_json_object(raw_message)
                        if parsed is None:
                            continue
                    input_text = _nested_text(parsed, ["serverContent", "inputTranscription", "text"])
                    output_text = _nested_text(parsed, ["serverContent", "outputTranscription", "text"])
                    if input_text:
                        transcript_parts.append(input_text)
                    if output_text:
                        response_text_parts.append(output_text)
                    for audio_bytes in _extract_inline_audio(parsed):
                        output_audio_chunks.append(audio_bytes)
                    if _nested_bool(parsed, ["serverContent", "turnComplete"]):
                        break
    except Exception as exc:  # noqa: BLE001 - fail closed into explicit Live result
        return _uncertain_result(type(exc).__name__, active_config, started)

    final_audio_path: str | None = None
    if _has_playable_audio(output_audio_chunks):
        output_path.parent.mkdir(parents=True, exist_ok=True)
        write_pcm_wav(output_path, b"".join(output_audio_chunks))
        final_audio_path = str(output_path)

    return GeminiLiveResult(
        status="ok" if final_audio_path or response_text_parts else "uncertain",
        transcript=" ".join(part.strip() for part in transcript_parts if part.strip()).strip(),
        response_text=" ".join(part.strip() for part in response_text_parts if part.strip()).strip()
        or ("Gemini Live hat Audio geliefert." if final_audio_path else "Gemini Live hat keine Antwort geliefert."),
        audio_path=final_audio_path,
        time_ms=round((perf_counter() - started) * 1000, 2),
        error=None if final_audio_path or response_text_parts else "empty live response",
        raw_evidence={
            "mode": "gemini_live",
            "model": active_config.model,
            "voice": active_config.voice,
            "messages": message_count,
            "audio_chunks": len(output_audio_chunks),
            "input_signal": input_signal,
        },
    )


def build_goat_voice_ws_url(builder_url: str) -> str:
    parsed = urlparse(builder_url.rstrip("/"))
    scheme = "wss" if parsed.scheme == "https" else "ws"
    return urlunparse((scheme, parsed.netloc, "/api/goat/voice", "", "", ""))


def iter_wav_pcm_chunks(audio_path: Path, chunk_frames: int = 2048):
    pcm_data = read_wav_as_16khz_pcm(audio_path)
    chunk_size = chunk_frames * 2
    for offset in range(0, len(pcm_data), chunk_size):
        yield pcm_data[offset : offset + chunk_size]


def read_wav_as_16khz_pcm(audio_path: Path) -> bytes:
    with wave.open(str(audio_path), "rb") as wav:
        channels = wav.getnchannels()
        sample_width = wav.getsampwidth()
        sample_rate = wav.getframerate()
        frames = wav.readframes(wav.getnframes())

    mono_samples = _decode_wav_samples(frames, channels, sample_width)
    if sample_rate != 16000:
        mono_samples = _resample_samples(mono_samples, sample_rate, 16000)
    return _encode_s16le(mono_samples)


def wav_signal_stats(audio_path: Path) -> dict[str, float]:
    pcm = read_wav_as_16khz_pcm(audio_path)
    samples = [int.from_bytes(pcm[offset : offset + 2], "little", signed=True) for offset in range(0, len(pcm), 2)]
    if not samples:
        return {"duration_s": 0.0, "rms": 0.0, "peak": 0.0, "loud_ratio": 0.0}
    rms = math.sqrt(sum(sample * sample for sample in samples) / len(samples))
    peak = max(abs(sample) for sample in samples)
    loud_ratio = sum(1 for sample in samples if abs(sample) > 700) / len(samples)
    return {
        "duration_s": round(len(samples) / 16000, 3),
        "rms": round(rms, 2),
        "peak": float(peak),
        "loud_ratio": round(loud_ratio, 5),
    }


def write_pcm_wav(output_path: Path, pcm_data: bytes, sample_rate: int | None = None) -> None:
    rate = int(_get_env("GOAT_VOICE_OUTPUT_SAMPLE_RATE", str(sample_rate or 24000)) or str(sample_rate or 24000))
    with wave.open(str(output_path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(rate)
        wav.writeframes(pcm_data)


def _parse_json_object(raw: str) -> dict | None:
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _parse_json_bytes(raw: bytes) -> dict | None:
    if not raw.lstrip().startswith((b"{", b"[")):
        return None
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return None
    return _parse_json_object(text)


def _has_playable_audio(chunks: list[bytes]) -> bool:
    return sum(len(chunk) for chunk in chunks) >= 1600


def _is_low_input_signal(stats: dict[str, float]) -> bool:
    min_rms = float(_get_env("GOAT_VOICE_MIN_RMS", "220") or "220")
    min_loud_ratio = float(_get_env("GOAT_VOICE_MIN_LOUD_RATIO", "0.02") or "0.02")
    return stats.get("duration_s", 0.0) > 0.0 and stats.get("rms", 0.0) < min_rms and stats.get("loud_ratio", 0.0) < min_loud_ratio


def _decode_wav_samples(frames: bytes, channels: int, sample_width: int) -> list[int]:
    if channels <= 0 or sample_width <= 0:
        return []
    frame_width = channels * sample_width
    samples: list[int] = []
    for offset in range(0, len(frames) - frame_width + 1, frame_width):
        total = 0
        for channel in range(channels):
            start = offset + channel * sample_width
            raw = frames[start : start + sample_width]
            if sample_width == 1:
                value = (raw[0] - 128) << 8
            else:
                value = int.from_bytes(raw, "little", signed=True)
                if sample_width > 2:
                    value >>= 8 * (sample_width - 2)
            total += value
        samples.append(int(total / channels))
    return samples


def _resample_samples(samples: list[int], source_rate: int, target_rate: int) -> list[int]:
    if not samples or source_rate <= 0 or source_rate == target_rate:
        return samples
    target_count = max(1, round(len(samples) * target_rate / source_rate))
    if target_count == 1:
        return [samples[0]]
    scale = (len(samples) - 1) / (target_count - 1)
    output: list[int] = []
    for index in range(target_count):
        source_pos = index * scale
        left = int(source_pos)
        right = min(left + 1, len(samples) - 1)
        fraction = source_pos - left
        output.append(round(samples[left] * (1.0 - fraction) + samples[right] * fraction))
    return output


def _encode_s16le(samples: list[int]) -> bytes:
    output = bytearray()
    for sample in samples:
        clamped = max(-32768, min(32767, int(sample)))
        output.extend(clamped.to_bytes(2, "little", signed=True))
    return bytes(output)


def _nested_text(root: dict, path: list[str]) -> str:
    value = root
    for key in path:
        if not isinstance(value, dict):
            return ""
        value = value.get(key)
    return value.strip() if isinstance(value, str) else ""


def _nested_bool(root: dict, path: list[str]) -> bool:
    value = root
    for key in path:
        if not isinstance(value, dict):
            return False
        value = value.get(key)
    return bool(value)


def _extract_inline_audio(root: dict) -> list[bytes]:
    chunks: list[bytes] = []

    def visit(value) -> None:
        if isinstance(value, dict):
            inline = value.get("inlineData")
            if isinstance(inline, dict):
                data = inline.get("data")
                mime_type = str(inline.get("mimeType") or "")
                if isinstance(data, str) and mime_type.startswith("audio/"):
                    try:
                        chunks.append(base64.b64decode(data))
                    except Exception:
                        pass
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(root)
    return chunks


def _get_env(name: str, default: str | None = None) -> str | None:
    value = os.environ.get(name)
    if value:
        return value
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as key:
            value, _value_type = winreg.QueryValueEx(key, name)
    except OSError:
        return default
    return str(value) if value else default


def _uncertain_result(
    error: str,
    config: GeminiLiveConfig,
    started: float,
    http_status: int | None = None,
) -> GeminiLiveResult:
    return GeminiLiveResult(
        status="uncertain",
        transcript="",
        response_text=error,
        audio_path=None,
        time_ms=round((perf_counter() - started) * 1000, 2),
        error=error,
        raw_evidence={
            "error": error,
            "http_status": http_status,
            "mode": "gemini_live",
            "model": config.model,
        },
    )


@contextmanager
def _temporary_resolve_override(url: str | None):
    override_ip = _get_env("GOAT_BUILDER_RESOLVE_IP")
    if not url or not override_ip:
        yield
        return

    hostname = urlparse(url).hostname
    if not hostname or hostname in {"127.0.0.1", "localhost", "::1"}:
        yield
        return

    original_getaddrinfo = socket.getaddrinfo

    def patched_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
        if host == hostname:
            return original_getaddrinfo(override_ip, port, family, type, proto, flags)
        return original_getaddrinfo(host, port, family, type, proto, flags)

    socket.getaddrinfo = patched_getaddrinfo
    try:
        yield
    finally:
        socket.getaddrinfo = original_getaddrinfo
