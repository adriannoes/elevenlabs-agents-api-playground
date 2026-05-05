"""Unit tests for Convai HTML helpers in ``apps/gradio_app.py``."""

from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_gradio_app() -> object:
    root = Path(__file__).resolve().parents[3]
    path = root / "apps" / "gradio_app.py"
    spec = importlib.util.spec_from_file_location("gradio_app_under_test", path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_gradio_app = _load_gradio_app()


def test_convai_signed_embed_has_no_script_tag() -> None:
    html = _gradio_app._convai_signed_embed("https://example.test/signed?token=abc")  # type: ignore[attr-defined]
    assert "<elevenlabs-convai" in html
    assert "signed-url=" in html
    assert "<script" not in html.lower()


def test_convai_missing_agent_html_names_env_and_prep_command() -> None:
    html = _gradio_app._convai_missing_agent_html("DEMO_AGENT_ID_TELECOM")  # type: ignore[attr-defined]
    assert "DEMO_AGENT_ID_TELECOM" in html
    assert "demo_prepare.py" in html
