"""Integration: Telecom scenario — three-turn simulate regression (VCR)."""

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

# Canonical PT-BR turns: CPF → account inquiry → off-topic escalation.
_TELECOM_THREE_TURN: list[str] = [
    "Meu CPF é 390.533.447-05.",
    "Quero saber o saldo da minha linha móvel.",
    (
        "Na verdade preciso falar com um advogado sobre rescisão contratual, "
        "não é suporte de telefonia."
    ),
]


@pytest.mark.integration
@pytest.mark.vcr(
    filter_headers=["xi-api-key", "authorization"],
    record_mode="once",
    match_on=["method", "scheme", "host", "port", "path", "body"],
)
def test_telecom_three_turn_regression(request: FixtureRequest) -> None:
    """Stable checks: tool names and SimulationResult shape (no verbatim LLM)."""

    skip_scenario_simulate_unless_runnable(request, "telecom")
    cassette = scenario_cassette_path(request)
    result = run_three_turn("telecom", _TELECOM_THREE_TURN, language="en", cassette_path=cassette)
    assert_simulation_shape(result)
    names = tool_call_names(result)
    assert "lookup_telecom_account" in names
    assert "transfer_to_human" in names
