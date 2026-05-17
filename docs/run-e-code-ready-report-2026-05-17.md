# Run E Code-Ready Report - 2026-05-17

Scope: Vision-LLM semantic-hint wiring. This is not a real provider benchmark: no provider API key is configured in the visible environment, so the run uses the deterministic mock provider to verify authority boundaries.

## Evidence

- `/vision-hint` responded with provider `mock` and `authority=semantic_hint_only`.
- `/screen-cue` received the vision hint as semantic context.
- Broker response kept local geometry authoritative via `active_window_local_geometry_accept`.
- Vision-only accept remains impossible by source validation.
- Vision input screenshot: `docs/screenshots/run-e-vision-input.png`.
- Screenshot: `docs/screenshots/run-e-mock-vision-hint-2026-05-17.png`.

## Decision

Run E decision: `code_ready`, not `completed`. The provider adapter and authority boundary are wired, but no real Vision-LLM provider latency, JSON stability, or UI semantic accuracy has been measured yet.

## Raw Evidence

```json
{
  "activated_title": "soulmatch-vision-worker \u30fb Web Service \u30fb Render Dashboard - Google Chrome",
  "vision_hint_response": {
    "ok": true,
    "provider": "mock",
    "hint": {
      "provider": "mock",
      "label": "primary action area",
      "rough_position": "center",
      "confidence": 0.65,
      "time_ms": 0.0,
      "raw_evidence": {
        "prompt": "Identify the primary actionable UI area semantically. Do not return coordinates.",
        "mode": "deterministic mock for Run E wiring only",
        "authority": "semantic_hint_only"
      }
    },
    "capture": {
      "ok": true,
      "active_window": {
        "hwnd": 131924,
        "title": "soulmatch-vision-worker \u30fb Web Service \u30fb Render Dashboard - Google Chrome",
        "rect": [
          -14,
          -14,
          3014,
          1906
        ],
        "foreground": true,
        "width": 3028,
        "height": 1920,
        "center": [
          1500,
          946
        ]
      },
      "capture": {
        "source": "mss",
        "scope": "active_window",
        "width": 3028,
        "height": 1920,
        "time_ms": 987.8,
        "saved_to": "docs/screenshots/run-e-vision-input.png"
      }
    },
    "authority": "semantic_hint_only"
  },
  "screen_cue_response": {
    "safety_state": "accept",
    "anchors": [
      {
        "type": "active_window_rect",
        "source": "win32",
        "bbox": [
          -14,
          -14,
          3014,
          1906
        ],
        "label": "soulmatch-vision-worker \u30fb Web Service \u30fb Render Dashboard - Google Chrome"
      }
    ],
    "broker_decision": {
      "status": "accept",
      "final_bbox": [
        1464.0,
        910.0,
        1536.0,
        982.0
      ],
      "final_confidence": 0.9,
      "reason": "vision hint recorded as semantic context only; local geometry remains authoritative; local geometry source passed finite-bounds, foreground-window, and semantic-label checks",
      "fusion_path": "active_window_local_geometry_accept",
      "time_ms": 0.08,
      "candidate": {
        "source": "active_window",
        "bbox": [
          1464.0,
          910.0,
          1536.0,
          982.0
        ],
        "label": "active window center",
        "confidence": 0.9,
        "raw_evidence": {
          "request": {
            "source": "active_window",
            "label": "Run E local geometry cue with semantic vision hint",
            "vision_hint": {
              "provider": "mock",
              "label": "primary action area",
              "rough_position": "center",
              "confidence": 0.65,
              "time_ms": 0.0,
              "raw_evidence": {
                "prompt": "Identify the primary actionable UI area semantically. Do not return coordinates.",
                "mode": "deterministic mock for Run E wiring only",
                "authority": "semantic_hint_only"
              }
            },
            "confidence": 0.9
          },
          "vision_hint": {
            "provider": "mock",
            "label": "primary action area",
            "rough_position": "center",
            "confidence": 0.65,
            "time_ms": 0.0,
            "raw_evidence": {
              "prompt": "Identify the primary actionable UI area semantically. Do not return coordinates.",
              "mode": "deterministic mock for Run E wiring only",
              "authority": "semantic_hint_only"
            }
          },
          "active_window": {
            "hwnd": 131924,
            "title": "soulmatch-vision-worker \u30fb Web Service \u30fb Render Dashboard - Google Chrome",
            "rect": [
              -14,
              -14,
              3014,
              1906
            ],
            "foreground": true,
            "width": 3028,
            "height": 1920,
            "center": [
              1500,
              946
            ]
          }
        }
      },
      "anchors": [
        {
          "type": "active_window_rect",
          "source": "win32",
          "bbox": [
            -14,
            -14,
            3014,
            1906
          ],
          "label": "soulmatch-vision-worker \u30fb Web Service \u30fb Render Dashboard - Google Chrome"
        }
      ]
    }
  },
  "overlay_rect_after_cue": [
    1469,
    915,
    1531,
    977
  ],
  "screenshot": "docs\\screenshots\\run-e-mock-vision-hint-2026-05-17.png",
  "real_provider_env_present": false
}
```
