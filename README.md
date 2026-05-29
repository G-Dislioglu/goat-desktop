# GOAT Desktop

GOAT Desktop is the local Windows desktop companion for Soulmatch/Maya. The desktop app owns the local boundary: tray UI, popup, overlay, screen sensing, LiveTalk, action gating, and the CNC Anchor Protocol. Builder remains the remote orchestrator; it proposes plans, but Desktop verifies local state and enforces approvals.

Canonical spec: [docs/GOAT-DESKTOP-VISION.md](docs/GOAT-DESKTOP-VISION.md)

## Stack Direction

- Python 3.12 or newer
- PyQt6 for tray, popup, and overlay
- FastAPI on `127.0.0.1` for the local bridge
- `websockets` for outbound Builder connection
- Slim Windows stack: `mss`, `pywinauto`, local coordinate verification, and narrow Win32 executors
- PyInstaller for later Windows packaging

UFO2 is not the application foundation. Run 0b rejected the UFO2 agent/library path for this repo because of dependency pins and latency. Current work must advance the visible product path instead of revisiting that decision.

## Product Progress Gate

GOAT Desktop work must produce at least one of these outcomes:

- a visible user-facing capability that can be exercised locally
- a live acceptance artifact proving Builder -> Desktop -> popup behavior
- a packaging/startup improvement that makes the product easier to run
- a narrowly scoped safety fix tied to a concrete bug or failing test

Copy, redaction, wording, or governance-only changes are allowed only when tied to a named bug, contract, or recovery task. They must not replace the next live product proof.

## Local Start

From a checkout on Windows:

```powershell
.\scripts\start-goat-desktop.ps1
```

To verify the startup path without opening the GUI:

```powershell
.\scripts\start-goat-desktop.ps1 -Check
```

When installed as a Python package, GOAT also exposes:

```powershell
goat-desktop
```

## Local Builder Cue Proposal

`POST /builder-cue` is a local-only proposal path for Builder-style cues. It does not execute desktop actions and does not move the mouse or type text.

Required payload fields:
- `source`: accepted local geometry source such as `uia`, `ocr`, `active_window`, or `test_cue`
- `action_type`: intended action, for example `hover`, `scroll`, or `type`
- `label`: user-visible target name
- `bbox`: four numeric screen coordinates `[left, top, right, bottom]`

The endpoint verifies the proposed geometry against the active local window. Only accepted proposals are shown in the GOAT popup. Execution still requires the user-facing popup flow: first `Pruefen`, then `Ausfuehren`. Rejected or incomplete proposals return `popupProposalEmitted=false` and keep all action effects false.
