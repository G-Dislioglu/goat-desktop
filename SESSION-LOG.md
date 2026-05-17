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
