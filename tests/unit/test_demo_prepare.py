"""Unit tests for ``scripts/demo_prepare`` merge helper."""

from __future__ import annotations

from scripts import demo_prepare


def test_merge_dotenv_replaces_existing_keys() -> None:
    content = (
        "ELEVENLABS_API_KEY=secret\n"
        "DEMO_AGENT_ID_TELECOM=old-telecom\n"
        "DEMO_AGENT_ID_BANKING=old-bank\n"
    )
    merged = demo_prepare.merge_dotenv_assignments(
        content,
        {"DEMO_AGENT_ID_TELECOM": "new-t", "DEMO_AGENT_ID_BANKING": "new-b"},
    )
    assert "DEMO_AGENT_ID_TELECOM=new-t" in merged
    assert "DEMO_AGENT_ID_BANKING=new-b" in merged
    assert "old-telecom" not in merged
    assert "ELEVENLABS_API_KEY=secret" in merged


def test_merge_dotenv_appends_missing_keys() -> None:
    content = "FOO=1\n"
    merged = demo_prepare.merge_dotenv_assignments(
        content,
        {"DEMO_AGENT_ID_HEALTHCARE": "hc-1"},
    )
    assert merged.startswith("FOO=1")
    assert merged.rstrip().endswith("DEMO_AGENT_ID_HEALTHCARE=hc-1")


def test_merge_dotenv_respects_export_prefix_lines() -> None:
    content = "export DEMO_AGENT_ID_TELECOM=old\n"
    merged = demo_prepare.merge_dotenv_assignments(
        content,
        {"DEMO_AGENT_ID_TELECOM": "tid"},
    )
    assert "DEMO_AGENT_ID_TELECOM=tid" in merged
    assert "old" not in merged


def test_merge_dotenv_preserves_comments_and_blanks() -> None:
    content = "# header\n\nDEMO_AGENT_ID_TELECOM=x\n"
    merged = demo_prepare.merge_dotenv_assignments(
        content,
        {"DEMO_AGENT_ID_TELECOM": "y"},
    )
    assert "# header" in merged
    assert "\n\n" in merged or merged.count("\n") >= 2
    assert "DEMO_AGENT_ID_TELECOM=y" in merged
