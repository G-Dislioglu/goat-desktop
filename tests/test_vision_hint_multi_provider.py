from __future__ import annotations

import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from goat_desktop.broker import build_candidate, verify_candidate
from goat_desktop.screen import WindowInfo
from goat_desktop.vision_config import load_vision_config, save_vision_config
from goat_desktop.vision_hint import get_vision_hint


class VisionHintHandler(BaseHTTPRequestHandler):
    response_mode = "ok"
    last_request: dict | None = None

    def do_POST(self) -> None:  # noqa: N802 - stdlib hook
        auth = self.headers.get("Authorization")
        raw_body = self.rfile.read(int(self.headers.get("Content-Length", "0")))
        if self.path != "/api/goat/vision-hint":
            self._send_json({}, 404)
            return
        if auth != "Bearer test-token":
            self._send_json({}, 401)
            return
        if self.response_mode == "timeout":
            time.sleep(1.0)
            return
        if self.response_mode == "error":
            self._send_json({}, 500)
            return

        payload = json.loads(raw_body.decode("utf-8"))
        VisionHintHandler.last_request = payload
        if self.response_mode == "alternate_fields":
            body = {
                "source": payload["provider"],
                "label": "StepStack Ordner",
                "rough_position": "oben links",
                "confidence": "0.74",
                "latency_ms": 123,
                "reasoning_level_used": payload["reasoning_level"],
            }
        elif self.response_mode == "not_visible":
            body = {
                "source": payload["provider"],
                "label": "StepStack Ordner",
                "rough_position": "oben links",
                "target_visible": False,
                "confidence": 0.91,
                "latency_ms": 123,
                "reasoning_level_used": payload["reasoning_level"],
            }
        else:
            body = {
                "source": payload["provider"],
                "semantic_label": "primary action button",
                "approximate_position": "center",
                "confidence": 0.82,
                "latency_ms": 123,
                "reasoning_level_used": payload["reasoning_level"],
            }
        self._send_json(body)

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
def image_path(tmp_path: Path) -> Path:
    path = tmp_path / "screen.png"
    path.write_bytes(b"fake-png")
    return path


@pytest.fixture
def mock_server(monkeypatch):
    VisionHintHandler.response_mode = "ok"
    VisionHintHandler.last_request = None
    server = ThreadingHTTPServer(("127.0.0.1", 0), VisionHintHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{server.server_port}"
    monkeypatch.setenv("GOAT_VISION_MODE", "builder_proxy")
    monkeypatch.setenv("GOAT_BUILDER_URL", base_url)
    monkeypatch.setenv("GOAT_BUILDER_TOKEN", "test-token")
    monkeypatch.setenv("GOAT_VISION_TIMEOUT_SECONDS", "0.2")
    yield server
    server.shutdown()
    thread.join(timeout=2)


def test_default_builder_proxy_call(monkeypatch, mock_server, image_path: Path) -> None:
    monkeypatch.delenv("GOAT_VISION_PROVIDER", raising=False)
    monkeypatch.delenv("GOAT_VISION_REASONING", raising=False)
    hint = get_vision_hint(image_path, "find primary button")
    assert hint.status == "ok"
    assert hint.provider == "gemini_flash_lite"
    assert hint.reasoning_level == "minimal"
    assert hint.label == "primary action button"
    assert VisionHintHandler.last_request["provider"] == "gemini_flash_lite"
    assert VisionHintHandler.last_request["reasoning_level"] == "minimal"
    assert "semantic_label" in VisionHintHandler.last_request["prompt"]
    assert "approximate_position" in VisionHintHandler.last_request["prompt"]


def test_grok_low_reasoning(monkeypatch, mock_server, image_path: Path) -> None:
    monkeypatch.setenv("GOAT_VISION_PROVIDER", "grok_4_3")
    monkeypatch.setenv("GOAT_VISION_REASONING", "low")
    hint = get_vision_hint(image_path, "find primary button")
    assert hint.provider == "grok_4_3"
    assert hint.reasoning_level == "low"
    assert hint.to_dict()["source"] == "grok_4_3"


def test_builder_proxy_accepts_alternate_target_fields(monkeypatch, mock_server, image_path: Path) -> None:
    VisionHintHandler.response_mode = "alternate_fields"

    hint = get_vision_hint(image_path, "find StepStack")

    assert hint.status == "ok"
    assert hint.label == "StepStack Ordner"
    assert hint.rough_position == "oben links"
    assert hint.confidence == 0.74


def test_builder_proxy_honors_not_visible_flag(monkeypatch, mock_server, image_path: Path) -> None:
    VisionHintHandler.response_mode = "not_visible"

    hint = get_vision_hint(image_path, "find StepStack")

    assert hint.status == "ok"
    assert hint.label == "StepStack Ordner"
    assert hint.rough_position == "oben links"
    assert hint.confidence == 0.0


def test_http_500_returns_uncertain(monkeypatch, mock_server, image_path: Path) -> None:
    VisionHintHandler.response_mode = "error"
    hint = get_vision_hint(image_path, "find primary button")
    assert hint.status == "uncertain"
    assert hint.http_status in {500, None}
    assert hint.error in {"http_500", "ConnectionAbortedError"}


def test_timeout_returns_uncertain(monkeypatch, mock_server, image_path: Path) -> None:
    VisionHintHandler.response_mode = "timeout"
    hint = get_vision_hint(image_path, "find primary button")
    assert hint.status == "uncertain"
    assert hint.error in {"TimeoutError", "timeout"}


def test_invalid_token_returns_uncertain(monkeypatch, mock_server, image_path: Path) -> None:
    monkeypatch.setenv("GOAT_BUILDER_TOKEN", "bad-token")
    hint = get_vision_hint(image_path, "find primary button")
    assert hint.status == "uncertain"
    assert hint.http_status == 401


def test_vision_config_persists(monkeypatch, tmp_path: Path) -> None:
    config_path = tmp_path / "vision_config.json"
    monkeypatch.setenv("GOAT_VISION_CONFIG_PATH", str(config_path))
    saved = save_vision_config("grok_4_3", "low")
    assert saved == {"provider": "grok_4_3", "reasoning_level": "low"}
    assert json.loads(config_path.read_text(encoding="utf-8")) == saved


def test_vision_config_loads(monkeypatch, tmp_path: Path) -> None:
    config_path = tmp_path / "vision_config.json"
    monkeypatch.setenv("GOAT_VISION_CONFIG_PATH", str(config_path))
    config_path.write_text(json.dumps({"provider": "gemini_flash", "reasoning_level": "high"}), encoding="utf-8")
    assert load_vision_config() == {"provider": "gemini_flash", "reasoning_level": "high"}


def test_vision_only_never_accepts() -> None:
    window = WindowInfo(hwnd=1, title="test", rect=[0, 0, 800, 600], foreground=True)
    candidate = build_candidate(
        {
            "source": "vision",
            "label": "primary button",
            "bbox": [100, 100, 200, 160],
            "confidence": 0.9,
        },
        window,
    )
    decision = verify_candidate(candidate, window)
    assert decision["status"] == "uncertain"
    assert decision["final_bbox"] is None
    assert decision["fusion_path"] == "vision_only_uncertain"
