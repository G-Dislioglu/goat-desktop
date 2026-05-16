# Run 0b - UFO2 Library Spike Report

Date: 2026-05-16
Repo tested: `microsoft/UFO`
Clone HEAD: `e6195cb Merge commit from fork`
Sandbox path used: `C:/Users/guerc/Documents/Codex/2026-05-16/files-mentioned-by-the-user-files/ufo2-spike-work`

## Summary

UFO2 is not cleanly usable as a drop-in Python library in this environment yet. The low-level UI modules are importable and usable directly after targeted dependency installation, but the full `requirements.txt` install fails on the available Python versions because this machine has Python 3.14, 3.13, and 3.12, while UFO declares Python 3.10/3.11 in its README badges and pins old packages.

Practical recommendation: use Weg B only after a Python 3.11 sandbox is available and after wrapping the low-level modules behind our own narrow adapter. Do not import UFO's full agent/session loop into GOAT Desktop. The direct UIA/screenshot path is promising; the full UFO runtime is too coupled to config, MCP/AIP, LLM, and app-specific dependencies for immediate clean library use.

## A. Library Usability

Partial yes:

- `ufo.automator.ui_control.screenshot` imported successfully.
- `ControlPhotographer` and `DesktopPhotographer` are directly exported.
- `ControlPhotographer(win).capture(...)` was used in the measured path.
- `ufo.automator.ui_control.controller` imported successfully after installing additional dependencies; `ControlReceiver`, `ClickInputCommand`, and `SetEditTextCommand` are exported.

Not clean:

- `ufo.module.basic` did not import under the minimal spike environment. It cascaded through agent/session/AIP/MCP dependencies and stopped at missing `fastapi` after several dependency additions.
- Full install from `requirements.txt` failed before completion.
- The repo must be on `sys.path`, and `cwd` must be the UFO repo root so `config/ufo/*.yaml` can be found.

## B. Startup Requirements

Observed requirements:

- Python 3.10/3.11 should be used. Python 3.14 failed on `faiss-cpu==1.8.0`. Python 3.12 got further but failed on `pandas==1.4.3`.
- UFO repo root must be the working directory for config auto-discovery.
- Config files are expected under `config/ufo/`; they exist in the cloned repo.
- UI/screenshot modules require at least `pywinauto`, `pywin32`, `Pillow`, `pyautogui`, `uiautomation`, `comtypes`, `PyYAML`, `psutil`, and `colorama`.
- Controller import additionally pulled app API dependencies such as `pandas` and `html2text`.
- Session/agent import pulls LLM/MCP/AIP dependencies such as `openai`, `fastmcp`, `websockets`, and `fastapi`.
- No API key was used. The measured UIA/screenshot path does not need a provider key.

## C. Runtime Measurement

Measured operation: active window lookup via UIA, window rect, first 40 descendants, screenshot of active window via UFO `ControlPhotographer`.

Active window: `Codex`
Class: `Chrome_WidgetWin_1`
Rect: `{ left: 384, top: 468, right: 2781, bottom: 1866, width: 2397, height: 1398 }`

Final measured run:

- Run 1: `2905.19 ms`
- Run 2: `2363.47 ms`
- Run 3: `1546.14 ms`
- Mean: `2271.6 ms`

Earlier successful runs varied between roughly `2.05s` and `3.28s`. This is below the v1.0 hard abort threshold of `> 3s` only sometimes; we need a Python 3.11 rerun and a smaller element traversal before treating this as production-grade.

## D. Element List Sample

```json
[
  {
    "name": "",
    "control_type": "Pane",
    "automation_id": "",
    "class_name": "Intermediate D3D Window",
    "rect": { "left": 384, "top": 468, "right": 2781, "bottom": 1866, "width": 2397, "height": 1398 }
  },
  {
    "name": "Codex",
    "control_type": "Pane",
    "automation_id": "",
    "class_name": "RootView",
    "rect": { "left": 385, "top": 468, "right": 2785, "bottom": 1868, "width": 2400, "height": 1400 }
  },
  {
    "name": "Minimize",
    "control_type": "Button",
    "automation_id": "",
    "class_name": "WinCaptionButton",
    "rect": { "left": 2473, "top": 470, "right": 2575, "bottom": 549, "width": 102, "height": 79 }
  },
  {
    "name": "Maximize",
    "control_type": "Button",
    "automation_id": "",
    "class_name": "WinCaptionButton",
    "rect": { "left": 2574, "top": 470, "right": 2678, "bottom": 549, "width": 104, "height": 79 }
  },
  {
    "name": "Close",
    "control_type": "Button",
    "automation_id": "",
    "class_name": "WinCaptionButton",
    "rect": { "left": 2678, "top": 470, "right": 2782, "bottom": 549, "width": 104, "height": 79 }
  }
]
```

## E. Dependencies And Licenses

Repo license: MIT (`LICENSE` in UFO repo).

Pinned requirements include:

- `pywinauto==0.6.8`
- `pywin32>=310`
- `Pillow==11.3.0`
- `pyautogui==0.9.54`
- `uiautomation==2.0.18`
- `comtypes==1.2.0`
- `PyYAML==6.0.1`
- `pandas==1.4.3`
- `faiss-cpu==1.8.0`
- `openai==1.66.2`
- `fastmcp==2.11.3`
- `fastapi==0.116.1`
- `websockets==12.0`

Spike-installed packages diverged from pins where Python 3.12 made old pins impractical: notably `pandas` resolved to `3.0.3`, and `numpy` to `2.4.5`. This is acceptable for a spike but not acceptable as product dependency state.

## F. Risks And Signals

- Python version mismatch is the biggest blocker. No Python 3.10/3.11 runtime was available via `py -0p`.
- Full `requirements.txt` install failed:
  - Python 3.14: no `faiss-cpu==1.8.0` wheel.
  - Python 3.12: `pandas==1.4.3` failed during build requirements.
- UFO config discovery is cwd-sensitive. Importing from outside the repo root fails with "No configuration found for 'ufo'".
- `ufo.automator.ui_control.controller` is not isolated to UI control only; import cascades into Excel/Web app API modules.
- `ufo.module.basic` is agent/session-layer coupled and not a narrow desktop automation API.
- `fastmcp` emitted an Authlib deprecation warning; no Defender warning appeared.
- Runtime is borderline: 1.5-4.1s observed depending on run.

## G. Recommendation

Do not take Weg A. Do not bring UFO's full agent loop into GOAT Desktop.

Use a revised Weg B:

1. Install Python 3.11 before Run A/C dependency work.
2. Treat UFO as source-level/library reference for low-level Windows mechanisms, not as a clean packaged dependency yet.
3. Wrap only narrow modules such as `ufo.automator.ui_control.screenshot.ControlPhotographer` and selected controller primitives behind GOAT's own adapter boundary.
4. Keep Maya/Builder as the only planning/personality layer.
5. Rerun this spike on Python 3.11 before committing any UFO dependency to `goat-desktop`.

Current decision: UFO low-level reuse is promising but not confirmed clean enough for product integration. GOAT Desktop should not advance to action-layer assumptions until a Python 3.11 rerun confirms installability and import stability.

## Embedded spike.py

```python
import importlib
import json
import os
import sys
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent
UFO_ROOT = ROOT / "UFO"
sys.path.insert(0, str(UFO_ROOT))
os.chdir(UFO_ROOT)

RESULTS = {
    "python": sys.version,
    "ufo_root": str(UFO_ROOT),
    "imports": {},
    "measurements_ms": [],
    "active_window": None,
    "elements_sample": [],
    "screenshot_path": None,
}


def try_import(module_name, names=None):
    try:
        module = importlib.import_module(module_name)
        exported = {}
        for name in names or []:
            exported[name] = hasattr(module, name)
        RESULTS["imports"][module_name] = {
            "ok": True,
            "file": getattr(module, "__file__", None),
            "exports": exported,
        }
        return module
    except Exception as exc:
        RESULTS["imports"][module_name] = {
            "ok": False,
            "error": repr(exc),
            "traceback_tail": traceback.format_exc().splitlines()[-6:],
        }
        return None


basic = try_import("ufo.module.basic", ["BaseSession", "BaseRound"])
controller = try_import(
    "ufo.automator.ui_control.controller",
    ["ControlReceiver", "ClickInputCommand", "SetEditTextCommand"],
)
screenshot_mod = try_import(
    "ufo.automator.ui_control.screenshot",
    ["ControlPhotographer", "DesktopPhotographer"],
)

from pywinauto import Desktop


def rect_to_dict(rect):
    return {
        "left": rect.left,
        "top": rect.top,
        "right": rect.right,
        "bottom": rect.bottom,
        "width": rect.width(),
        "height": rect.height(),
    }


def one_measurement(index):
    start = time.perf_counter()
    desktop = Desktop(backend="uia")
    win = desktop.window(active_only=True).wrapper_object()
    rect = win.rectangle()
    elements = []
    for child in win.descendants()[:40]:
        try:
            crect = child.rectangle()
            elements.append(
                {
                    "name": child.window_text(),
                    "control_type": child.friendly_class_name(),
                    "automation_id": getattr(child.element_info, "automation_id", ""),
                    "class_name": getattr(child.element_info, "class_name", ""),
                    "rect": rect_to_dict(crect),
                }
            )
        except Exception as exc:
            elements.append({"error": repr(exc)})
    screenshot_path = ROOT / f"ufo2-spike-active-window-{index}.png"
    if screenshot_mod and hasattr(screenshot_mod, "ControlPhotographer"):
        image = screenshot_mod.ControlPhotographer(win).capture(save_path=str(screenshot_path))
    else:
        image = win.capture_as_image()
        image.save(screenshot_path)
    elapsed = (time.perf_counter() - start) * 1000
    return win, rect, elements, screenshot_path, elapsed


for i in range(3):
    win, rect, elements, screenshot_path, elapsed = one_measurement(i + 1)
    RESULTS["measurements_ms"].append(round(elapsed, 2))
    if i == 0:
        RESULTS["active_window"] = {
            "title": win.window_text(),
            "class_name": getattr(win.element_info, "class_name", ""),
            "handle": getattr(win.element_info, "handle", None),
            "rect": rect_to_dict(rect),
        }
        RESULTS["elements_sample"] = elements[:12]
        RESULTS["screenshot_path"] = str(screenshot_path)

RESULTS["mean_ms"] = round(sum(RESULTS["measurements_ms"]) / len(RESULTS["measurements_ms"]), 2)

print(json.dumps(RESULTS, indent=2, ensure_ascii=False))
```
