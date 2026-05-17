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
- Started Run D after reading sol-cross-032 and sol-cross-044.
- Added an outbound-only Builder WebSocket client with token header, hello capabilities, timeouts, and reconnect loop.
- Added popup approval controls for Builder cues; incoming Builder test cues can only become rendered cues after `Cue freigeben`.
- Completed Run D against a local test Builder WebSocket: Desktop connected outbound, sent hello, received test cue, showed preview, required approval, then rendered the ball through the local Broker path.
- Started Run E as provider wiring because no real Vision provider key is visible in the environment.
- Added a Vision Hint adapter with disabled, mock, and OpenAI-compatible modes.
- Added `/vision-hint` and Broker logging for semantic hints, while preserving the rule that Vision-only can never produce `accept`.
- Left Run E at `code_ready`; real provider latency, JSON stability, and UI-semantic accuracy still need measurement before any default provider is named.
- Started Run F as a Half-Duplex LiveTalk shell because no real STT/TTS provider is configured.
- Added a deterministic mock LiveTalk session and enabled the popup `LiveTalk` button.
- Verified Run F code-ready with a screenshot showing the mock transcript and Maya response; no audio was recorded or played.
- Left Run F at `code_ready`; real microphone/STT/TTS verification is still required before completion.
- Extended Run E with multi-provider Builder-proxy support for gemini_flash_lite, grok_4_3, and gemini_flash.
- Added persisted Vision UI selection with provider and reasoning dropdowns in the popup.
- Added `vision_config.py` for `%APPDATA%/GoatDesktop/vision_config.json` persistence.
- Added tests for Builder-proxy success, Grok reasoning, HTTP 500, timeout, invalid token, config persistence/load, and Vision-only `uncertain`.
- Kept Run E not completed; real Builder endpoint acceptance is still pending.
- Completed Run E after the Soulmatch Builder endpoint went live and local User env exposed the Builder token.
- Verified real Builder-proxy responses for gemini_flash_lite, gemini_flash, and grok_4_3 on the Run E desktop screenshot; all returned semantic hints only with HTTP 200.
- Added optional GOAT_BUILDER_RESOLVE_IP support because this local Codex process had DNS resolution trouble for the Render hostname while explicit Cloudflare resolution worked.
