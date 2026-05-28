from __future__ import annotations

from goat_desktop.redaction import (
    REDACTED_VALUE,
    SENSITIVE_FIELD_LABEL,
    SENSITIVE_TARGET_LABEL,
    redact_context,
    redact_locked_classification_payload,
    redact_locked_request_payload,
    redact_locked_stage3_payload,
    redact_nested_context_values,
)


def test_redaction_labels_are_stable_normal_user_copy() -> None:
    assert REDACTED_VALUE == "[redacted]"
    assert SENSITIVE_FIELD_LABEL == "sensibles Feld"
    assert SENSITIVE_TARGET_LABEL == "sensibles Ziel"


def test_locked_request_redaction_does_not_mutate_source() -> None:
    source = {
        "action_type": "type",
        "label": "api-token-input",
        "text": "private-value",
        "context": {"automation_id": "api-token-input"},
    }

    redacted = redact_locked_request_payload(source, redact_text=True)

    assert redacted == {
        "action_type": "type",
        "label": "[redacted]",
        "label_redacted": True,
        "text": "",
        "text_redacted": True,
        "context": {"automation_id": "[redacted]"},
        "context_redacted": True,
    }
    assert source["label"] == "api-token-input"
    assert source["text"] == "private-value"
    assert source["context"] == {"automation_id": "api-token-input"}


def test_locked_classification_redacts_normalized_text() -> None:
    redacted = redact_locked_classification_payload({"stage": 4, "normalized_text": "type api-token-input"})

    assert redacted["stage"] == 4
    assert redacted["normalized_text"] == "[redacted]"
    assert redacted["normalized_text_redacted"] is True


def test_locked_stage3_payload_redacts_consequence_summary() -> None:
    redacted = redact_locked_stage3_payload(
        {"action_type": "type", "label": "api-token-input", "consequence_summary": "raw-secret-summary"}
    )

    assert redacted["label"] == "[redacted]"
    assert redacted["label_redacted"] is True
    assert redacted["consequence_summary"] == ""
    assert redacted["consequence_summary_redacted"] is True


def test_nested_context_redaction_is_recursive() -> None:
    payload = {
        "broker_decision": {
            "candidate": {
                "raw_evidence": {
                    "request": {
                        "context": {"automation_id": "api-token-input", "aria_label": "2FA code"},
                    }
                }
            }
        }
    }

    redacted = redact_nested_context_values(payload)

    request = redacted["broker_decision"]["candidate"]["raw_evidence"]["request"]
    assert request["context"] == {"automation_id": "[redacted]", "aria_label": "[redacted]"}
    assert request["context_redacted"] is True
    assert payload["broker_decision"]["candidate"]["raw_evidence"]["request"]["context"] == {
        "automation_id": "api-token-input",
        "aria_label": "2FA code",
    }


def test_context_redaction_preserves_keys_only() -> None:
    assert redact_context({"input_type": "password", "role": "Edit"}) == {
        "input_type": "[redacted]",
        "role": "[redacted]",
    }
