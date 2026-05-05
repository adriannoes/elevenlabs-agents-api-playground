"""Tests for the banking scenario."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from eleven_demo.scenarios import banking as banking_module


def test_banking_exports_tools_and_zrm_settings() -> None:
    assert banking_module.TOOL_NAMES == [
        "lookup_account_summary",
        "request_card_block",
        "request_card_replacement",
        "transfer_to_human",
    ]
    assert banking_module.KB_IDS == []
    assert banking_module.BANKING_PLATFORM_SETTINGS.privacy is not None
    assert banking_module.BANKING_PLATFORM_SETTINGS.privacy.zero_retention_mode is True
    assert banking_module.BANKING_PLATFORM_SETTINGS.privacy.record_voice is False


def test_provision_upserts_agent_with_platform_privacy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ELEVENLABS_API_KEY", "test-key-for-validation-only")
    monkeypatch.setenv("DEFAULT_PT_VOICE_ID", "voice-banking-test")

    fake_agent = MagicMock()
    fake_agent.agent_id = "agent-banking-1"

    with patch.object(banking_module, "upsert_agent", return_value=fake_agent) as upsert:
        aid = banking_module.provision()

    assert aid == "agent-banking-1"
    upsert.assert_called_once()
    kwargs = upsert.call_args.kwargs
    assert kwargs["platform_settings"] is banking_module.BANKING_PLATFORM_SETTINGS

    pos_args = upsert.call_args[0]
    assert pos_args[0] == "demo-banking-sac-en"
    cfg_arg = pos_args[1]
    assert cfg_arg.agent is not None
    assert "Onyx" not in cfg_arg.agent.first_message
    assert "Onyx" not in banking_module.SYSTEM_PROMPT


def test_scenario_proxy_delegates(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ELEVENLABS_API_KEY", "test-key-for-validation-only")
    monkeypatch.setenv("DEFAULT_PT_VOICE_ID", "voice-proxy-test")

    assert banking_module.SCENARIO.name == "demo-banking-sac-en"


def test_from_settings_requires_voice() -> None:
    with patch("eleven_demo.scenarios.banking.get_settings") as mock_get:
        mock_get.return_value = MagicMock(
            default_agent_voice_id=None,
            default_pt_voice_id=None,
            default_en_voice_id=None,
        )
        with pytest.raises(ValueError, match="DEFAULT_AGENT_VOICE_ID"):
            banking_module.BankingScenario.from_settings()
