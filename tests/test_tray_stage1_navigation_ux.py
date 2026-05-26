from __future__ import annotations

from goat_desktop.tray import GoatTrayApp


class FakeLabel:
    def __init__(self, text: str = "") -> None:
        self._text = text

    def setText(self, text: str) -> None:
        self._text = text

    def text(self) -> str:
        return self._text


class FakeButton(FakeLabel):
    def __init__(self, text: str = "") -> None:
        super().__init__(text)
        self.enabled = False

    def setEnabled(self, enabled: bool) -> None:
        self.enabled = enabled


class FakePopup:
    def __init__(self) -> None:
        self.target_value = FakeLabel()
        self.screen_context_value = FakeLabel()
        self.maya_value = FakeLabel()
        self.cue_approve = FakeButton("Ziel verwenden")
        self.cue_reject = FakeButton("Nein, anderes Ziel")


class FakeTray:
    def __init__(self) -> None:
        self.popup = FakePopup()
        self.pending_builder_cue = None
        self.pending_stage1_action = None
        self.pending_stage2_action = None
        self.shown = False

    def show_popup(self) -> None:
        self.shown = True


def test_builder_stage1_cue_shows_target_check_before_navigation() -> None:
    fake = FakeTray()

    GoatTrayApp.receive_builder_cue(
        fake,
        {
            "action_type": "hover",
            "label": "Senden Button",
            "bbox": [10, 20, 110, 80],
        },
    )

    assert fake.pending_stage1_action == {"action_type": "hover", "label": "Senden Button", "scroll_amount": -360}
    assert fake.popup.target_value.text() == "Zielvorschlag: Senden Button"
    assert fake.popup.screen_context_value.text() == "Bitte pruefe das markierte Ziel"
    assert fake.popup.maya_value.text() == "Danach kannst du GOAT navigieren lassen."
    assert fake.popup.cue_approve.text() == "Ziel pruefen"
    assert fake.popup.cue_approve.enabled is True
    assert fake.popup.cue_reject.enabled is True
    assert fake.shown is True


def test_accepted_stage1_cue_turns_into_navigation_preview() -> None:
    fake = FakeTray()
    GoatTrayApp.receive_builder_cue(fake, {"action_type": "hover", "label": "Senden Button", "bbox": [10, 20, 110, 80]})

    GoatTrayApp._finish_builder_cue(
        fake,
        {
            "status": "ok",
            "response": {
                "safety_state": "accept",
                "broker_decision": {"status": "accept", "final_bbox": [10, 20, 110, 80]},
            },
        },
    )

    assert fake.pending_stage1_action["broker_decision"] == {"status": "accept", "final_bbox": [10, 20, 110, 80]}
    assert fake.popup.screen_context_value.text() == "GOAT kann dich navigieren"
    assert fake.popup.maya_value.text() == (
        "GOAT will den Mauszeiger auf Senden Button bewegen. Dabei wird nichts geklickt und nichts getippt."
    )
    assert fake.popup.cue_approve.text() == "Navigieren"
    assert fake.popup.cue_approve.enabled is True


def test_accepted_scroll_cue_turns_into_scroll_preview() -> None:
    fake = FakeTray()
    GoatTrayApp.receive_builder_cue(
        fake,
        {"action_type": "scroll", "label": "Seite", "bbox": [10, 20, 110, 80], "scroll_amount": 360},
    )

    GoatTrayApp._finish_builder_cue(
        fake,
        {
            "status": "ok",
            "response": {
                "safety_state": "accept",
                "broker_decision": {"status": "accept", "final_bbox": [10, 20, 110, 80]},
            },
        },
    )

    assert fake.pending_stage1_action["scroll_amount"] == 360
    assert fake.popup.screen_context_value.text() == "GOAT kann dich navigieren"
    assert fake.popup.maya_value.text() == (
        "GOAT will auf der Seite nach oben scrollen. Dabei wird nichts geklickt und nichts getippt."
    )
    assert fake.popup.cue_approve.text() == "Scrollen"
    assert fake.popup.cue_approve.enabled is True


def test_stage1_done_resets_pending_navigation() -> None:
    fake = FakeTray()
    fake.pending_builder_cue = {"label": "Senden Button"}
    fake.pending_stage1_action = {"action_type": "hover", "label": "Senden Button"}

    GoatTrayApp._finish_builder_cue(fake, {"status": "stage1_done", "response": {"executed": True}})

    assert fake.pending_builder_cue is None
    assert fake.pending_stage1_action is None
    assert fake.popup.screen_context_value.text() == "Navigation ausgefuehrt"
    assert fake.popup.maya_value.text() == "Ich habe dich zum Ziel gefuehrt."
    assert fake.popup.cue_approve.text() == "Ziel verwenden"
    assert fake.popup.cue_approve.enabled is False
    assert fake.popup.cue_reject.enabled is False


def test_builder_stage2_cue_shows_input_check_before_execution() -> None:
    fake = FakeTray()

    GoatTrayApp.receive_builder_cue(
        fake,
        {
            "action_type": "type",
            "label": "Suchfeld",
            "text": "StepStack",
            "safe_text_context": True,
            "bbox": [10, 20, 110, 80],
        },
    )

    assert fake.pending_stage2_action == {
        "action_type": "type",
        "label": "Suchfeld",
        "text": "StepStack",
        "safe_text_context": True,
    }
    assert fake.popup.target_value.text() == "Eingabefeld: Suchfeld"
    assert fake.popup.screen_context_value.text() == "Bitte pruefe das Eingabefeld"
    assert fake.popup.maya_value.text() == "Danach kannst du die Eingabe freigeben."
    assert fake.popup.cue_approve.text() == "Ziel pruefen"


def test_accepted_stage2_cue_turns_into_input_preview() -> None:
    fake = FakeTray()
    GoatTrayApp.receive_builder_cue(
        fake,
        {
            "action_type": "type",
            "label": "Suchfeld",
            "text": "StepStack",
            "safe_text_context": True,
            "bbox": [10, 20, 110, 80],
        },
    )

    GoatTrayApp._finish_builder_cue(
        fake,
        {
            "status": "ok",
            "response": {
                "safety_state": "accept",
                "broker_decision": {"status": "accept", "final_bbox": [10, 20, 110, 80]},
            },
        },
    )

    assert fake.pending_stage2_action["broker_decision"] == {"status": "accept", "final_bbox": [10, 20, 110, 80]}
    assert fake.popup.screen_context_value.text() == "Freigabe fuer Eingabe"
    assert fake.popup.maya_value.text() == (
        'GOAT will Text in Suchfeld eingeben: "StepStack". Bitte pruefe die Eingabe vor dem Ausfuehren.'
    )
    assert fake.popup.cue_approve.text() == "Eingabe ausfuehren"
    assert fake.popup.cue_approve.enabled is True


def test_stage2_preview_without_safe_context_disables_execute() -> None:
    fake = FakeTray()
    GoatTrayApp.receive_builder_cue(
        fake,
        {"action_type": "type", "label": "Suchfeld", "text": "StepStack", "safe_text_context": False, "bbox": [10, 20, 110, 80]},
    )

    GoatTrayApp._finish_builder_cue(
        fake,
        {
            "status": "ok",
            "response": {
                "safety_state": "accept",
                "broker_decision": {"status": "accept", "final_bbox": [10, 20, 110, 80]},
            },
        },
    )

    assert fake.popup.maya_value.text() == "Ich tippe hier noch nicht. Ich habe das Eingabefeld nicht sicher genug erkannt."
    assert fake.popup.cue_approve.text() == "Nicht sicher"
    assert fake.popup.cue_approve.enabled is False


def test_stage2_failed_execution_uses_plain_user_message() -> None:
    fake = FakeTray()
    fake.pending_builder_cue = {"label": "Suchfeld"}
    fake.pending_stage2_action = {"action_type": "type", "label": "Suchfeld", "text": "StepStack"}

    GoatTrayApp._finish_builder_cue(
        fake,
        {
            "status": "stage2_done",
            "response": {
                "executed": False,
                "reason": "safe_text_context must be true before stage 2 text input can execute",
            },
        },
    )

    assert fake.popup.screen_context_value.text() == "Eingabe nicht ausgefuehrt"
    assert fake.popup.maya_value.text() == "Ich tippe hier nicht. Ich habe das Eingabefeld nicht sicher genug erkannt."
    assert fake.popup.cue_approve.enabled is False


def test_stage2_backend_failure_uses_plain_user_message() -> None:
    fake = FakeTray()

    GoatTrayApp._finish_builder_cue(
        fake,
        {
            "status": "stage2_done",
            "response": {"executed": False, "reason": "text input backend failed before completion"},
        },
    )

    assert fake.popup.screen_context_value.text() == "Eingabe nicht ausgefuehrt"
    assert fake.popup.maya_value.text() == "Die Eingabe hat nicht geklappt. Ich melde sie nicht als erledigt."


def test_stage1_backend_failure_uses_plain_user_message() -> None:
    fake = FakeTray()

    GoatTrayApp._finish_builder_cue(
        fake,
        {
            "status": "stage1_done",
            "response": {"executed": False, "reason": "mouse backend failed before pointer move completed"},
        },
    )

    assert fake.popup.screen_context_value.text() == "Navigation nicht ausgefuehrt"
    assert fake.popup.maya_value.text() == "Die Navigation hat nicht geklappt. Ich melde sie nicht als erledigt."


def test_stage2_done_resets_pending_input() -> None:
    fake = FakeTray()
    fake.pending_builder_cue = {"label": "Suchfeld"}
    fake.pending_stage2_action = {"action_type": "type", "label": "Suchfeld", "text": "StepStack"}

    GoatTrayApp._finish_builder_cue(fake, {"status": "stage2_done", "response": {"executed": True}})

    assert fake.pending_builder_cue is None
    assert fake.pending_stage1_action is None
    assert fake.pending_stage2_action is None
    assert fake.popup.screen_context_value.text() == "Eingabe ausgefuehrt"
    assert fake.popup.maya_value.text() == "Ich habe den Text eingetragen."


def test_reject_pending_cue_resets_navigation_state() -> None:
    fake = FakeTray()
    fake.pending_builder_cue = {"label": "Senden Button"}
    fake.pending_stage1_action = {"action_type": "hover", "label": "Senden Button"}
    fake.pending_stage2_action = {"action_type": "type", "label": "Suchfeld", "text": "StepStack"}

    GoatTrayApp.reject_pending_cue(fake)

    assert fake.pending_builder_cue is None
    assert fake.pending_stage1_action is None
    assert fake.pending_stage2_action is None
    assert fake.popup.screen_context_value.text() == "Ziel abgelehnt"
    assert fake.popup.cue_approve.text() == "Ziel verwenden"
