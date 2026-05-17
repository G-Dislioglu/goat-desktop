# Run D Completion Report - 2026-05-17

Scope: outbound Builder WebSocket bridge with token auth, reconnect-capable client, Builder test cue preview, explicit user approval, and cue dispatch through the local Coordinate Broker. No Builder-initiated inbound port, no action execution, no Vision/OCR.

## Evidence

- Local test Builder WebSocket accepted an outbound Desktop connection on `127.0.0.1:9876`.
- Token auth checked through `Authorization: Bearer <token>`; token value is not committed.
- Desktop sent `hello` with `user_approval_required` capability.
- Builder sent `test_cue`.
- Popup preview screenshot: `docs/screenshots/run-d-builder-cue-preview-2026-05-17.png`.
- `Cue freigeben` was clicked through the popup approval path.
- Approval response safety_state: `accept`.
- Broker fusion path: `active_window_local_geometry_accept`.
- Overlay rect after approval: `(1469, 915, 1531, 977)`.
- Approved cue screenshot: `docs/screenshots/run-d-builder-cue-approved-2026-05-17.png`.

## Decision

Run D decision: `completed`. Completed requires outbound WebSocket connect, token auth, Builder test cue preview without auto-render, explicit approval, Broker `accept`, and visual confirmation that the ball rendered only after approval.

## Raw Evidence

```json
{
  "activated_title": "soulmatch-vision-worker \u30fb Web Service \u30fb Render Dashboard - Google Chrome",
  "builder_events": [
    {
      "event": "connect",
      "authorization_ok": true
    },
    {
      "event": "hello",
      "message": {
        "type": "hello",
        "client": "goat-desktop",
        "capabilities": [
          "screen_cue_preview",
          "user_approval_required"
        ],
        "ts": 1779004018.540514
      }
    },
    {
      "event": "test_cue_sent"
    }
  ],
  "pending_builder_cue": {
    "source": "active_window",
    "label": "Run D Builder test cue",
    "confidence": 0.9
  },
  "approve_button_was_enabled": true,
  "approval_response": {
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
      "reason": "local geometry source passed finite-bounds, foreground-window, and semantic-label checks",
      "fusion_path": "active_window_local_geometry_accept",
      "time_ms": 0.07,
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
            "label": "Run D Builder test cue",
            "confidence": 0.9
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
  "overlay_rect_after_approval": [
    1469,
    915,
    1531,
    977
  ],
  "preview_screenshot": "docs\\screenshots\\run-d-builder-cue-preview-2026-05-17.png",
  "approved_screenshot": "docs\\screenshots\\run-d-builder-cue-approved-2026-05-17.png"
}
```
