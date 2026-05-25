from __future__ import annotations

from goat_desktop.uia_context import build_uia_marker, build_uia_screen_context, find_best_uia_match


def test_find_best_uia_match_finds_named_target() -> None:
    match = find_best_uia_match(
        [
            {
                "name": "Downloads",
                "control_type": "ListItem",
                "rect": {"left": 20, "top": 30, "right": 120, "bottom": 80},
            },
            {
                "name": "StepStack",
                "control_type": "ListItem",
                "rect": {"left": 200, "top": 100, "right": 340, "bottom": 150},
            },
        ],
        "Siehst du den StepStack Ordner auf meinem Desktop?",
    )

    assert match is not None
    assert match["element"]["name"] == "StepStack"
    assert match["score"] >= 0.95


def test_find_best_uia_match_normalizes_german_umlauts() -> None:
    match = find_best_uia_match(
        [
            {
                "name": "Senden Schaltfl\u00e4che",
                "control_type": "Button",
                "rect": {"left": 20, "top": 30, "right": 120, "bottom": 80},
            }
        ],
        "Wo ist die Senden Schaltflaeche?",
    )

    assert match is not None
    assert match["element"]["name"] == "Senden Schaltfl\u00e4che"


def test_find_best_uia_match_ignores_weak_match() -> None:
    match = find_best_uia_match(
        [{"name": "Downloads", "control_type": "ListItem", "rect": {"left": 0, "top": 0, "right": 1, "bottom": 1}}],
        "Wo ist StepStack?",
    )

    assert match is None


def test_build_uia_marker_uses_element_rect() -> None:
    match = {
        "score": 0.95,
        "element": {
            "name": "StepStack",
            "control_type": "ListItem",
            "rect": {"left": 200, "top": 100, "right": 340, "bottom": 150},
        },
    }

    marker = build_uia_marker(match)

    assert marker == {
        "available": True,
        "label": "StepStack",
        "region": {"x": 200.0, "y": 100.0, "width": 140.0, "height": 50.0},
        "confidence": 0.95,
        "source": "uia",
    }


def test_build_uia_screen_context_is_clear() -> None:
    context = build_uia_screen_context(
        {
            "score": 0.95,
            "element": {
                "name": "StepStack",
                "control_type": "ListItem",
                "rect": {"left": 200, "top": 100, "right": 340, "bottom": 150},
            },
        }
    )

    assert context == "Lokales UIA: StepStack (ListItem) sichtbar. Vertrauen 0.95 via uia."
