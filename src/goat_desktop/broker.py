from __future__ import annotations

from dataclasses import asdict, dataclass
from math import isfinite
from time import perf_counter
from typing import Any

from goat_desktop.screen import WindowInfo


LOCAL_GEOMETRY_SOURCES = {"uia", "ocr", "active_window", "test_cue"}


@dataclass(frozen=True)
class Candidate:
    source: str
    bbox: list[float]
    label: str
    confidence: float
    raw_evidence: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_candidate(payload: dict[str, Any], window: WindowInfo) -> Candidate:
    bbox = payload.get("bbox")
    label = str(payload.get("label") or "screen cue")
    source = str(payload.get("source") or "test_cue")
    confidence = float(payload.get("confidence") or 0.9)

    if bbox is None:
        cx, cy = window.center
        bbox = [cx - 36, cy - 36, cx + 36, cy + 36]
        source = "active_window"
        label = "active window center"

    return Candidate(
        source=source,
        bbox=[float(value) for value in bbox],
        label=label,
        confidence=confidence,
        raw_evidence={
            "request": payload,
            "vision_hint": payload.get("vision_hint"),
            "active_window": window.to_dict(),
        },
    )


def verify_candidate(candidate: Candidate, window: WindowInfo) -> dict[str, Any]:
    started = perf_counter()
    reasons: list[str] = []
    left, top, right, bottom = candidate.bbox
    values_finite = all(isfinite(value) for value in candidate.bbox)
    width = right - left
    height = bottom - top
    center_x = (left + right) / 2
    center_y = (top + bottom) / 2

    if not values_finite:
        reasons.append("bbox contains non-finite values")
    if width <= 0 or height <= 0:
        reasons.append("bbox has non-positive size")
    if not window.foreground or window.width <= 0 or window.height <= 0:
        reasons.append("active window is unavailable")
    if not (window.rect[0] <= center_x <= window.rect[2] and window.rect[1] <= center_y <= window.rect[3]):
        reasons.append("bbox center is outside active window")
    if candidate.source not in LOCAL_GEOMETRY_SOURCES:
        reasons.append("source is not an accepted local geometry source")
    if not candidate.label.strip():
        reasons.append("semantic label is empty")
    vision_hint = candidate.raw_evidence.get("vision_hint")
    if candidate.source == "vision":
        reasons.append("vision source alone cannot accept")

    if reasons:
        if candidate.source == "vision":
            status = "uncertain"
            confidence = min(max(candidate.confidence, 0.0), 0.4)
            fusion_path = "vision_only_uncertain"
        else:
            status = "stop"
            confidence = min(candidate.confidence, 0.0)
            fusion_path = "local_verifier_rejected"
    else:
        status = "accept"
        confidence = min(max(candidate.confidence, 0.0), 0.95)
        fusion_path = f"{candidate.source}_local_geometry_accept"
        if vision_hint:
            reasons.append("vision hint recorded as semantic context only; local geometry remains authoritative")
        reasons.append("local geometry source passed finite-bounds, foreground-window, and semantic-label checks")

    elapsed_ms = round((perf_counter() - started) * 1000, 2)
    return {
        "status": status,
        "final_bbox": [round(value, 2) for value in candidate.bbox] if status == "accept" else None,
        "final_confidence": confidence,
        "reason": "; ".join(reasons),
        "fusion_path": fusion_path,
        "time_ms": elapsed_ms,
        "candidate": candidate.to_dict(),
        "anchors": [
            {
                "type": "active_window_rect",
                "source": "win32",
                "bbox": window.rect,
                "label": window.title or "active window",
            }
        ],
    }
