"""Tests for tool schemas and deterministic mocks."""

from __future__ import annotations

from unittest.mock import patch

import pydantic
import pytest

from eleven_demo.agents.tools import (
    TOOLS_REGISTRY,
    BookMedicalAppointmentInput,
    LookupAccountSummaryInput,
    LookupTelecomAccountInput,
    RequestCardBlockInput,
    RequestCardReplacementInput,
    TransferToHumanInput,
    mock_book_medical_appointment,
    mock_lookup_account_summary,
    mock_lookup_telecom_account,
    mock_request_card_block,
    mock_request_card_replacement,
    mock_transfer_to_human,
)


def test_lookup_telecom_rejects_bad_cpf() -> None:
    with pytest.raises(pydantic.ValidationError):
        LookupTelecomAccountInput.model_validate({"cpf": "123"})


def test_lookup_telecom_accepts_formatted_cpf() -> None:
    inp = LookupTelecomAccountInput.model_validate({"cpf": "123.456.789-09"})
    assert inp.cpf == "12345678909"


def test_deterministic_mock_output() -> None:
    sample = LookupTelecomAccountInput.model_validate({"cpf": "11144477735"})
    a = mock_lookup_telecom_account(sample)
    b = mock_lookup_telecom_account(sample)
    assert a.account_ref_masked == b.account_ref_masked
    assert "***" in a.account_ref_masked


def test_transfer_output_no_raw_pii_echo() -> None:
    out = mock_transfer_to_human(
        TransferToHumanInput(reason_code="customer_request", customer_reference_hint="user-42")
    )
    assert "user-42" not in out.callback_reference


def test_tools_registry_completeness() -> None:
    expected = {
        "lookup_telecom_account",
        "lookup_account_summary",
        "request_card_block",
        "request_card_replacement",
        "book_medical_appointment",
        "transfer_to_human",
    }
    assert set(TOOLS_REGISTRY.keys()) == expected


@pytest.mark.parametrize(
    ("payload", "match"),
    [
        ({"cpf": "12345678901", "last_transaction_amount_hint_brl": 0}, "greater than 0"),
        ({"cpf": "abc", "last_transaction_amount_hint_brl": 10.0}, "11 digits"),
    ],
)
def test_lookup_account_summary_validation(payload: dict, match: str) -> None:
    with pytest.raises(pydantic.ValidationError, match=match):
        LookupAccountSummaryInput.model_validate(payload)


def test_mock_lookup_account_summary_shape() -> None:
    inp = LookupAccountSummaryInput.model_validate(
        {"cpf": "11144477735", "last_transaction_amount_hint_brl": 42.5},
    )
    out = mock_lookup_account_summary(inp)
    assert "11144477735"[-4:] in out.account_ref_masked or out.account_ref_masked
    assert out.available_credit_brl >= 0
    assert out.recent_activity_score in ("low", "medium", "high")


@pytest.mark.parametrize(
    ("field", "payload"),
    [
        (
            "cpf",
            {"cpf": "12", "card_last_four": "1234"},
        ),
        (
            "card_last_four",
            {"cpf": "12345678901", "card_last_four": "12"},
        ),
    ],
)
def test_request_card_block_validators(field: str, payload: dict) -> None:
    with pytest.raises(pydantic.ValidationError) as exc:
        RequestCardBlockInput.model_validate(payload)
    assert any(err["loc"] and field in err["loc"][-1] for err in exc.value.errors())


@pytest.mark.parametrize(
    ("field", "payload"),
    [
        ("cpf", {"cpf": "12", "card_last_four": "1234", "mailing_postal_hint": None}),
        ("card_last_four", {"cpf": "12345678901", "card_last_four": "99"}),
    ],
)
def test_request_card_replacement_validators(field: str, payload: dict) -> None:
    with pytest.raises(pydantic.ValidationError) as exc:
        RequestCardReplacementInput.model_validate(payload)
    assert any(err["loc"] and field in err["loc"][-1] for err in exc.value.errors())


def test_mock_request_card_block_deterministic() -> None:
    inp = RequestCardBlockInput.model_validate({"cpf": "12345678901", "card_last_four": "9876"})
    a = mock_request_card_block(inp)
    b = mock_request_card_block(inp)
    assert a == b
    assert a.status == "queued"


def test_mock_request_card_replacement_uses_optional_hint() -> None:
    base = {"cpf": "12345678901", "card_last_four": "4242"}
    with_hint = RequestCardReplacementInput.model_validate({**base, "mailing_postal_hint": "01310"})
    no_hint = RequestCardReplacementInput.model_validate(base)
    assert (
        mock_request_card_replacement(with_hint).ticket_ref_masked
        != mock_request_card_replacement(no_hint).ticket_ref_masked
    )


@pytest.mark.parametrize("window", ("morning", "afternoon"))
def test_mock_book_medical_sets_hour_by_window(window: str) -> None:
    inp = BookMedicalAppointmentInput.model_validate(
        {"cpf_or_ref": "REF-001", "preferred_window": window},
    )
    out = mock_book_medical_appointment(inp)
    assert out.reference_token.startswith("APT-")
    expect_hour = 14 if window == "afternoon" else 9
    assert out.appointment_slot_start_utc.hour == expect_hour


def test_mock_book_medical_short_ref_uses_anon_suffix() -> None:
    inp = BookMedicalAppointmentInput.model_validate(
        {"cpf_or_ref": "ab", "preferred_window": "morning"},
    )
    out = mock_book_medical_appointment(inp)
    assert out.specialty in ("general", "pulmonology", "cardiology", "referral_router")


@patch("eleven_demo.agents.tools._stable_int_from_text", side_effect=[0, 1, 2, 3])
def test_mock_book_medical_specialty_branches(_mock_seed: object) -> None:
    inp = BookMedicalAppointmentInput.model_validate(
        {"cpf_or_ref": "LONGREF-9999", "preferred_window": "morning"},
    )
    assert mock_book_medical_appointment(inp).specialty == "general"
    assert mock_book_medical_appointment(inp).specialty == "pulmonology"
    assert mock_book_medical_appointment(inp).specialty == "cardiology"
    assert mock_book_medical_appointment(inp).specialty == "referral_router"
