"""Unit tests for TTS vendor benchmark model and runner (mocked streams)."""

from __future__ import annotations

import random
from collections.abc import Iterator

import pytest
from pydantic import SecretStr

from eleven_demo.benchmarks.tts_vendor import (
    VENDOR_CANONICAL_TEXT_SETS,
    VendorBenchmarkReport,
    VendorSummary,
    comparison_from_vendor_report,
    run_vendor_benchmark,
)
from eleven_demo.config import Settings


def test_vendor_canonical_text_sets_contains_short_pt_br() -> None:
    assert "short-pt-br" in VENDOR_CANONICAL_TEXT_SETS
    assert len(VENDOR_CANONICAL_TEXT_SETS["short-pt-br"]) >= 1


def _fake_eleven(_: str) -> Iterator[tuple[bytes, float | None]]:
    yield b"x", 0.01
    yield b"y", None


def _fake_openai(_: str) -> Iterator[tuple[bytes, float | None]]:
    yield b"p", 0.02
    yield b"q", None


def test_run_vendor_benchmark_collects_runs_and_summaries(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = Settings(
        elevenlabs_api_key=SecretStr("xi-z"),
        default_pt_voice_id="voice-z",
        tts_model_id="eleven_flash_v2_5",
        tts_output_format="mp3_22050_32",
        openai_api_key=SecretStr("sk-z"),
        openai_tts_model_id="gpt-4o-mini-tts",
        openai_tts_voice="coral",
        openai_tts_response_format="mp3",
    )

    monkeypatch.setattr("eleven_demo.benchmarks.tts_vendor.get_settings", lambda: fake)

    report = run_vendor_benchmark(
        ["hello"],
        2,
        randomize_order=False,
        eleven_stream_fn=_fake_eleven,
        openai_stream_fn=_fake_openai,
        rng=random.Random(0),
    )

    assert len(report.runs) == 4
    assert {r.provider for r in report.runs} == {"elevenlabs", "openai"}
    el = next(s for s in report.summaries if s.provider == "elevenlabs")
    oa = next(s for s in report.summaries if s.provider == "openai")
    assert el.sample_count == 2
    assert oa.sample_count == 2
    assert el.median_ttfb_ms == pytest.approx(10.0)
    assert oa.median_ttfb_ms == pytest.approx(20.0)
    assert comparison_from_vendor_report(report)["outcome"] == "elevenlabs_faster"


def _minimal_report(*summaries: VendorSummary) -> VendorBenchmarkReport:
    return VendorBenchmarkReport(
        runs=[],
        summaries=list(summaries),
        hypothesis="h",
        caveats="c",
    )


def test_comparison_elevenlabs_faster() -> None:
    el = VendorSummary(
        provider="elevenlabs",
        median_ttfb_ms=10.0,
        p95_ttfb_ms=11.0,
        mean_ttfb_ms=10.5,
        median_total_ms=50.0,
        sample_count=3,
    )
    oa = VendorSummary(
        provider="openai",
        median_ttfb_ms=25.0,
        p95_ttfb_ms=30.0,
        mean_ttfb_ms=26.0,
        median_total_ms=80.0,
        sample_count=3,
    )
    cmp = comparison_from_vendor_report(_minimal_report(el, oa))
    assert cmp["outcome"] == "elevenlabs_faster"
    assert cmp["margin_ms"] == pytest.approx(15.0)
    assert cmp["margin_pct_vs_slower"] == pytest.approx(60.0)


def test_comparison_openai_faster() -> None:
    el = VendorSummary(
        provider="elevenlabs",
        median_ttfb_ms=40.0,
        p95_ttfb_ms=41.0,
        mean_ttfb_ms=40.0,
        median_total_ms=90.0,
        sample_count=2,
    )
    oa = VendorSummary(
        provider="openai",
        median_ttfb_ms=20.0,
        p95_ttfb_ms=21.0,
        mean_ttfb_ms=20.0,
        median_total_ms=45.0,
        sample_count=2,
    )
    cmp = comparison_from_vendor_report(_minimal_report(el, oa))
    assert cmp["outcome"] == "openai_faster"
    assert cmp["margin_ms"] == pytest.approx(20.0)


def test_comparison_tie_within_epsilon() -> None:
    el = VendorSummary(
        provider="elevenlabs",
        median_ttfb_ms=10.0,
        p95_ttfb_ms=10.0,
        mean_ttfb_ms=10.0,
        median_total_ms=10.0,
        sample_count=1,
    )
    oa = VendorSummary(
        provider="openai",
        median_ttfb_ms=10.2,
        p95_ttfb_ms=10.2,
        mean_ttfb_ms=10.2,
        median_total_ms=10.2,
        sample_count=1,
    )
    cmp = comparison_from_vendor_report(_minimal_report(el, oa), tie_epsilon_ms=0.5)
    assert cmp["outcome"] == "tie"


def test_comparison_nan_median() -> None:
    el = VendorSummary(
        provider="elevenlabs",
        median_ttfb_ms=float("nan"),
        p95_ttfb_ms=float("nan"),
        mean_ttfb_ms=float("nan"),
        median_total_ms=float("nan"),
        sample_count=0,
    )
    oa = VendorSummary(
        provider="openai",
        median_ttfb_ms=20.0,
        p95_ttfb_ms=20.0,
        mean_ttfb_ms=20.0,
        median_total_ms=20.0,
        sample_count=1,
    )
    cmp = comparison_from_vendor_report(_minimal_report(el, oa))
    assert cmp["outcome"] == "insufficient_data"


def test_run_vendor_benchmark_requires_voice_id(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = Settings(
        elevenlabs_api_key=SecretStr("xi-z"),
        default_pt_voice_id=None,
    )

    monkeypatch.setattr("eleven_demo.benchmarks.tts_vendor.get_settings", lambda: fake)

    with pytest.raises(ValueError, match="DEFAULT_PT_VOICE_ID"):
        run_vendor_benchmark(
            ["x"],
            1,
            eleven_stream_fn=_fake_eleven,
            openai_stream_fn=_fake_openai,
        )
