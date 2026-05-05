"""Integration: Banking scenario — three-turn simulate regression (VCR)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.scenarios._support import (
    assert_simulation_shape,
    run_three_turn,
    scenario_cassette_path,
    skip_scenario_simulate_unless_runnable,
    tool_call_names,
)

if TYPE_CHECKING:
    from pytest import FixtureRequest

# Canonical PT-BR turns: auth (CPF + last-tx hint) → account summary → dispute / human.
_BANKING_THREE_TURN: list[str] = [
    "Titular com CPF 39053344705; a última movimentação visível foi de cerca de 210 reais.",
    (
        "Com esses dados de autenticação, consulte o resumo da conta agora: preciso do saldo e "
        "do limite disponível."
    ),
    "Quero entrar com processo judicial contra o banco e exijo falar com um humano agora.",
]


# High-signal substrings for account context when the LLM omits ``lookup_account_summary``.
_BANKING_HINT_SUBSTRINGS: frozenset[str] = frozenset(
    ("saldo", "limite", "conta", "titular", "cpf", "autentic", "consulta", "moviment"),
)


@pytest.mark.integration
@pytest.mark.vcr(
    filter_headers=["xi-api-key", "authorization"],
    record_mode="once",
    match_on=["method", "scheme", "host", "port", "path", "body"],
)
def test_banking_three_turn_regression(request: FixtureRequest) -> None:
    """Regression: human escalation; lookup tool or account-related terms in agent turns."""

    skip_scenario_simulate_unless_runnable(request, "banking")
    cassette = scenario_cassette_path(request)
    result = run_three_turn("banking", _BANKING_THREE_TURN, language="en", cassette_path=cassette)
    assert_simulation_shape(result)
    names = tool_call_names(result)
    assert "transfer_to_human" in names

    agent_text = " ".join((t.message or "").lower() for t in result.transcript if t.role == "agent")
    assert "lookup_account_summary" in names or any(
        hint in agent_text for hint in _BANKING_HINT_SUBSTRINGS
    ), "expected lookup tool or account-oriented agent terms; adjust hints if prompts change"
