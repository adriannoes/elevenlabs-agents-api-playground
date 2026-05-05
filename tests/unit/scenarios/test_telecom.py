"""Tests for the Telecom vertical scenario."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from eleven_demo.config import get_settings
from eleven_demo.scenarios import telecom as telecom_module


def test_telecom_tool_and_kb_exports_align_with_registry() -> None:
    assert telecom_module.TOOL_NAMES == ["lookup_telecom_account", "transfer_to_human"]
    assert telecom_module.KB_IDS == []
    assert telecom_module.LANGUAGE == "en"
    assert len(telecom_module.SUCCESS_CRITERIA) >= 2


def test_provision_upserts_agent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ELEVENLABS_API_KEY", "test-key-for-validation-only")
    monkeypatch.setenv("DEFAULT_PT_VOICE_ID", "voice-telecom-test")

    fake_agent = MagicMock()
    fake_agent.agent_id = "agent-telecom-1"

    with patch.object(telecom_module, "upsert_agent", return_value=fake_agent) as upsert:
        aid = telecom_module.provision()

    assert aid == "agent-telecom-1"
    upsert.assert_called_once()
    call_name, cfg_arg = upsert.call_args[0]
    assert call_name == "demo-telecom-sac-en"
    assert cfg_arg.agent is not None
    assert cfg_arg.agent.first_message == telecom_module.FIRST_MESSAGE
    assert "ACME" not in cfg_arg.agent.first_message
    assert "ACME" not in telecom_module.SYSTEM_PROMPT


def test_scenario_proxy_delegates_to_inner(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ELEVENLABS_API_KEY", "test-key-for-validation-only")
    monkeypatch.setenv("DEFAULT_PT_VOICE_ID", "voice-proxy-test")

    assert telecom_module.SCENARIO.name == "demo-telecom-sac-en"
    assert telecom_module.SCENARIO.first_message == telecom_module.FIRST_MESSAGE


def test_scenario_from_settings_requires_voice() -> None:
    with patch("eleven_demo.scenarios.telecom.get_settings") as mock_get:
        mock_get.return_value = MagicMock(
            default_agent_voice_id=None,
            default_pt_voice_id=None,
            default_en_voice_id=None,
        )
        with pytest.raises(ValueError, match="DEFAULT_AGENT_VOICE_ID"):
            telecom_module.TelecomScenario.from_settings()


def test_from_settings_registers_convai_demo_tool_webhook_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ELEVENLABS_API_KEY", "test-key-for-validation-only")
    monkeypatch.setenv("DEFAULT_PT_VOICE_ID", "voice-webhook-test")
    monkeypatch.setenv("CONVAI_DEMO_TOOL_WEBHOOK_URL", "https://tunnel.example/convai/demo-tools")
    get_settings.cache_clear()

    scenario = telecom_module.TelecomScenario.from_settings()

    assert scenario.tool_webhook_url == "https://tunnel.example/convai/demo-tools"
    get_settings.cache_clear()
