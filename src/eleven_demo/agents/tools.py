"""Pydantic tool schemas plus deterministic mocks for ElevenAgents server tools."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

CPF_REGEX = re.compile(r"^\d{11}$")
LAST4_REGEX = re.compile(r"^\d{4}$")

type ToolCallable = Callable[..., BaseModel]
type ToolRegistration = tuple[type[BaseModel], type[BaseModel], ToolCallable]


def _stable_int_from_text(value: str) -> int:
    digest = hashlib.sha256(value.encode()).hexdigest()
    return int(digest[:12], 16)


def normalize_cpf_digits(value: str) -> str:
    """Return digits-only CPF (11 chars) after stripping separators and whitespace."""
    digits = "".join(ch for ch in value if ch.isdigit())
    return digits


class LookupTelecomAccountInput(BaseModel):
    cpf: str = Field(description="Brazilian taxpayer id (CPF), digits only after normalization.")

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    @field_validator("cpf")
    @classmethod
    def digits_only_eleven(cls, v: str) -> str:
        d = normalize_cpf_digits(v)
        if not CPF_REGEX.fullmatch(d):
            msg = "cpf must contain exactly 11 digits"
            raise ValueError(msg)
        return d


class LookupTelecomAccountOutput(BaseModel):
    account_ref_masked: str
    balance_brl_major: float
    plan_summary: Literal["prepaid_standard", "postpaid_standard", "corporate_managed"]
    support_channel_locked: Literal["billing", "tech", "collections"]

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


def mock_lookup_telecom_account(inp: LookupTelecomAccountInput) -> LookupTelecomAccountOutput:
    seed = _stable_int_from_text(inp.cpf)
    last4 = inp.cpf[-4:]
    major = round((seed % 9000) / 100 + 10.5, 2)
    p = seed % 3
    c = (seed // 3) % 3
    plan: Literal["prepaid_standard", "postpaid_standard", "corporate_managed"] = (
        "prepaid_standard" if p == 0 else "postpaid_standard" if p == 1 else "corporate_managed"
    )
    channel: Literal["billing", "tech", "collections"] = (
        "billing" if c == 0 else "tech" if c == 1 else "collections"
    )
    return LookupTelecomAccountOutput(
        account_ref_masked=f"***{last4}",
        balance_brl_major=major,
        plan_summary=plan,
        support_channel_locked=channel,
    )


class LookupAccountSummaryInput(BaseModel):
    cpf: str
    last_transaction_amount_hint_brl: float = Field(
        ...,
        gt=0,
        description=(
            "User-provided coarse amount from recent activity; used only after identity checks."
        ),
    )

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    @field_validator("cpf")
    @classmethod
    def cpf_validator(cls, v: str) -> str:
        d = normalize_cpf_digits(v)
        if not CPF_REGEX.fullmatch(d):
            msg = "cpf must contain exactly 11 digits"
            raise ValueError(msg)
        return d


class LookupAccountSummaryOutput(BaseModel):
    account_ref_masked: str
    available_credit_brl: float
    recent_activity_score: Literal["low", "medium", "high"]

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


def mock_lookup_account_summary(inp: LookupAccountSummaryInput) -> LookupAccountSummaryOutput:
    seed = _stable_int_from_text(f"{inp.cpf}:{inp.last_transaction_amount_hint_brl:g}")
    last4 = inp.cpf[-4:]
    credit = round(float(seed % 50_000) / 100, 2)
    i = seed % 3
    score: Literal["low", "medium", "high"] = "low" if i == 0 else "medium" if i == 1 else "high"
    return LookupAccountSummaryOutput(
        account_ref_masked=f"ACC·{last4}",
        available_credit_brl=credit,
        recent_activity_score=score,
    )


class RequestCardBlockInput(BaseModel):
    cpf: str
    card_last_four: str

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    @field_validator("cpf")
    @classmethod
    def cpf_val(cls, v: str) -> str:
        d = normalize_cpf_digits(v)
        if not CPF_REGEX.fullmatch(d):
            msg = "cpf must contain exactly 11 digits"
            raise ValueError(msg)
        return d

    @field_validator("card_last_four")
    @classmethod
    def four_digits(cls, v: str) -> str:
        if not LAST4_REGEX.fullmatch(v):
            msg = "card_last_four must be exactly 4 digits"
            raise ValueError(msg)
        return v


class RequestCardBlockOutput(BaseModel):
    ticket_ref_masked: str
    status: Literal["queued"]

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


def mock_request_card_block(inp: RequestCardBlockInput) -> RequestCardBlockOutput:
    seed = _stable_int_from_text(f"{inp.cpf}:{inp.card_last_four}")
    return RequestCardBlockOutput(
        ticket_ref_masked=f"BLK-{inp.card_last_four}-{(seed % 900000):06d}",
        status="queued",
    )


class RequestCardReplacementInput(BaseModel):
    cpf: str
    card_last_four: str
    mailing_postal_hint: str | None = None

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    @field_validator("cpf")
    @classmethod
    def cpf_val(cls, v: str) -> str:
        d = normalize_cpf_digits(v)
        if not CPF_REGEX.fullmatch(d):
            msg = "cpf must contain exactly 11 digits"
            raise ValueError(msg)
        return d

    @field_validator("card_last_four")
    @classmethod
    def four_digits(cls, v: str) -> str:
        if not LAST4_REGEX.fullmatch(v):
            msg = "card_last_four must be exactly 4 digits"
            raise ValueError(msg)
        return v


class RequestCardReplacementOutput(BaseModel):
    ticket_ref_masked: str
    eta_business_days: int
    status: Literal["queued"]

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


def mock_request_card_replacement(inp: RequestCardReplacementInput) -> RequestCardReplacementOutput:
    seed = _stable_int_from_text(f"{inp.cpf}:{inp.card_last_four}:{inp.mailing_postal_hint or '-'}")
    return RequestCardReplacementOutput(
        ticket_ref_masked=f"RCR-{inp.card_last_four}-{(seed % 900000):06d}",
        eta_business_days=5 + seed % 4,
        status="queued",
    )


class BookMedicalAppointmentInput(BaseModel):
    cpf_or_ref: str = Field(
        description="Masked or internal reference identifier; omit raw CPF in logs.",
    )
    preferred_window: Literal["morning", "afternoon"]

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class BookMedicalAppointmentOutput(BaseModel):
    appointment_slot_start_utc: datetime
    specialty: Literal["general", "pulmonology", "cardiology", "referral_router"]
    reference_token: str

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


def mock_book_medical_appointment(inp: BookMedicalAppointmentInput) -> BookMedicalAppointmentOutput:
    seed = _stable_int_from_text(f"{inp.cpf_or_ref}:{inp.preferred_window}")
    start = datetime.now(tz=UTC).replace(minute=0, second=0, microsecond=0)
    base = start + timedelta(days=1 + seed % 14)
    base = base.replace(hour=14) if inp.preferred_window == "afternoon" else base.replace(hour=9)
    specs = json.dumps(
        {
            "masked_ref_suffix": inp.cpf_or_ref[-4:] if len(inp.cpf_or_ref) >= 4 else "anon",
            "window": inp.preferred_window,
        },
        separators=(",", ":"),
    )
    spec_hash = hashlib.sha256(specs.encode()).hexdigest()
    r = seed % 4
    specialty: Literal["general", "pulmonology", "cardiology", "referral_router"] = (
        "general"
        if r == 0
        else "pulmonology"
        if r == 1
        else "cardiology"
        if r == 2
        else "referral_router"
    )
    return BookMedicalAppointmentOutput(
        appointment_slot_start_utc=base,
        specialty=specialty,
        reference_token=f"APT-{spec_hash[:10]}",
    )


class TransferToHumanInput(BaseModel):
    reason_code: Literal["customer_request", "compliance_escalation", "off_topic", "ambiguous"]
    customer_reference_hint: str | None = None

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class TransferToHumanOutput(BaseModel):
    queue_position: int
    callback_reference: str

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


def mock_transfer_to_human(inp: TransferToHumanInput) -> TransferToHumanOutput:
    payload = inp.reason_code + (inp.customer_reference_hint or "")
    seed = _stable_int_from_text(payload)
    return TransferToHumanOutput(
        queue_position=1 + (seed % 20),
        callback_reference=f"TCK-{(seed % 999999):06d}",
    )


TOOLS_REGISTRY: dict[str, ToolRegistration] = {
    "lookup_telecom_account": (
        LookupTelecomAccountInput,
        LookupTelecomAccountOutput,
        mock_lookup_telecom_account,
    ),
    "lookup_account_summary": (
        LookupAccountSummaryInput,
        LookupAccountSummaryOutput,
        mock_lookup_account_summary,
    ),
    "request_card_block": (RequestCardBlockInput, RequestCardBlockOutput, mock_request_card_block),
    "request_card_replacement": (
        RequestCardReplacementInput,
        RequestCardReplacementOutput,
        mock_request_card_replacement,
    ),
    "book_medical_appointment": (
        BookMedicalAppointmentInput,
        BookMedicalAppointmentOutput,
        mock_book_medical_appointment,
    ),
    "transfer_to_human": (TransferToHumanInput, TransferToHumanOutput, mock_transfer_to_human),
}
