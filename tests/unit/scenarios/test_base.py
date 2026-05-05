"""Unit tests for the Scenario base contract."""

from __future__ import annotations

import pytest
from elevenlabs.types import ConversationalConfig
from pydantic import ValidationError

from eleven_demo.scenarios.base import (
    DEFAULT_AGENT_LLM,
    DEFAULT_CONVERSATION_TEMPERATURE,
    Scenario,
    convai_tts_model_id_for_language,
)


class _StubScenario(Scenario):
    """Minimal concrete scenario for structural tests."""

    def provision(self) -> str:
        return "agent-id-stub"


def test_scenario_requires_core_fields() -> None:
    with pytest.raises(ValidationError):
        _StubScenario(
            name="",
            system_prompt="sys",
            first_message="fm",
            voice_id="v1",
        )


def test_unknown_tool_name_rejected() -> None:
    with pytest.raises(ValidationError, match="unknown tool_names"):
        _StubScenario(
            name="n",
            system_prompt="sys",
            first_message="fm",
            voice_id="v1",
            tool_names=["not_a_registered_tool"],
        )


def test_convai_tts_model_id_english_maps_flash_v2_5_to_flash_v2() -> None:
    assert convai_tts_model_id_for_language("en", "eleven_flash_v2_5") == "eleven_flash_v2"


def test_convai_tts_model_id_english_keeps_allowed_models() -> None:
    assert convai_tts_model_id_for_language("en", "eleven_flash_v2") == "eleven_flash_v2"
    assert convai_tts_model_id_for_language("en", "eleven_turbo_v2") == "eleven_turbo_v2"


def test_convai_tts_model_id_non_english_uses_configured() -> None:
    assert convai_tts_model_id_for_language("pt", "eleven_flash_v2_5") == "eleven_flash_v2_5"


def test_build_conversation_config_english_tts_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ELEVENLABS_API_KEY", "test-key-for-validation-only")

    raw = _StubScenario(
        name="demo",
        system_prompt="You are the demo.",
        first_message="Hello!",
        language="en",
        voice_id="voice-abc",
        tool_names=["transfer_to_human"],
        kb_doc_ids=["doc-1"],
        success_criteria=["transfer offered"],
    )._build_conversation_config()

    cfg = ConversationalConfig.model_validate(raw)
    assert cfg.agent is not None
    assert cfg.agent.first_message == "Hello!"
    assert cfg.agent.language == "en"
    assert cfg.tts is not None
    assert cfg.tts.voice_id == "voice-abc"
    assert cfg.agent.prompt is not None
    assert cfg.agent.prompt.prompt == "You are the demo."
    assert cfg.agent.prompt.llm == DEFAULT_AGENT_LLM
    assert cfg.agent.prompt.temperature == DEFAULT_CONVERSATION_TEMPERATURE
    assert cfg.tts.model_id == "eleven_flash_v2"
    monkeypatch.setenv("ELEVENLABS_API_KEY", "test-key-for-validation-only")

    raw = _StubScenario(
        name="demo",
        system_prompt="sys",
        first_message="fm",
        voice_id="v",
        kb_doc_ids=["a", "b"],
        success_criteria=["x"],
    )._build_conversation_config()

    cfg = ConversationalConfig.model_validate(raw)
    assert cfg.agent and cfg.agent.prompt and cfg.agent.prompt.knowledge_base is not None
    kb = cfg.agent.prompt.knowledge_base
    assert len(kb) == 2
    assert {loc.id for loc in kb} == {"a", "b"}
    assert all(loc.usage_mode == "auto" for loc in kb)


def test_tool_names_map_to_webhook_tools(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ELEVENLABS_API_KEY", "test-key-for-validation-only")

    raw = _StubScenario(
        name="demo",
        system_prompt="sys",
        first_message="fm",
        voice_id="v",
        tool_names=["lookup_telecom_account", "transfer_to_human"],
        tool_webhook_url="https://hooks.example.test/tools",
        success_criteria=["lookup"],
    )._build_conversation_config()

    cfg = ConversationalConfig.model_validate(raw)
    assert cfg.agent and cfg.agent.prompt and cfg.agent.prompt.tools is not None
    tools = cfg.agent.prompt.tools
    assert len(tools) == 2
    names = []
    for t in tools:
        dumped = t.model_dump(exclude_none=True)
        names.append(dumped["name"])
        assert dumped["type"] == "webhook"
        assert dumped["api_schema"]["url"] == "https://hooks.example.test/tools"
        assert "request_body_schema" in dumped["api_schema"]
        body_schema = dumped["api_schema"]["request_body_schema"]
        assert body_schema["type"] == "object"
        assert "additionalProperties" not in body_schema
        assert "title" not in body_schema
        for prop in body_schema["properties"].values():
            assert "description" in prop
            assert "title" not in prop
    assert names == ["lookup_telecom_account", "transfer_to_human"]


def test_module_alias_pattern_lists_align_with_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    """Concrete modules export TOOL_NAMES / KB_IDS aligned with Scenario lists (FR-14)."""
    monkeypatch.setenv("ELEVENLABS_API_KEY", "test-key-for-validation-only")

    TOOL_NAMES = ["lookup_telecom_account"]  # noqa: N806
    KB_IDS: list[str] = []  # noqa: N806

    scenario = _StubScenario(
        name="acme",
        system_prompt="sys",
        first_message="fm",
        voice_id="v",
        tool_names=TOOL_NAMES,
        kb_doc_ids=KB_IDS,
        success_criteria=["account lookup"],
    )

    assert list(scenario.tool_names) == list(TOOL_NAMES)
    assert list(scenario.kb_doc_ids) == list(KB_IDS)
