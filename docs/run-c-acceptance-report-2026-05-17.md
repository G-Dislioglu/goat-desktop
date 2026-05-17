# Run C Acceptance Report - 2026-05-17

Scope: local-only FastAPI bridge on `127.0.0.1`, active-window/screen-capture endpoints, Coordinate Broker + Local Verifier, and cue dispatch to the yellow ball. No Builder bridge, no Vision provider, no OCR, and no action execution.

## Evidence

- `/healthz`: `{'ok': True, 'service': 'goat-desktop-local-bridge', 'scope': 'local-only', 'host': '127.0.0.1'}`.
- Activated external window: Chrome/Render dashboard.
- `/active-window`: Chrome/Render dashboard, rect `[-14, -14, 3014, 1906]`.
- `/screen-capture`: ok `True`, source `mss`, time_ms `157.93`.
- `/screen-cue` safety_state: `accept`.
- Broker fusion path: `active_window_local_geometry_accept`.
- Broker final bbox: `[1456.0, 902.0, 1544.0, 990.0]`.
- Overlay rect after cue: `(1469, 915, 1531, 977)`.
- Screenshot: `docs/screenshots/run-c-bridge-cue-acceptance-2026-05-17.png`.

## Decision

Accepted as Run C `code_ready`: `/healthz`, `/active-window`, `/screen-capture`, and `/screen-cue` respond locally; the broker returns `accept`; the response includes `safety_state`, `anchors[]`, and `broker_decision`; and the screenshot visibly shows the ball at the cued coordinate. Full Run C `completed` still needs the stricter popup-triggered acceptance path from the master spec.

## Raw Evidence

```json
{
  "healthz": {
    "ok": true,
    "service": "goat-desktop-local-bridge",
    "scope": "local-only",
    "host": "127.0.0.1"
  },
  "activated_title": "Big-Bro \u30fb Web Service \u30fb Render Dashboard - Google Chrome",
  "active_window": {
    "hwnd": 131924,
    "title": "Big-Bro \u30fb Web Service \u30fb Render Dashboard - Google Chrome",
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
  "screen_capture": {
    "ok": true,
    "active_window": {
      "hwnd": 131924,
      "title": "Big-Bro \u30fb Web Service \u30fb Render Dashboard - Google Chrome",
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
      "time_ms": 157.93,
      "saved_to": null
    }
  },
  "screen_cue_payload": {
    "source": "active_window",
    "label": "Run C acceptance cue",
    "bbox": [
      1456,
      902,
      1544,
      990
    ],
    "confidence": 0.92
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
        "label": "Big-Bro \u30fb Web Service \u30fb Render Dashboard - Google Chrome"
      }
    ],
    "broker_decision": {
      "status": "accept",
      "final_bbox": [
        1456.0,
        902.0,
        1544.0,
        990.0
      ],
      "final_confidence": 0.92,
      "reason": "local geometry source passed finite-bounds, foreground-window, and semantic-label checks",
      "fusion_path": "active_window_local_geometry_accept",
      "time_ms": 0.01,
      "candidate": {
        "source": "active_window",
        "bbox": [
          1456.0,
          902.0,
          1544.0,
          990.0
        ],
        "label": "Run C acceptance cue",
        "confidence": 0.92,
        "raw_evidence": {
          "request": {
            "source": "active_window",
            "label": "Run C acceptance cue",
            "bbox": [
              1456,
              902,
              1544,
              990
            ],
            "confidence": 0.92
          },
          "active_window": {
            "hwnd": 131924,
            "title": "Big-Bro \u30fb Web Service \u30fb Render Dashboard - Google Chrome",
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
          "label": "Big-Bro \u30fb Web Service \u30fb Render Dashboard - Google Chrome"
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
  "screenshot": "docs\\screenshots\\run-c-bridge-cue-acceptance-2026-05-17.png"
}
```
