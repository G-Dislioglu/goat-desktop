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

## Local Builder Cue Proposal

`POST /builder-cue` is a local-only proposal path for Builder-style cues. It does not execute desktop actions and does not move the mouse or type text.

Required payload fields:
- `source`: accepted local geometry source such as `uia`, `ocr`, `active_window`, or `test_cue`
- `action_type`: intended action, for example `hover`, `scroll`, or `type`
- `label`: user-visible target name
- `bbox`: four numeric screen coordinates `[left, top, right, bottom]`

The endpoint verifies the proposed geometry against the active local window. Only accepted proposals are shown in the GOAT popup. Execution still requires the user-facing popup flow: first `Pruefen`, then `Ausfuehren`. Rejected or incomplete proposals return `popupProposalEmitted=false` and keep all action effects false.
