from __future__ import annotations

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
from typing import Any
from urllib.parse import urlparse


class ChatMode(StrEnum):
    DISABLED = "disabled"
    BUILDER_PROXY = "builder_proxy"


@dataclass(frozen=True)
class ChatConfig:
    mode: ChatMode
    builder_url: str | None
    builder_token: str | None
    provider: str
    reasoning_level: str
    timeout_seconds: float


@dataclass(frozen=True)
class ChatResult:
    status: str
    response_text: str
    provider: str
    reasoning_level: str
    confidence: float
    time_ms: float
    raw_evidence: dict[str, Any]
    http_status: int | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_chat_config() -> ChatConfig:
    builder_url = _get_env("GOAT_BUILDER_URL")
    builder_token = _get_env("GOAT_BUILDER_TOKEN")
    mode = _parse_mode(_get_env("GOAT_CHAT_MODE"), _default_chat_mode(builder_url, builder_token))
    timeout = float(_get_env("GOAT_CHAT_TIMEOUT_SECONDS", "12.0") or "12.0")
    return ChatConfig(
        mode=mode,
        builder_url=builder_url,
        builder_token=builder_token,
        provider=_get_env("GOAT_CHAT_PROVIDER", "builder_default") or "builder_default",
        reasoning_level=_get_env("GOAT_CHAT_REASONING", "minimal") or "minimal",
        timeout_seconds=max(0.5, timeout),
    )


def request_chat_response(
    message: str,
    context: dict[str, Any] | None = None,
    config: ChatConfig | None = None,
) -> ChatResult:
    active_config = config or load_chat_config()
    started = time.perf_counter()
    clean_message = message.strip()
    if not clean_message:
        return _uncertain_result("empty message", active_config, started)
    if active_config.mode != ChatMode.BUILDER_PROXY:
        return _uncertain_result("Maya-KI ist noch nicht live angebunden.", active_config, started)
    if not active_config.builder_url or not active_config.builder_token:
        return _uncertain_result("GOAT_BUILDER_URL and GOAT_BUILDER_TOKEN are required", active_config, started)

    body = {
        "message": clean_message,
        "context": context or {},
        "provider": active_config.provider,
        "reasoning_level": active_config.reasoning_level,
    }
    request = urllib.request.Request(
        active_config.builder_url.rstrip("/") + "/api/goat/chat",
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
        if exc.code == 404:
            return _uncertain_result(
                "Maya-KI ist im Builder noch nicht live angebunden (/api/goat/chat fehlt).",
                active_config,
                started,
                http_status=exc.code,
            )
        return _uncertain_result(f"http_{exc.code}", active_config, started, http_status=exc.code)
    except Exception as exc:  # noqa: BLE001 - fail closed into explicit uncertain chat
        return _uncertain_result(type(exc).__name__, active_config, started)

    response_text = str(
        payload.get("response_text")
        or payload.get("text")
        or payload.get("message")
        or payload.get("answer")
        or ""
    ).strip()
    if not response_text:
        return _uncertain_result("empty response", active_config, started, http_status=http_status)

    return ChatResult(
        status="ok",
        response_text=response_text,
        provider=str(payload.get("source") or payload.get("provider") or active_config.provider),
        reasoning_level=str(payload.get("reasoning_level_used") or active_config.reasoning_level),
        confidence=float(payload.get("confidence") or 0.0),
        time_ms=float(payload.get("latency_ms") or round((time.perf_counter() - started) * 1000, 2)),
        http_status=http_status,
        raw_evidence={
            "mode": ChatMode.BUILDER_PROXY.value,
            "provider": active_config.provider,
            "reasoning_level": active_config.reasoning_level,
            "http_status": http_status,
        },
    )


def _parse_mode(value: str | None, default: ChatMode) -> ChatMode:
    if value is None:
        return default
    try:
        return ChatMode(value.strip().lower())
    except ValueError:
        return default


def _default_chat_mode(builder_url: str | None, builder_token: str | None) -> ChatMode:
    if builder_url and builder_token:
        return ChatMode.BUILDER_PROXY
    return ChatMode.DISABLED


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
    config: ChatConfig,
    started: float,
    http_status: int | None = None,
) -> ChatResult:
    return ChatResult(
        status="uncertain",
        response_text=error,
        provider=config.provider,
        reasoning_level=config.reasoning_level,
        confidence=0.0,
        time_ms=round((time.perf_counter() - started) * 1000, 2),
        http_status=http_status,
        error=error,
        raw_evidence={
            "error": error,
            "http_status": http_status,
            "fallback": "uncertain_chat",
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
