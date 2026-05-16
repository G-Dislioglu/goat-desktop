# GOAT Desktop

GOAT Desktop is the local Windows desktop companion for Soulmatch/Maya. The desktop app owns the local boundary: tray UI, popup, overlay, screen sensing, LiveTalk, action gating, and the CNC Anchor Protocol. Builder remains the remote orchestrator; it proposes plans, but Desktop verifies local state and enforces approvals.

Canonical spec: [docs/GOAT-DESKTOP-VISION.md](docs/GOAT-DESKTOP-VISION.md)

## Stack Direction

- Python 3.11
- PyQt6 for tray, popup, and overlay
- FastAPI on `127.0.0.1` for the local bridge
- `websockets` for outbound Builder connection
- UFO2 as Windows automation foundation, subject to Run 0b spike verification
- PyInstaller for later Windows packaging

No application code belongs in this initial commit. The first implementation step is Run 0b, because the UFO2 library-vs-agent-loop assumption must be tested before product code depends on it.
