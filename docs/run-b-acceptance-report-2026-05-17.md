# Run B Acceptance Report - 2026-05-17

Scope: global yellow cue ball overlay, popup controls, click-through guardrail, and emergency hotkey. No bridge, UIA, OCR, Vision, or actions.

## Evidence

- Screenshot 1: `docs/screenshots/run-b-acceptance-context-1.png`.
- Screenshot 2: `docs/screenshots/run-b-acceptance-context-2.png`.
- Coordinate change: `(120, 120, 182, 182)` to `(420, 260, 482, 322)`.
- Overlay extended style: `0x000800A8`.
- `WS_EX_TRANSPARENT`: `True`.
- `WS_EX_LAYERED`: `True`.
- Hit-test 1 returned overlay itself: `False`; target title: Chrome/Render window.
- Hit-test 2 returned overlay itself: `False`; target title: Chrome window.
- Emergency hotkey `Ctrl+Alt+Esc` sent via Windows key events.
- Overlay visible after hotkey: `False`.
- Popup visible after hotkey: `False`.

## Visual Check

Both screenshots were visually inspected before commit. They show the yellow cue ball above external Chrome/Render UI in two different positions. No secrets or `.env` contents are visible.

## Decision

Accepted for Run B: the screenshots visibly show the yellow cue ball in both positions, `WS_EX_TRANSPARENT` and `WS_EX_LAYERED` are true, hit-tests do not resolve to the overlay as the blocking target, and `Ctrl+Alt+Esc` hides GOAT windows.

## Raw Evidence

```json
{
  "rect1": [
    120,
    120,
    182,
    182
  ],
  "rect2": [
    420,
    260,
    482,
    322
  ],
  "style_hex": "0x000800A8",
  "ws_ex_transparent": true,
  "ws_ex_layered": true,
  "hit1_overlay": false,
  "hit1_title": "Big-Bro \u30fb Web Service \u30fb Render Dashboard - Google Chrome",
  "hit2_overlay": false,
  "hit2_title": "Chrome Legacy Window",
  "overlay_visible_after_hotkey": false,
  "popup_visible_after_hotkey": false
}
```
