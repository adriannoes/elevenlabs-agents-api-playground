"""Tests for the healthcare scenario."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from eleven_demo.scenarios import healthcare as healthcare_module


@pytest.fixture(autouse=True)
def clear_healthcare_kb_cache() -> None:
    healthcare_module._kb_doc_ids_cache.clear()
    yield
    healthcare_module._kb_doc_ids_cache.clear()


def test_healthcare_exports_tools_zrm_and_kb_alias() -> None:
    assert healthcare_module.TOOL_NAMES == ["book_medical_appointment", "transfer_to_human"]
    assert healthcare_module.KB_IDS is healthcare_module._kb_doc_ids_cache
    assert healthcare_module.HEALTHCARE_PLATFORM_SETTINGS.privacy is not None
    assert healthcare_module.HEALTHCARE_PLATFORM_SETTINGS.privacy.zero_retention_mode is True
    assert healthcare_module.HEALTHCARE_PLATFORM_SETTINGS.privacy.record_voice is False


def test_healthcare_kb_filenames_match_seed_task_list() -> None:
    assert healthcare_module.HEALTHCARE_KB_FILENAMES == (
        "01-symptom-fever.md",
        "02-symptom-headache.md",
        "03-symptom-chest-pain.md",
        "04-specialties.md",
        "05-lgpd-policy.md",
        "06-demo-conversation-cues.md",
    )


def test_healthcare_kb_seed_paths_exist() -> None:
    paths = healthcare_module.healthcare_kb_seed_paths()
    assert len(paths) == 6
    for path in paths:
        assert path.is_file()


def test_provision_indexes_kb_and_upserts_agent_with_privacy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ELEVENLABS_API_KEY", "test-key-for-validation-only")
    monkeypatch.setenv("DEFAULT_PT_VOICE_ID", "voice-health-test")

    fake_paths = tuple(Path(f"/mock/{name}") for name in healthcare_module.HEALTHCARE_KB_FILENAMES)
    fake_docs = []
    for i, name in enumerate(healthcare_module.HEALTHCARE_KB_FILENAMES):
        m = MagicMock()
        m.id = f"doc-{i}"
        m.name = name
        fake_docs.append(m)

    fake_agent = MagicMock()
    fake_agent.agent_id = "agent-health-1"

    with (
        patch.object(healthcare_module, "healthcare_kb_seed_paths", return_value=fake_paths),
        patch.object(
            healthcare_module,
            "ensure_kb_file_uploaded",
            side_effect=fake_docs,
        ) as ensure_upload,
        patch.object(healthcare_module, "compute_rag") as compute_rag,
        patch.object(healthcare_module, "upsert_agent", return_value=fake_agent) as upsert,
    ):
        aid = healthcare_module.provision()

    assert aid == "agent-health-1"
    assert ensure_upload.call_count == 6
    compute_rag.assert_called_once_with(
        ["doc-0", "doc-1", "doc-2", "doc-3", "doc-4", "doc-5"],
        client=None,
    )

    upsert.assert_called_once()
    ps = upsert.call_args.kwargs["platform_settings"]
    assert ps is healthcare_module.HEALTHCARE_PLATFORM_SETTINGS
    assert upsert.call_args[0][0] == "demo-healthcare-triage-en"
    cfg_arg = upsert.call_args[0][1]
    assert cfg_arg.agent is not None
    assert "VITA-" in healthcare_module.SYSTEM_PROMPT

    assert healthcare_module.KB_IDS == [
        "doc-0",
        "doc-1",
        "doc-2",
        "doc-3",
        "doc-4",
        "doc-5",
    ]


def test_scenario_proxy_delegates(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ELEVENLABS_API_KEY", "test-key-for-validation-only")
    monkeypatch.setenv("DEFAULT_PT_VOICE_ID", "voice-proxy-health")

    assert healthcare_module.SCENARIO.name == "demo-healthcare-triage-en"


def test_from_settings_requires_voice() -> None:
    with patch("eleven_demo.scenarios.healthcare.get_settings") as mock_get:
        mock_get.return_value = MagicMock(
            default_agent_voice_id=None,
            default_pt_voice_id=None,
            default_en_voice_id=None,
        )
        with pytest.raises(ValueError, match="DEFAULT_AGENT_VOICE_ID"):
            healthcare_module.HealthcareScenario.from_settings()
