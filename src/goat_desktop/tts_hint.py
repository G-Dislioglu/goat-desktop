from __future__ import annotations

import base64
import json
import os
import socket
import time
import urllib.error
import urllib.request
import winreg
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


class TtsMode(StrEnum):
    DISABLED = "disabled"
    BUILDER_PROXY = "builder_proxy"


@dataclass(frozen=True)
class TtsConfig:
    mode: TtsMode
    builder_url: str | None
    builder_token: str | None
    provider: str
    voice: str
    language: str
    timeout_seconds: float


@dataclass(frozen=True)
class TtsResult:
    status: str
    audio_path: str | None
    provider: str
    voice: str
    language: str
    time_ms: float
    raw_evidence: dict[str, Any]
    mime_type: str = "audio/wav"
    http_status: int | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_tts_config() -> TtsConfig:
    builder_url = _get_env("GOAT_BUILDER_URL")
    builder_token = _get_env("GOAT_BUILDER_TOKEN")
    mode = _parse_mode(_get_env("GOAT_TTS_MODE"), _default_tts_mode(builder_url, builder_token))
    timeout = float(_get_env("GOAT_TTS_TIMEOUT_SECONDS", "8.0") or "8.0")
    return TtsConfig(
        mode=mode,
        builder_url=builder_url,
        builder_token=builder_token,
        provider=_get_env("GOAT_TTS_PROVIDER", "builder_default") or "builder_default",
        voice=_get_env("GOAT_TTS_VOICE", "maya_de") or "maya_de",
        language=_get_env("GOAT_TTS_LANGUAGE", "de-DE") or "de-DE",
        timeout_seconds=max(1.0, timeout),
    )


def synthesize_speech(
    text: str,
    output_path: Path,
    config: TtsConfig | None = None,
) -> TtsResult:
    active_config = config or load_tts_config()
    started = time.perf_counter()
    if active_config.mode != TtsMode.BUILDER_PROXY:
        return _uncertain_result("TTS mode disabled", active_config, started)
    if not active_config.builder_url or not active_config.builder_token:
        return _uncertain_result("GOAT_BUILDER_URL and GOAT_BUILDER_TOKEN are required", active_config, started)
    if not text.strip():
        return _uncertain_result("text is empty", active_config, started)

    body = {
        "text": text,
        "provider": active_config.provider,
        "voice": active_config.voice,
        "language": active_config.language,
        "format": "wav",
        "pronunciation_hints": {
            "GOAT": "Goat",
            "Maya": "Maya",
        },
    }
    request = urllib.request.Request(
        active_config.builder_url.rstrip("/") + "/api/goat/tts",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {active_config.builder_token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with _temporary_resolve_override(active_config.builder_url):
            response_context = urllib.request.urlopen(request, timeout=active_config.timeout_seconds)
        with response_context as response:
            payload = json.loads(response.read().decode("utf-8"))
            http_status = int(response.status)
    except urllib.error.HTTPError as exc:
        return _uncertain_result(f"http_{exc.code}", active_config, started, http_status=exc.code)
    except Exception as exc:  # noqa: BLE001 - fail closed into uncertain TTS
        return _uncertain_result(type(exc).__name__, active_config, started)

    encoded_audio = str(payload.get("audio_base64") or "")
    if not encoded_audio:
        return _uncertain_result("empty audio", active_config, started, http_status=http_status)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(base64.b64decode(encoded_audio))
    if output_path.stat().st_size <= 44:
        return _uncertain_result("audio too small", active_config, started, http_status=http_status)

    return TtsResult(
        status="ok",
        audio_path=str(output_path),
        provider=str(payload.get("source") or active_config.provider),
        voice=str(payload.get("voice_used") or active_config.voice),
        language=str(payload.get("language_used") or active_config.language),
        mime_type=str(payload.get("mime_type") or "audio/wav"),
        time_ms=float(payload.get("latency_ms") or round((time.perf_counter() - started) * 1000, 2)),
        http_status=http_status,
        raw_evidence={
            "mode": TtsMode.BUILDER_PROXY.value,
            "provider": active_config.provider,
            "voice": active_config.voice,
            "language": active_config.language,
            "http_status": http_status,
            "audio_bytes": output_path.stat().st_size,
        },
    )


def _parse_mode(value: str | None, default: TtsMode) -> TtsMode:
    if value is None:
        return default
    try:
        return TtsMode(value.strip().lower())
    except ValueError:
        return default


def _default_tts_mode(builder_url: str | None, builder_token: str | None) -> TtsMode:
    if builder_url and builder_token:
        return TtsMode.BUILDER_PROXY
    return TtsMode.DISABLED


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
    config: TtsConfig,
    started: float,
    http_status: int | None = None,
) -> TtsResult:
    return TtsResult(
        status="uncertain",
        audio_path=None,
        provider=config.provider,
        voice=config.voice,
        language=config.language,
        time_ms=round((time.perf_counter() - started) * 1000, 2),
        http_status=http_status,
        error=error,
        raw_evidence={
            "error": error,
            "http_status": http_status,
            "fallback": "uncertain_tts",
        },
    )


@contextmanager
def _temporary_resolve_override(url: str | None):
    override_ip = _get_env("GOAT_BUILDER_RESOLVE_IP")
    if not url or not override_ip:
        yield
        return

    hostname = urlparse(url).hostname
    if not hostname:
        yield
        return
    if hostname in {"127.0.0.1", "localhost", "::1"}:
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
