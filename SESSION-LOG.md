# SESSION LOG

## 2026-05-16

- Initialized documentation-only `goat-desktop` repository.
- Added canonical GOAT Desktop Vision v1.0 spec.
- Added AICOS reference list.
- No application code added.

## 2026-05-17

- Upgraded canonical GOAT Desktop Vision spec to v1.1 after Run 0c evidence.
- Added Run A native PyQt6 tray shell with movable mini-popup.
- Kept Run A scope limited: no overlay, bridge, UIA, OCR, Vision, LiveTalk implementation, or actions.
- Visual acceptance screenshot is pending; an attempted desktop screenshot was discarded because a sensitive `.env` Notepad window was visible in the background.
- Run A accepted after a clean cropped screenshot was captured and checked: `docs/screenshots/run-a-acceptance-2026-05-17.png`.
- Started Run B after reading `err-dev-002`.
- Rejected the first fullscreen-overlay approach because it rendered as a black blocking surface.
- Added a smaller click-through topmost cue-window with yellow ball, popup movement controls, and global Ctrl+Alt+Esc emergency hotkey.
- Left Run B at `code_ready`; final screencast/manual click-through acceptance is still pending.
- Replaced an invalid Run B acceptance screenshot pair that missed the ball because the crop did not include the overlay rect.
- Accepted Run B after regenerated screenshots showed the yellow cue ball in two positions over external Chrome/Render UI and runtime evidence confirmed click-through styles, non-overlay hit-test targets, and Ctrl+Alt+Esc hiding GOAT windows.
- Started Run C after reading sol-cross-062 and sol-cross-063.
- Added local-only FastAPI bridge endpoints for health, active-window, screen-capture, and screen-cue.
- Added a minimal Coordinate Broker + Local Verifier and wired accepted cue coordinates to the yellow ball through a Qt signal.
- Verified Run C code-ready via local HTTP calls and a screenshot showing the ball at the cued coordinate; full Run C completion remains pending until the popup-triggered acceptance path is captured.
- Added a `Cue testen` popup button that hides the popup, calls local `/screen-cue`, stores the bridge response, and lets the accepted cue dispatch move the ball.
- Completed Run C after the popup-triggered path produced Broker `accept`, `anchors[]`, `broker_decision`, and a visual after-screenshot with the ball at the cue coordinate.
