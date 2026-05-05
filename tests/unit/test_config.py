"""Unit tests for `eleven_demo.config.Settings` and `get_settings`."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from pydantic import ValidationError

from eleven_demo.config import (
    Settings,
    conversational_agent_voice_id,
    get_settings,
    resolve_conversational_agent_voice_id,
)

if TYPE_CHECKING:
    from _pytest.monkeypatch import MonkeyPatch


def test_loads_default_tts_model_when_not_set(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("ELEVENLABS_API_KEY", "xi-test-key")
    monkeypatch.delenv("TTS_MODEL_ID", raising=False)

    assert get_settings().tts_model_id == "eleven_flash_v2_5"


def test_overrides_defaults_from_env(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("ELEVENLABS_API_KEY", "xi-test-key")
    monkeypatch.setenv("TTS_MODEL_ID", "custom_tts_model")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")

    settings = get_settings()
    assert settings.tts_model_id == "custom_tts_model"
    assert settings.log_level == "DEBUG"


def test_raises_validation_error_when_api_key_missing(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)

    with pytest.raises(ValidationError) as exc_info:
        get_settings()

    assert "elevenlabs_api_key" in str(exc_info.value)


def test_raises_when_api_key_empty(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("ELEVENLABS_API_KEY", "")

    with pytest.raises(ValidationError) as exc_info:
        get_settings()

    assert "ELEVENLABS_API_KEY is required" in str(exc_info.value)


def test_secret_str_does_not_leak_in_repr(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    secret = "xi-super-secret-do-not-print"
    monkeypatch.setenv("ELEVENLABS_API_KEY", secret)

    settings = get_settings()
    text = repr(settings)

    assert secret not in text


def test_get_settings_is_cached(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("ELEVENLABS_API_KEY", "xi-test-key-one")

    first = get_settings()
    second = get_settings()

    assert first is second


def test_cache_clear_returns_fresh_settings(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("ELEVENLABS_API_KEY", "xi-first")
    before = get_settings()

    monkeypatch.setenv("ELEVENLABS_API_KEY", "xi-second")
    get_settings.cache_clear()

    after = get_settings()

    assert before is not after
    assert after.elevenlabs_api_key.get_secret_value() == "xi-second"


def test_optional_env_empty_string_becomes_none(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("ELEVENLABS_API_KEY", "xi-test-key")
    monkeypatch.setenv("DEFAULT_PT_VOICE_ID", "")

    settings = get_settings()

    assert settings.default_pt_voice_id is None


def test_settings_instantiation_without_cache(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("ELEVENLABS_API_KEY", "xi-direct")

    s = Settings()

    assert s.elevenlabs_api_key.get_secret_value() == "xi-direct"


def test_openai_api_key_optional(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("ELEVENLABS_API_KEY", "xi-test-key")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    get_settings.cache_clear()

    s = get_settings()
    assert s.openai_api_key is None


def test_openai_api_key_loaded_from_env(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("ELEVENLABS_API_KEY", "xi-test-key")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-openai-test")
    get_settings.cache_clear()

    s = get_settings()
    assert s.openai_api_key is not None
    assert s.openai_api_key.get_secret_value() == "sk-openai-test"


def test_openai_secret_not_in_repr(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("ELEVENLABS_API_KEY", "xi-test-key")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-super-secret-openai")
    get_settings.cache_clear()

    s = get_settings()
    text = repr(s)
    assert "sk-super-secret-openai" not in text


def test_conversational_agent_voice_id_prefers_agent_then_en_then_pt(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("ELEVENLABS_API_KEY", "xi-test-key")
    monkeypatch.setenv("DEFAULT_AGENT_VOICE_ID", "voice-agent")
    monkeypatch.setenv("DEFAULT_PT_VOICE_ID", "voice-pt")
    monkeypatch.setenv("DEFAULT_EN_VOICE_ID", "voice-en")
    get_settings.cache_clear()

    s = get_settings()
    assert conversational_agent_voice_id(s) == "voice-agent"


def test_conversational_agent_voice_id_prefers_en_over_pt_when_agent_missing(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("ELEVENLABS_API_KEY", "xi-test-key")
    monkeypatch.delenv("DEFAULT_AGENT_VOICE_ID", raising=False)
    monkeypatch.setenv("DEFAULT_PT_VOICE_ID", "voice-pt")
    monkeypatch.setenv("DEFAULT_EN_VOICE_ID", "voice-en")
    get_settings.cache_clear()

    s = get_settings()
    assert conversational_agent_voice_id(s) == "voice-en"
    assert resolve_conversational_agent_voice_id(s) == "voice-en"


def test_conversational_agent_voice_id_falls_back_to_en_when_pt_missing(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("ELEVENLABS_API_KEY", "xi-test-key")
    monkeypatch.delenv("DEFAULT_AGENT_VOICE_ID", raising=False)
    monkeypatch.delenv("DEFAULT_PT_VOICE_ID", raising=False)
    monkeypatch.setenv("DEFAULT_EN_VOICE_ID", "voice-en-only")
    get_settings.cache_clear()

    s = get_settings()
    assert conversational_agent_voice_id(s) == "voice-en-only"
    assert resolve_conversational_agent_voice_id(s) == "voice-en-only"


def test_conversational_agent_voice_id_falls_back_to_pt_when_only_pt_set(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("ELEVENLABS_API_KEY", "xi-test-key")
    monkeypatch.delenv("DEFAULT_AGENT_VOICE_ID", raising=False)
    monkeypatch.delenv("DEFAULT_EN_VOICE_ID", raising=False)
    monkeypatch.setenv("DEFAULT_PT_VOICE_ID", "voice-pt-only")
    get_settings.cache_clear()

    s = get_settings()
    assert conversational_agent_voice_id(s) == "voice-pt-only"
    assert resolve_conversational_agent_voice_id(s) == "voice-pt-only"


def test_resolve_conversational_agent_voice_id_raises_when_all_missing(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("ELEVENLABS_API_KEY", "xi-test-key")
    monkeypatch.delenv("DEFAULT_AGENT_VOICE_ID", raising=False)
    monkeypatch.delenv("DEFAULT_PT_VOICE_ID", raising=False)
    monkeypatch.delenv("DEFAULT_EN_VOICE_ID", raising=False)
    get_settings.cache_clear()

    s = get_settings()
    assert conversational_agent_voice_id(s) is None
    with pytest.raises(ValueError, match="DEFAULT_AGENT_VOICE_ID"):
        resolve_conversational_agent_voice_id(s)
