from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication

from goat_desktop.popup import GoatPopup


APP = QApplication.instance() or QApplication([])


def test_popup_uses_assistant_first_labels() -> None:
    popup = GoatPopup()

    assert popup.screen_context_caption.text() == "Deine Frage"
    assert popup.maya_caption.text() == "Maya"
    assert popup.screen_context_value.text() == "Noch keine Frage"
    assert popup.maya_value.text() == "Bereit. Frag mich, was ich fuer dich finden soll."
    assert popup.review_status_value.isHidden() is True
    assert popup.connection_chip.text() == "Status: Bereit"
    assert popup.audio_chip.text() == "Sprache: Bereit"
    assert popup.talk_button.text() == "Mit Maya sprechen"
    assert popup.cue_approve.text() == "Pruefen"
    assert popup.cue_reject.text() == "Abbrechen"
    assert popup.vision_panel.isHidden() is True


def test_popup_livetalk_mode_keeps_main_path_plain() -> None:
    popup = GoatPopup()
    popup.review_status_value.setText("Nur Review - keine Ausfuehrung")
    popup.review_status_value.setVisible(True)

    popup.set_livetalk_mode(True, focus_chat=False)

    assert popup.talk_button.text() == "Halten zum Sprechen"
    assert popup.video_frames_toggle.isHidden() is False
    assert popup.cue_approve.isHidden() is True
    assert popup.cue_reject.isHidden() is True
    assert popup.review_status_value.isHidden() is True

    popup.set_livetalk_mode(False, focus_chat=False)

    assert popup.talk_button.text() == "Mit Maya sprechen"
    assert popup.video_frames_toggle.isHidden() is True
