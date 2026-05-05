"""Local Gradio surface for ElevenLabs vertical exploration (TTS, agents, benchmarks)."""

from __future__ import annotations

import html
import math
import os
import tempfile
from pathlib import Path
from typing import Any, Literal, cast

import gradio as gr
import pandas as pd
from dotenv import load_dotenv
from elevenlabs.core import ApiError

from eleven_demo.benchmarks.tts_vendor import (
    VENDOR_CANONICAL_TEXT_SETS,
    VendorBenchmarkReport,
    comparison_from_vendor_report,
    run_vendor_benchmark,
)
from eleven_demo.client import get_client
from eleven_demo.config import Settings, get_settings
from eleven_demo.metrics.latency import LatencyReport
from eleven_demo.scenarios import healthcare as healthcare_scenario
from eleven_demo.tts.stream import stream as eleven_tts_stream
from eleven_demo.tts.sync import ApplyTextNormalization, synthesize
from eleven_demo.voices.catalog import list_pt_br_voices

# Injected once via ``Blocks.launch(head=...)`` so the Convai custom element upgrades. Gradio
# strips ``<script>`` tags from ``gr.HTML`` updates, which previously left the widget inert.
CONVAI_WIDGET_HEAD_HTML = (
    '<script src="https://unpkg.com/@elevenlabs/convai-widget-embed" async '
    'type="text/javascript"></script>'
)


def _repo_root() -> Path:
    """Project root (`apps/` parent)."""

    return Path(__file__).resolve().parents[1]


def _reload_env_and_settings() -> Settings:
    """Reload ``.env`` and drop cached settings and SDK client (long-lived Gradio process)."""

    load_dotenv(_repo_root() / ".env", override=True)
    get_settings.cache_clear()
    get_client.cache_clear()
    return get_settings()


def _scenario_markdown_or_stub(slug: str, fallback: str) -> str:
    """Load ``docs/scenarios/<slug>.md`` or fall back without failing the demo."""

    doc = _repo_root() / "docs" / "scenarios" / f"{slug}.md"
    if doc.is_file():
        return doc.read_text(encoding="utf-8")

    missing = html.escape(str(doc.relative_to(_repo_root())))
    return (
        f"Scenario copy is not on disk (`{missing}`). Add it under `docs/scenarios/`, "
        "or see `engineering/tasks/tasks-prd-elevenlabs-vertical-exploration.md`.\n\n---\n\n"
        + fallback
    )


def _convai_shell_intro_html(kind: Literal["telecom", "banking", "healthcare"]) -> str:
    if kind == "telecom":
        label = "<strong>Telecom</strong> (SAC demo)"
    elif kind == "banking":
        label = "<strong>Banking</strong> (digital banking demo)"
    else:
        label = "<strong>Healthcare</strong> (triage + KB/RAG)"
    return (
        '<div class="demo-convai-shell demo-convai-shell--muted" aria-live="polite">'
        f"<p>{label} tab: click <em>Start session</em> to load the ElevenLabs widget "
        "with a <strong>signed URL</strong> (private session).</p>"
        "<p>The raw <code>agent_id</code> is not sent to the browser; "
        "only the encapsulated URL is.</p>"
        "</div>"
    )


def _healthcare_rag_sources_markdown() -> str:
    """List RAG/KB document identifiers from ``scenarios.healthcare.SCENARIO.kb_doc_ids``.

    When the process has not provisioned Healthcare yet, ``kb_doc_ids`` may be empty; the panel
    still names the bundled seed filenames under ``data/kb/healthcare/``.
    """

    hc = healthcare_scenario
    footer = (
        "\n\n_RAG runs on the ElevenLabs platform; this panel lists indexed documents "
        "attached to the agent (`SCENARIO.kb_doc_ids`)._"
    )

    try:
        kb_ids = list(hc.SCENARIO.kb_doc_ids)
    except ValueError:
        seeds = "".join(f"- `{name}`\n" for name in hc.HEALTHCARE_KB_FILENAMES)
        return (
            "#### Source documents (KB / RAG)\n\n"
            "Set **`DEFAULT_PT_VOICE_ID`** in `.env` so the scenario can resolve. "
            "IDs appear after `uv run python scripts/agent_create.py healthcare`.\n\n"
            "**Versioned seeds** (`data/kb/healthcare/`):\n"
            f"{seeds}"
            f"{footer}"
        )

    if not kb_ids:
        seeds = "".join(f"- `{name}`\n" for name in hc.HEALTHCARE_KB_FILENAMES)
        return (
            "#### Source documents (KB / RAG)\n\n"
            "**No document IDs in this Python process yet.** Provision to populate "
            "`SCENARIO.kb_doc_ids`:\n\n"
            "`uv run python scripts/agent_create.py healthcare`\n\n"
            "**Expected seeds:**\n"
            f"{seeds}"
            f"{footer}"
        )

    lines: list[str] = [
        "#### Source documents (KB / RAG)",
        "",
        "Knowledge-base documents indexed and available to this agent:",
        "",
    ]
    names = hc.HEALTHCARE_KB_FILENAMES
    if len(kb_ids) == len(names):
        for fname, doc_id in zip(names, kb_ids, strict=True):
            disp = doc_id if len(doc_id) <= 36 else f"{doc_id[:33]}..."
            lines.append(f"- `{fname}` -> `{disp}`")
    else:
        lines.append("_Count differs from the seed list — listing IDs only:_")
        lines.append("")
        for idx, doc_id in enumerate(kb_ids, start=1):
            disp = doc_id if len(doc_id) <= 40 else f"{doc_id[:37]}..."
            lines.append(f"- {idx}. `{disp}`")

    return "\n".join(lines) + footer


def _convai_missing_agent_html(env_key: str) -> str:
    esc = html.escape(env_key)
    return (
        '<div class="demo-convai-shell demo-convai-shell--muted" role="alert">'
        "<p><strong>Agent id not configured.</strong> Add this variable to <code>.env</code> "
        "at the repository root, then click <em>Start session</em> again (no restart needed):</p>"
        f"<pre><code>{esc}</code></pre>"
        "<p>Provision and persist ids: "
        "<code>uv run python scripts/demo_prepare.py</code> "
        "or run <code>uv run python scripts/agent_create.py telecom</code> (etc.) and paste "
        "the printed id into <code>.env</code>.</p>"
        "</div>"
    )


def _convai_sdk_error_html(message: str) -> str:
    esc = html.escape(message, quote=False)
    return (
        '<div class="demo-convai-shell demo-convai-shell--warn" role="alert">'
        f"<p>Could not obtain the signed URL.</p><p>{esc}</p>"
        "</div>"
    )


def _convai_signed_embed(signed_url: str) -> str:
    escaped = html.escape(signed_url, quote=True)
    return (
        '<div class="demo-convai-shell">'
        f'<elevenlabs-convai signed-url="{escaped}"></elevenlabs-convai>'
        "</div>"
    )


def _start_agent_voice_surface(agent_id: str | None, *, env_key_name: str) -> tuple[str, str]:
    """Mint a signed URL and return widget HTML plus a short Markdown status."""

    if not agent_id or not agent_id.strip():
        return _convai_missing_agent_html(env_key_name), (
            "**Configuration pending.** Set the environment variable in `.env`; "
            "`scripts/agent_create.py` prints an `agent_id` after provisioning."
        )

    try:
        client = get_client()
        signed = client.conversational_ai.conversations.get_signed_url(
            agent_id=agent_id.strip(),
        )
    except ApiError as exc:
        body = exc.body
        detail = f"HTTP {exc.status_code}"
        if body is not None:
            detail = f"{detail} — `{body}`"
        return _convai_sdk_error_html(detail), (
            "**ElevenLabs API error.** See the message beside this panel or "
            "Agent Testing for details."
        )
    except OSError as exc:
        return _convai_sdk_error_html(str(exc)), (
            "**Network or I/O error** while calling the ElevenLabs API. Check connectivity."
        )
    except Exception as exc:
        return _convai_sdk_error_html(f"{type(exc).__name__}: {exc}"), (
            "**Unexpected error** while minting the signed URL. Check the server terminal for "
            "a traceback."
        )

    return _convai_signed_embed(signed.signed_url.strip()), (
        "**Private session started.** The widget loads only the signed URL "
        "(never log raw signed URLs)."
    )


DEMO_CSS = """
:root {
  --demo-bg: #f7f7f4;
  --demo-surface: #ffffff;
  --demo-surface-muted: #f1f2ef;
  --demo-text: #111111;
  --demo-text-muted: #5f6368;
  --demo-border: #deded8;
  --agents-accent: #2f6df6;
  --agents-accent-soft: #e8f0ff;
  --agents-orb-start: #2f6df6;
  --agents-orb-end: #8fb4ff;
  --api-accent: #111111;
  --api-accent-soft: #eeeeea;
  --success: #168a4a;
  --warning: #b7791f;
  --danger: #c2413a;
}
/* Gradio 6: dark tokens on :root.dark or .dark wrapper (gradio.themes.base). */
:root.dark,
:root .dark {
  --demo-bg: #0e0e0c;
  --demo-surface: #171716;
  --demo-surface-muted: #21211e;
  --demo-text: #ecece8;
  --demo-text-muted: #9b9d96;
  --demo-border: #3a3a34;
  --agents-accent: #6a9eff;
  --agents-accent-soft: #1a2438;
  --agents-orb-start: #6a9eff;
  --agents-orb-end: #a8c4ff;
  --api-accent: #ecece8;
  --api-accent-soft: #262624;
  --success: #3ecf8e;
  --warning: #e0b04a;
  --danger: #f07167;
}
:root.dark .demo-chip--ok,
:root .dark .demo-chip--ok {
  border-color: color-mix(in srgb, var(--success) 40%, var(--demo-border));
  background: color-mix(in srgb, var(--success) 22%, var(--demo-surface-muted));
  color: #d4f5e6 !important;
}
:root.dark .demo-chip--warn,
:root .dark .demo-chip--warn {
  border-color: color-mix(in srgb, var(--warning) 40%, var(--demo-border));
  background: color-mix(in srgb, var(--warning) 22%, var(--demo-surface-muted));
  color: #fcecc0 !important;
}
.gradio-container {
  background: linear-gradient(
    to bottom,
    var(--demo-bg) 0%,
    var(--demo-surface-muted) 100%
  ) !important;
  color: var(--demo-text) !important;
}
.demo-landing-card {
  background: var(--demo-surface);
  border: 1px solid var(--demo-border);
  border-radius: 12px;
  padding: 1.25rem 1.5rem;
  margin-bottom: 1rem;
}
.demo-landing-headline {
  font-size: 1.35rem;
  font-weight: 600;
  margin: 0 0 0.35rem 0;
  color: var(--demo-text);
}
.demo-landing-sub {
  margin: 0 0 0.75rem 0;
  color: var(--demo-text-muted);
  font-size: 0.95rem;
  line-height: 1.5;
}
.demo-chip-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin: 0.75rem 0;
}
.demo-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.35rem 0.65rem;
  border-radius: 999px;
  font-size: 0.82rem;
  border: 1px solid var(--demo-border);
  background: var(--demo-surface-muted);
  color: var(--demo-text) !important;
}
.demo-chip svg {
  flex-shrink: 0;
  width: 0.55rem;
  height: 0.55rem;
  border-radius: 50%;
  display: inline-block;
}
.demo-chip--ok {
  border-color: color-mix(in srgb, var(--success) 45%, var(--demo-border));
  background: color-mix(in srgb, var(--success) 14%, white);
  color: #052e1c !important;
}
.demo-chip--warn {
  border-color: color-mix(in srgb, var(--warning) 45%, var(--demo-border));
  background: color-mix(in srgb, var(--warning) 16%, white);
  color: #4a3200 !important;
}
.demo-chip--muted {
  border-color: var(--demo-border);
  color: var(--demo-text-muted) !important;
}
.demo-legal-note {
  font-size: 0.8rem;
  color: var(--demo-text-muted);
  margin-top: 0.5rem;
}
.demo-column-heading {
  font-size: 0.85rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--demo-text-muted);
  margin-bottom: 0.5rem;
}
.tab-panel-agents .demo-column-heading {
  color: var(--agents-accent);
}
.tab-panel-agents .demo-panel-well {
  background: linear-gradient(145deg, var(--agents-accent-soft) 0%, var(--demo-surface) 72%);
}
.tab-panel-api .demo-column-heading {
  color: var(--api-accent);
}
.tab-panel-api .demo-panel-well {
  background: linear-gradient(180deg, var(--api-accent-soft) 0%, var(--demo-surface) 56%);
}
.demo-panel-well {
  border: 1px solid var(--demo-border);
  border-radius: 10px;
  padding: 0.85rem;
  min-height: 140px;
}
.demo-convai-shell {
  min-height: 360px;
  border: 1px dashed var(--demo-border);
  border-radius: 10px;
  padding: 0.85rem;
  margin-bottom: 0.85rem;
  background: var(--demo-surface);
}
.demo-convai-shell--muted {
  background: var(--demo-surface-muted);
}
.demo-convai-shell--warn {
  border-color: color-mix(in srgb, var(--danger) 45%, transparent);
  background: color-mix(in srgb, var(--danger) 6%, white);
}
.demo-convai-shell pre {
  margin: 0.5rem 0 0 0;
  font-size: 0.82rem;
  overflow-x: auto;
}
/* Compact primary tab row — Gradio 5 sends overflow tabs to a "⋯" menu; shorter labels + denser
   buttons keep six tabs visible on typical laptop widths without hiding Benchmark. */
.gradio-container [role="tablist"] {
  flex-wrap: wrap;
  row-gap: 0.2rem;
  column-gap: 0.15rem;
}
.gradio-container [role="tablist"] button[role="tab"] {
  font-size: 0.78rem;
  padding: 0.38rem 0.55rem;
  line-height: 1.15;
}
.demo-benchmark-placeholder {
  margin: 0;
  font-size: 0.88rem;
  color: var(--demo-text-muted);
}
.demo-benchmark-callout {
  border-radius: 10px;
  padding: 0.75rem 0.95rem;
  margin: 0 0 0.65rem 0;
  border: 1px solid var(--demo-border);
  background: var(--demo-surface-muted);
  font-size: 0.92rem;
  line-height: 1.45;
}
.demo-benchmark-callout p {
  margin: 0 0 0.45rem 0;
}
.demo-benchmark-callout p:last-child {
  margin-bottom: 0;
}
.demo-benchmark-callout-kicker {
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--demo-text-muted);
  margin-bottom: 0.35rem !important;
}
.demo-benchmark-callout-detail {
  font-size: 0.82rem;
  color: var(--demo-text-muted);
}
.demo-benchmark-callout-metric {
  display: block;
  margin-top: 0.5rem;
  font-size: 0.72rem;
  color: var(--demo-text-muted);
  line-height: 1.35;
}
.demo-benchmark-callout--elevenlabs-lead {
  border-color: color-mix(in srgb, var(--success) 45%, var(--demo-border));
  background: color-mix(in srgb, var(--success) 16%, var(--demo-surface));
  box-shadow: 0 0 0 1px color-mix(in srgb, var(--success) 25%, transparent);
}
.demo-benchmark-callout--elevenlabs-lead .demo-benchmark-callout-kicker {
  color: color-mix(in srgb, var(--success) 90%, var(--demo-text-muted));
}
:root.dark .demo-benchmark-callout--elevenlabs-lead,
:root .dark .demo-benchmark-callout--elevenlabs-lead {
  background: color-mix(in srgb, var(--success) 14%, var(--demo-surface-muted));
}
.demo-benchmark-callout--openai-lead {
  border-color: color-mix(in srgb, var(--warning) 45%, var(--demo-border));
  background: color-mix(in srgb, var(--warning) 12%, var(--demo-surface));
}
:root.dark .demo-benchmark-callout--openai-lead,
:root .dark .demo-benchmark-callout--openai-lead {
  background: color-mix(in srgb, var(--warning) 12%, var(--demo-surface-muted));
}
.demo-benchmark-callout--tie {
  border-style: dashed;
}
.demo-benchmark-callout--muted {
  border-color: var(--demo-border);
  background: var(--demo-surface-muted);
  font-size: 0.88rem;
}
"""

TTS_OUTPUT_FORMAT_CHOICES = ["mp3_22050_32", "mp3_44100_128", "pcm_16000", "ulaw_8000"]
TTS_MODEL_CHOICES = ["eleven_flash_v2_5", "eleven_multilingual_v2", "eleven_v3"]

LATENCY_MODEL_PRESETS: dict[str, str] = {
    "flash": "eleven_flash_v2_5",
    "multilingual": "eleven_multilingual_v2",
}


def _latency_json_float(x: float) -> float | None:
    """Serialize aggregate for JSON (``math.nan`` becomes ``None``)."""

    if isinstance(x, float) and math.isnan(x):
        return None
    return float(x)


def _run_latency_benchmark(
    model_preset: str,
    n_runs: float,
    text: str,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    """Stream TTS ``n`` times; record TTFB per run for :class:`LatencyReport` + charts."""

    settings = get_settings()
    empty = pd.DataFrame({"run": [], "ttfb_ms": []})

    def _latency_error_payload(msg: str) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
        payload: dict[str, Any] = {
            "error": msg,
            "median": None,
            "p95": None,
            "mean": None,
            "unit": "seconds",
            "n": 0,
        }
        return empty, empty, payload

    voice_id = (settings.default_pt_voice_id or "").strip()
    n = max(1, min(20, int(n_runs)))
    stripped = (text or "").strip()
    if not stripped:
        return _latency_error_payload("Enter non-empty text to measure TTFB.")

    if not voice_id:
        return _latency_error_payload(
            "Set DEFAULT_PT_VOICE_ID in `.env` (same voice list as TTS Playground).",
        )

    model_id = LATENCY_MODEL_PRESETS.get(model_preset, LATENCY_MODEL_PRESETS["flash"])
    report = LatencyReport()
    rows: list[dict[str, Any]] = []

    try:
        for i in range(n):
            total_bytes = 0
            ttfb_seconds: float | None = None
            for chunk, tag in eleven_tts_stream(
                stripped,
                voice_id=voice_id,
                model_id=model_id,
                output_format=settings.tts_output_format,
            ):
                total_bytes += len(chunk)
                if tag is not None:
                    ttfb_seconds = tag
            if ttfb_seconds is None:
                return _latency_error_payload(
                    "Stream ended before the first audio chunk (empty response).",
                )
            report.samples.append(ttfb_seconds)
            rows.append(
                {
                    "run": i + 1,
                    "ttfb_ms": float(ttfb_seconds * 1000.0),
                    "total_bytes": total_bytes,
                }
            )
    except ApiError as exc:
        detail = f"HTTP {exc.status_code}"
        if exc.body is not None:
            detail = f"{detail} — {exc.body!r}"
        return _latency_error_payload(f"TTS stream failed: {detail}")

    df = pd.DataFrame(rows)
    plot_df = df[["run", "ttfb_ms"]].copy()
    summary: dict[str, Any] = {
        "median": _latency_json_float(report.median),
        "p95": _latency_json_float(report.p95),
        "mean": _latency_json_float(report.mean),
        "unit": "seconds",
        "n": report.count,
        "model_id": model_id,
    }
    return plot_df, df, summary


VENDOR_METHODOLOGY_MD = (
    "**Methodology (local TTFB)**\n\n"
    "Time-to-first-byte is measured **on this machine** (`perf_counter`) when the "
    "first audio chunk reaches the client. Latency depends on network, region, load, and "
    "SDK versions — use this as a **relative**, repeatable check, not an official ranking "
    "between ElevenLabs and OpenAI."
)

VENDOR_BANNER_INITIAL = (
    '<p class="demo-benchmark-placeholder">Run the benchmark to see who leads on '
    "<strong>median TTFB</strong> (first audio chunk) for this machine.</p>"
)


def _vendor_benchmark_banner_html(comparison: dict[str, Any] | None) -> str:
    """Highlighted outcome strip for the vendor benchmark tab (HTML inside Markdown)."""

    if comparison is None:
        return VENDOR_BANNER_INITIAL

    outcome = comparison.get("outcome")
    metric_note = (
        '<span class="demo-benchmark-callout-metric">Metric: median streaming TTFB · '
        "lower is faster · single-machine snapshot</span>"
    )

    if outcome == "insufficient_data":
        return (
            '<div class="demo-benchmark-callout demo-benchmark-callout--muted" role="status">'
            "<p><strong>Comparison unavailable.</strong> Need valid median TTFB for both "
            "providers.</p>"
            f"{metric_note}"
            "</div>"
        )

    if outcome == "tie":
        el = comparison.get("elevenlabs_median_ms")
        oa = comparison.get("openai_median_ms")
        return (
            '<div class="demo-benchmark-callout demo-benchmark-callout--tie" role="status">'
            "<p><strong>Tie on median TTFB</strong> (within rounding): ElevenLabs "
            f"{float(el):.1f} ms · OpenAI {float(oa):.1f} ms.</p>"
            f"{metric_note}"
            "</div>"
        )

    if outcome == "elevenlabs_faster":
        margin_ms = float(comparison["margin_ms"])
        el = float(comparison["elevenlabs_median_ms"])
        oa = float(comparison["openai_median_ms"])
        pct = comparison.get("margin_pct_vs_slower")
        pct_html = f" (~{float(pct):.1f}% lower median vs OpenAI)" if pct is not None else ""
        return (
            '<div class="demo-benchmark-callout demo-benchmark-callout--elevenlabs-lead" '
            'role="status">'
            '<p class="demo-benchmark-callout-kicker">This run — faster first audio</p>'
            "<p><strong>ElevenLabs leads</strong> on median TTFB vs OpenAI by "
            f"<strong>{margin_ms:.1f} ms</strong>{pct_html}.</p>"
            '<p class="demo-benchmark-callout-detail">Median TTFB: ElevenLabs '
            f"{el:.1f} ms · OpenAI {oa:.1f} ms</p>"
            f"{metric_note}"
            "</div>"
        )

    if outcome == "openai_faster":
        margin_ms = float(comparison["margin_ms"])
        el = float(comparison["elevenlabs_median_ms"])
        oa = float(comparison["openai_median_ms"])
        pct = comparison.get("margin_pct_vs_slower")
        pct_html = f" (~{float(pct):.1f}% lower median vs ElevenLabs)" if pct is not None else ""
        return (
            '<div class="demo-benchmark-callout demo-benchmark-callout--openai-lead" '
            'role="status">'
            '<p class="demo-benchmark-callout-kicker">This run — faster first audio</p>'
            "<p><strong>OpenAI leads</strong> on median TTFB vs ElevenLabs by "
            f"<strong>{margin_ms:.1f} ms</strong>{pct_html}. Try another network window or "
            "review methodology below.</p>"
            '<p class="demo-benchmark-callout-detail">Median TTFB: ElevenLabs '
            f"{el:.1f} ms · OpenAI {oa:.1f} ms</p>"
            f"{metric_note}"
            "</div>"
        )

    return VENDOR_BANNER_INITIAL


def _vendor_error_banner_html(message: str) -> str:
    esc = html.escape(message, quote=False)
    return (
        f'<div class="demo-benchmark-callout demo-benchmark-callout--muted" role="alert">'
        f"<p>{esc}</p></div>"
    )


def _vendor_empty_runs_df() -> pd.DataFrame:
    """Table schema used when no benchmark ran or prerequisites are missing."""

    return pd.DataFrame(
        columns=["leg", "provider", "text_id", "ttfb_ms", "total_ms", "byte_count", "model_id"],
    )


def _vendor_nan_to_none(val: float) -> float | None:
    if isinstance(val, float) and math.isnan(val):
        return None
    return float(val)


def _vendor_report_to_summary_json(report: VendorBenchmarkReport) -> dict[str, Any]:
    """JSON-safe summary dict (no NaN floats) for ``gr.JSON``."""

    summaries: list[dict[str, Any]] = []
    for s in report.summaries:
        summaries.append(
            {
                "provider": s.provider,
                "median_ttfb_ms": _vendor_nan_to_none(s.median_ttfb_ms),
                "p95_ttfb_ms": _vendor_nan_to_none(s.p95_ttfb_ms),
                "mean_ttfb_ms": _vendor_nan_to_none(s.mean_ttfb_ms),
                "median_total_ms": _vendor_nan_to_none(s.median_total_ms),
                "sample_count": int(s.sample_count),
            },
        )
    base: dict[str, Any] = {
        "hypothesis": report.hypothesis,
        "caveats": report.caveats,
        "summaries": summaries,
        "runs_recorded": len(report.runs),
        "comparison": comparison_from_vendor_report(report),
    }
    return base


def _vendor_runs_to_dataframe(report: VendorBenchmarkReport) -> pd.DataFrame:
    rows = [
        {
            "leg": i + 1,
            "provider": r.provider,
            "text_id": r.text_id,
            "ttfb_ms": float(r.ttfb_ms),
            "total_ms": float(r.total_ms),
            "byte_count": int(r.byte_count),
            "model_id": r.model_id,
        }
        for i, r in enumerate(report.runs)
    ]
    if not rows:
        return _vendor_empty_runs_df()
    return pd.DataFrame(rows)


def _vendor_initial_hint(settings: Settings) -> str:
    """Readiness copy for the vendor tab (shown before Run)."""

    lines = [
        "**Prerequisites** — without these the action only returns structured errors in JSON:",
        "",
    ]
    oa = settings.openai_api_key
    if oa is None or not oa.get_secret_value().strip():
        lines.append("- `OPENAI_API_KEY` not set — add it to `.env` (see `.env.example`).")
    else:
        lines.append("- `OPENAI_API_KEY`: OK.")

    vid = settings.default_pt_voice_id
    if not vid:
        lines.append("- `DEFAULT_PT_VOICE_ID`: required for the ElevenLabs benchmark leg.")
    else:
        lines.append("- `DEFAULT_PT_VOICE_ID`: OK.")

    lines.append("")
    lines.append(
        "*ElevenLabs Flash (model from `tts_model_id` / `.env`) and OpenAI "
        "`gpt-4o-mini-tts` are the current benchmark defaults.*"
    )
    return "\n".join(lines)


def _run_vendor_benchmark_ui(  # noqa: PLR0911
    n_runs: float,
    text_set_key: str,
    openai_response_format: str,
) -> tuple[pd.DataFrame, dict[str, Any], str, str]:
    """Wrapper around :func:`run_vendor_benchmark` for Gradio outputs."""

    settings = get_settings()
    empty_df = _vendor_empty_runs_df()
    n = max(1, min(10, int(n_runs)))

    oa = settings.openai_api_key
    if oa is None or not oa.get_secret_value().strip():
        return (
            empty_df,
            {
                "error": "OPENAI_API_KEY missing",
                "setup": "Add OPENAI_API_KEY to `.env` (see `.env.example`).",
            },
            _vendor_error_banner_html(
                "Add OPENAI_API_KEY to compare providers — headline result appears here after a "
                "successful run.",
            ),
            f"{VENDOR_METHODOLOGY_MD}\n\n---\n\n**Status:** OpenAI API key missing — "
            "the benchmark will not call OpenAI until you set the variable.",
        )

    if not (settings.default_pt_voice_id or "").strip():
        return (
            empty_df,
            {
                "error": "DEFAULT_PT_VOICE_ID missing",
                "setup": "Set DEFAULT_PT_VOICE_ID for the ElevenLabs benchmark leg.",
            },
            _vendor_error_banner_html(
                "Set DEFAULT_PT_VOICE_ID so the ElevenLabs streaming leg can run.",
            ),
            f"{VENDOR_METHODOLOGY_MD}\n\n---\n\n**Status:** set `DEFAULT_PT_VOICE_ID` "
            "for the ElevenLabs benchmark leg.",
        )

    texts_tuple = VENDOR_CANONICAL_TEXT_SETS.get(text_set_key)
    if not texts_tuple:
        return (
            empty_df,
            {"error": f"Unknown text set: {text_set_key!r}"},
            _vendor_error_banner_html(f"Unknown text set {text_set_key!r}."),
            VENDOR_METHODOLOGY_MD,
        )
    texts = list(texts_tuple)

    try:
        report = run_vendor_benchmark(
            texts,
            n,
            openai_response_format=openai_response_format,
        )
    except (ValueError, RuntimeError) as exc:
        return (
            empty_df,
            {"error": str(exc)},
            _vendor_error_banner_html(str(exc)),
            f"{VENDOR_METHODOLOGY_MD}\n\n---\n\n**Falha:** `{exc}`",
        )
    except ApiError as exc:
        detail = f"HTTP {exc.status_code}"
        if exc.body is not None:
            detail = f"{detail} — {exc.body!r}"
        return (
            empty_df,
            {"error": "ElevenLabs API error", "detail": detail},
            _vendor_error_banner_html(f"ElevenLabs API error: {detail}"),
            f"{VENDOR_METHODOLOGY_MD}\n\n---\n\n**Falha ElevenAPI:** {detail}",
        )
    except Exception as exc:
        return (
            empty_df,
            {"error": "Vendor benchmark failed", "detail": str(exc)},
            _vendor_error_banner_html(str(exc)),
            f"{VENDOR_METHODOLOGY_MD}\n\n---\n\n**Falha:** `{exc}`",
        )

    df = _vendor_runs_to_dataframe(report)
    summary = _vendor_report_to_summary_json(report)
    banner = _vendor_benchmark_banner_html(summary["comparison"])
    return df, summary, banner, VENDOR_METHODOLOGY_MD


def _file_suffix_for_tts_format(output_format: str) -> str:
    """Pick a tempfile suffix hint for the synthesized payload."""

    if output_format.startswith("mp3"):
        return ".mp3"
    if output_format.startswith("pcm"):
        return ".pcm"
    if "ulaw" in output_format:
        return ".raw"
    return ".bin"


def _tts_playback_caveat(output_format: str) -> str:
    """Warn when HTML5 playback is unlikely (telephony / raw PCM)."""

    if output_format.startswith("mp3"):
        return ""
    return (
        f"**Playback note:** `{output_format}` is not MP3. The player may stay silent even when "
        "synthesis succeeds — use telephony codecs (e.g. Twilio/SIP) or offline decoding."
    )


def _pt_br_voice_dropdown(settings: Settings) -> tuple[list[tuple[str, str]], str]:
    """Build ElevenAPI Library labels and a sane default voice id."""

    try:
        cards = list_pt_br_voices()
    except ApiError:
        fb = settings.default_pt_voice_id
        if fb:
            return [(f"Voice list unavailable — using DEFAULT_PT_VOICE_ID ({fb[:8]}…)", fb)], fb
        return [("Voice list unavailable — set DEFAULT_PT_VOICE_ID in `.env`", "")], ""

    fb = settings.default_pt_voice_id
    if not cards:
        if fb:
            return [(f"Fallback · DEFAULT_PT_VOICE_ID ({fb[:8]}…)", fb)], fb
        return [("No PT-BR-matched voices in this page — set DEFAULT_PT_VOICE_ID", "")], ""

    pairs = [(f"{c.name} · {c.voice_id}", c.voice_id) for c in cards]
    if fb and any(c.voice_id == fb for c in cards):
        return pairs, fb
    return pairs, cards[0].voice_id


def _normalize_tts_radio(value: str) -> ApplyTextNormalization:
    if value in {"on", "off"}:
        return cast(ApplyTextNormalization, value)
    return "auto"


def _run_tts_playground(
    text: str,
    voice_id: str,
    stability: float,
    similarity_boost: float,
    style: float,
    use_speaker_boost: bool,
    output_format: str,
    apply_text_normalization: str,
    model_id: str,
) -> tuple[str | None, dict[str, Any], str]:
    """Synthesize speech and persist bytes to a temp file for ``gr.Audio``."""

    caveat = _tts_playback_caveat(output_format)
    stripped = (text or "").strip()
    if not stripped:
        return None, {"error": "Enter some text to synthesize."}, caveat

    vid = (voice_id or "").strip()
    if not vid:
        return (
            None,
            {"error": "Pick a voice or configure DEFAULT_PT_VOICE_ID in `.env`."},
            caveat,
        )

    voice_settings: dict[str, Any] = {
        "stability": float(stability),
        "similarity_boost": float(similarity_boost),
        "style": float(style),
        "use_speaker_boost": bool(use_speaker_boost),
    }
    norm = _normalize_tts_radio(apply_text_normalization)

    try:
        audio, meta = synthesize(
            stripped,
            voice_id=vid,
            model_id=model_id,
            output_format=output_format,
            voice_settings=voice_settings,
            apply_text_normalization=norm,
        )
    except ApiError as exc:
        err: dict[str, Any] = {
            "error": "ElevenAPI TTS request failed",
            "status_code": exc.status_code,
        }
        if exc.body is not None:
            err["body"] = exc.body
        return None, err, caveat

    suffix = _file_suffix_for_tts_format(output_format)
    fd, path = tempfile.mkstemp(prefix="eleven-tts-", suffix=suffix)
    try:
        os.write(fd, audio)
    finally:
        os.close(fd)

    merged: dict[str, Any] = {**meta, "audio_byte_length": len(audio)}
    return path, merged, caveat


def _agents_configured(settings: Settings) -> tuple[int, int]:
    """Return (configured_count, total) for demo ElevenAgents IDs."""

    ids = (
        settings.demo_agent_id_telecom,
        settings.demo_agent_id_banking,
        settings.demo_agent_id_healthcare,
    )
    n_ok = sum(1 for x in ids if x)
    return n_ok, len(ids)


def _readiness_chips_html(settings: Settings) -> str:
    """Return status chips HTML for the landing card."""

    openai_present = settings.openai_api_key is not None
    configured, total = _agents_configured(settings)
    if configured == total:
        agent_chip = (
            '<span class="demo-chip demo-chip--ok"> ElevenAgents demo IDs: configured (3/3)</span>'
        )
    elif configured == 0:
        agent_chip = (
            '<span class="demo-chip demo-chip--warn"'
            "> ElevenAgents demo IDs: pending — set DEMO_AGENT_ID_*</span>"
        )
    else:
        agent_chip = (
            '<span class="demo-chip demo-chip--warn"'
            f"> ElevenAgents demo IDs: partial ({configured}/{total})</span>"
        )

    openai_inner = (
        "OpenAI key: OK — vendor benchmark usable"
        if openai_present
        else (
            "OpenAI key: missing — optional; required only for Vendor Benchmark "
            '<span aria-hidden="true">vs</span> ElevenAPI comparisons'
        )
    )
    openai_class = "demo-chip demo-chip--ok" if openai_present else "demo-chip demo-chip--muted"

    chips_md = (
        '<div class="demo-chip-row">'
        '<span class="demo-chip demo-chip--ok"><span aria-hidden="true"></span>'
        " ElevenLabs API key: OK</span>"
        f'<span class="{openai_class}">{openai_inner}</span>'
        f"{agent_chip}"
        "</div>"
    )

    return chips_md


def build_demo() -> gr.Blocks:  # noqa: PLR0915
    """Construct the Gradio playground (TTS, three agent verticals, latency, vendor benchmark).

    Call ``launch(theme=..., css=...)`` (see module ``__main__`` block) — recent Gradio places
    ``theme`` and ``css`` on ``launch()`` rather than on ``Blocks()``.
    """

    load_dotenv(_repo_root() / ".env", override=True)
    settings = get_settings()
    chips_html = _readiness_chips_html(settings)

    with gr.Blocks(
        title="ElevenLabs Vertical Exploration",
    ) as demo:
        gr.HTML(
            f"""
<section class="demo-landing-card" aria-label="Demo overview">
<h1 class="demo-landing-headline">ElevenLabs Vertical Exploration</h1>
<p class="demo-landing-sub">
  Local product/engineering playground for ElevenAPI (streaming TTFB and voice synthesis) and
  ElevenAgents (multi-vertical SAC-style voice demos). Intended for demos on your machine, not as
  a hosted product surface.
</p>
<div>{chips_html}</div>
<p class="demo-legal-note">
  Brand-inspired visuals only — this demo is not an official ElevenLabs application.
</p>
</section>
"""
        )

        tab_names = (
            "TTS Playground",
            "Telecom",
            "Banking",
            "Health + RAG",
            "Latency",
            "Benchmark",
        )

        why_blocks: list[tuple[str, str]] = [
            (
                "_eleven_api",
                (
                    "ElevenAPI — exercised through the SDK: pick a PT-BR voice, steer "
                    "stability/style, and hear output with reproducible billing metadata."
                ),
            ),
            (
                "_eleven_agents",
                (
                    "ElevenAgents — telecom SAC assistant with lookup and human "
                    "handoff; browser voice uses a signed conversation URL."
                ),
            ),
            (
                "_eleven_agents",
                (
                    "ElevenAgents — authenticate before mocked account tools; "
                    "Zero Retention posture lives in provisioning configuration."
                ),
            ),
            (
                "_eleven_agents",
                (
                    "ElevenAgents + KB — triage prompts against seeded docs with RAG index "
                    "diagnostics on the ElevenLabs side."
                ),
            ),
            (
                "_eleven_api",
                (
                    "ElevenAPI — stream Flash or Multilingual; measure first-byte latency across "
                    "runs (median/p95)."
                ),
            ),
            (
                "_eleven_api",
                (
                    "ElevenLabs Flash v2.5 vs OpenAI speech models — see methodology in "
                    "`docs/benchmarks/tts-vendor-comparison.md`."
                ),
            ),
        ]

        telecom_scenario_md = _scenario_markdown_or_stub("telecom", why_blocks[1][1])
        banking_scenario_md = _scenario_markdown_or_stub("banking", why_blocks[2][1])
        healthcare_scenario_md = _scenario_markdown_or_stub("healthcare", why_blocks[3][1])

        def start_telecom_voice() -> tuple[str, str]:
            s = _reload_env_and_settings()
            return _start_agent_voice_surface(
                s.demo_agent_id_telecom,
                env_key_name="DEMO_AGENT_ID_TELECOM",
            )

        def start_banking_voice() -> tuple[str, str]:
            s = _reload_env_and_settings()
            return _start_agent_voice_surface(
                s.demo_agent_id_banking,
                env_key_name="DEMO_AGENT_ID_BANKING",
            )

        def start_healthcare_voice() -> tuple[str, str, str]:
            s = _reload_env_and_settings()
            html_out, status = _start_agent_voice_surface(
                s.demo_agent_id_healthcare,
                env_key_name="DEMO_AGENT_ID_HEALTHCARE",
            )
            return html_out, status, _healthcare_rag_sources_markdown()

        voice_choice_pairs, voice_default = _pt_br_voice_dropdown(settings)
        model_choices = list(TTS_MODEL_CHOICES)
        if settings.tts_model_id and settings.tts_model_id not in model_choices:
            model_choices.insert(0, settings.tts_model_id)
        model_default = (
            settings.tts_model_id if settings.tts_model_id in model_choices else model_choices[0]
        )

        _tts_kind, tts_why = why_blocks[0]
        with gr.Tab(tab_names[0]), gr.Column(elem_classes=["tab-panel-api"]), gr.Row():
            with gr.Column(scale=1):
                gr.Markdown('<p class="demo-column-heading">Controls</p>')
                tts_text = gr.Textbox(
                    label="Text",
                    lines=6,
                    value="Hello — this is a synthetic ElevenAPI demo string (try PT-BR too).",
                    placeholder="Type or paste narration to synthesize.",
                )
                tts_voice = gr.Dropdown(
                    label="Voice (Voice Library · PT-BR heuristic)",
                    choices=voice_choice_pairs,
                    value=voice_default if voice_default else voice_choice_pairs[0][1],
                )
                tts_stability = gr.Slider(
                    minimum=0.0,
                    maximum=1.0,
                    value=0.4,
                    step=0.01,
                    label="Stability",
                )
                tts_similarity = gr.Slider(
                    minimum=0.0,
                    maximum=1.0,
                    value=0.85,
                    step=0.01,
                    label="Similarity boost",
                )
                tts_style = gr.Slider(
                    minimum=0.0,
                    maximum=1.0,
                    value=0.4,
                    step=0.01,
                    label="Style",
                )
                tts_speaker_boost = gr.Checkbox(
                    value=True,
                    label="Use speaker boost",
                )
                tts_output_format = gr.Dropdown(
                    label="Output format",
                    choices=TTS_OUTPUT_FORMAT_CHOICES,
                    value="mp3_22050_32",
                )
                tts_norm = gr.Radio(
                    label="Apply text normalization (numbers / dates)",
                    choices=["auto", "on", "off"],
                    value="auto",
                )
                tts_model = gr.Dropdown(
                    label="TTS model",
                    choices=model_choices,
                    value=model_default,
                )
                tts_generate = gr.Button("Generate", variant="primary")

            with gr.Column(scale=1):
                gr.Markdown('<p class="demo-column-heading">Output</p>')
                tts_audio = gr.Audio(
                    label="Synthesized audio",
                    autoplay=True,
                    type="filepath",
                )
                tts_metadata = gr.JSON(label="Billing / trace metadata")
                tts_caveat_md = gr.Markdown()
                gr.Markdown("#### Why this matters")
                gr.Markdown(tts_why)

        tts_generate.click(
            fn=_run_tts_playground,
            inputs=[
                tts_text,
                tts_voice,
                tts_stability,
                tts_similarity,
                tts_style,
                tts_speaker_boost,
                tts_output_format,
                tts_norm,
                tts_model,
            ],
            outputs=[tts_audio, tts_metadata, tts_caveat_md],
        )

        with gr.Tab(tab_names[1]), gr.Column(elem_classes=["tab-panel-agents"]), gr.Row():
            with gr.Column(scale=1):
                gr.Markdown('<p class="demo-column-heading">Controls</p>')
                telecom_start_btn = gr.Button("Start session", variant="primary")
                gr.Markdown(
                    "ElevenAgents widget via "
                    "[`convai-widget-embed`](https://unpkg.com/@elevenlabs/convai-widget-embed), "
                    "`signed-url` attribute (private session). "
                    "[Widget customization]"
                    "(https://elevenlabs.io/docs/eleven-agents/customization/widget)."
                )
            with gr.Column(scale=1):
                gr.Markdown('<p class="demo-column-heading">Output</p>')
                telecom_widget = gr.HTML(value=_convai_shell_intro_html("telecom"))
                telecom_voice_status = gr.Markdown(value="")
                gr.Markdown("#### Scenario")
                gr.Markdown(telecom_scenario_md)

        telecom_start_btn.click(
            fn=start_telecom_voice,
            outputs=[telecom_widget, telecom_voice_status],
        )

        with gr.Tab(tab_names[2]), gr.Column(elem_classes=["tab-panel-agents"]), gr.Row():
            with gr.Column(scale=1):
                gr.Markdown('<p class="demo-column-heading">Controls</p>')
                banking_start_btn = gr.Button("Start session", variant="primary")
                gr.Markdown(
                    "Same signed-URL flow as Telecom; use the agent provisioned with "
                    "`scripts/agent_create.py banking`."
                )
            with gr.Column(scale=1):
                gr.Markdown('<p class="demo-column-heading">Output</p>')
                banking_widget = gr.HTML(value=_convai_shell_intro_html("banking"))
                banking_voice_status = gr.Markdown(value="")
                gr.Markdown("#### Scenario")
                gr.Markdown(banking_scenario_md)

        banking_start_btn.click(
            fn=start_banking_voice,
            outputs=[banking_widget, banking_voice_status],
        )

        with gr.Tab(tab_names[3]), gr.Column(elem_classes=["tab-panel-agents"]), gr.Row():
            with gr.Column(scale=1):
                gr.Markdown('<p class="demo-column-heading">Controls</p>')
                healthcare_start_btn = gr.Button("Start session", variant="primary")
                gr.Markdown(
                    "Same signed-URL flow; the Healthcare agent uses RAG over the documents "
                    "listed in the output column. [Widget customization]"
                    "(https://elevenlabs.io/docs/eleven-agents/customization/widget)."
                )
            with gr.Column(scale=1):
                gr.Markdown('<p class="demo-column-heading">Output</p>')
                healthcare_widget = gr.HTML(value=_convai_shell_intro_html("healthcare"))
                healthcare_voice_status = gr.Markdown(value="")
                healthcare_sources = gr.Markdown(value=_healthcare_rag_sources_markdown())
                gr.Markdown("#### Scenario")
                gr.Markdown(healthcare_scenario_md)

        healthcare_start_btn.click(
            fn=start_healthcare_voice,
            outputs=[healthcare_widget, healthcare_voice_status, healthcare_sources],
        )

        latency_why = why_blocks[4][1]
        with gr.Tab(tab_names[4]), gr.Column(elem_classes=["tab-panel-api"]), gr.Row():
            with gr.Column(scale=1):
                gr.Markdown('<p class="demo-column-heading">Controls</p>')
                latency_model = gr.Radio(
                    choices=["flash", "multilingual"],
                    value="flash",
                    label="Model preset",
                )
                latency_n = gr.Slider(
                    minimum=1,
                    maximum=20,
                    value=10,
                    step=1,
                    label="Runs (n)",
                )
                latency_text = gr.Textbox(
                    label="Text",
                    lines=4,
                    value="This is a latency demonstration string.",
                )
                latency_run = gr.Button("Run benchmark", variant="primary")

            with gr.Column(scale=1):
                gr.Markdown('<p class="demo-column-heading">Output</p>')
                latency_plot = gr.LinePlot(
                    label="TTFB per run",
                    x="run",
                    y="ttfb_ms",
                    x_title="Run",
                    y_title="TTFB (ms)",
                    height=320,
                )
                latency_samples = gr.DataFrame(
                    label="Raw samples",
                    headers=["run", "ttfb_ms", "total_bytes"],
                    wrap=True,
                )
                latency_summary = gr.JSON(label="Summary (median, p95, mean · seconds)")
                gr.Markdown("#### Why this matters")
                gr.Markdown(latency_why)

        latency_run.click(
            fn=_run_latency_benchmark,
            inputs=[latency_model, latency_n, latency_text],
            outputs=[latency_plot, latency_samples, latency_summary],
        )

        vendor_why = why_blocks[5][1]
        with gr.Tab(tab_names[5]), gr.Column(elem_classes=["tab-panel-api"]), gr.Row():
            with gr.Column(scale=1):
                gr.Markdown('<p class="demo-column-heading">Controls</p>')
                gr.Markdown(_vendor_initial_hint(settings))
                vendor_n = gr.Slider(
                    minimum=1,
                    maximum=10,
                    value=3,
                    step=1,
                    label="Runs (n)",
                )
                vendor_text_set = gr.Dropdown(
                    choices=list(VENDOR_CANONICAL_TEXT_SETS.keys()),
                    value="short-pt-br",
                    label="Text set",
                )
                vendor_openai_fmt = gr.Radio(
                    choices=["mp3", "pcm"],
                    value="mp3",
                    label="OpenAI response format",
                )
                vendor_run = gr.Button("Run vendor benchmark", variant="primary")

            with gr.Column(scale=1):
                gr.Markdown('<p class="demo-column-heading">Output</p>')
                vendor_outcome_banner = gr.Markdown(value=VENDOR_BANNER_INITIAL)
                vendor_runs_df = gr.DataFrame(
                    label="Raw runs",
                    headers=[
                        "leg",
                        "provider",
                        "text_id",
                        "ttfb_ms",
                        "total_ms",
                        "byte_count",
                        "model_id",
                    ],
                    wrap=True,
                )
                vendor_summary = gr.JSON(label="Summary")
                vendor_methodology = gr.Markdown(value=VENDOR_METHODOLOGY_MD)
                gr.Markdown("#### Why this matters")
                gr.Markdown(vendor_why)

        vendor_run.click(
            fn=_run_vendor_benchmark_ui,
            inputs=[vendor_n, vendor_text_set, vendor_openai_fmt],
            outputs=[vendor_runs_df, vendor_summary, vendor_outcome_banner, vendor_methodology],
        )

    return demo


if __name__ == "__main__":
    ui = build_demo()
    ui.launch(
        theme=gr.themes.Soft(),
        css=DEMO_CSS,
        head=CONVAI_WIDGET_HEAD_HTML,
    )
