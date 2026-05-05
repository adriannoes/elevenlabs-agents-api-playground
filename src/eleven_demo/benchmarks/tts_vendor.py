"""Structured vendor TTS benchmark (ElevenLabs vs OpenAI)."""

from __future__ import annotations

import math
import random
from collections.abc import Callable, Iterator
from time import perf_counter
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

from eleven_demo.benchmarks.openai_tts import parse_openai_response_format, stream_openai_tts
from eleven_demo.config import get_settings
from eleven_demo.metrics.latency import LatencyReport
from eleven_demo.tts.stream import stream as eleven_http_stream

StreamLeg = Callable[[str], Iterator[tuple[bytes, float | None]]]


VENDOR_CANONICAL_TEXT_SETS: dict[str, tuple[str, ...]] = {
    "short-pt-br": (
        "Olá, encontrei sua conta. Posso te ajudar com a segunda via?",
        "Entendi. Vou verificar isso agora.",
        "Certo, por segurança vou confirmar alguns dados.",
    ),
}


class VendorRun(BaseModel):
    """Single timed streaming run."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    provider: Literal["elevenlabs", "openai"]
    model_id: str
    voice: str
    output_format: str
    text_id: str
    ttfb_ms: float
    total_ms: float
    byte_count: int
    region: str | None = None


class VendorSummary(BaseModel):
    """Aggregated latency stats for one provider across runs."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    provider: Literal["elevenlabs", "openai"]
    median_ttfb_ms: float
    p95_ttfb_ms: float
    mean_ttfb_ms: float
    median_total_ms: float
    sample_count: int


class VendorBenchmarkReport(BaseModel):
    """Full benchmark output including raw runs and summaries."""

    model_config = ConfigDict(extra="forbid")

    runs: list[VendorRun]
    summaries: list[VendorSummary]
    hypothesis: str
    caveats: str


def _summary_for_provider(
    provider: Literal["elevenlabs", "openai"],
    ttfb_samples: list[float],
    total_samples: list[float],
) -> VendorSummary:
    ttfb_report = LatencyReport(samples=list(ttfb_samples))
    total_report = LatencyReport(samples=list(total_samples))
    if not ttfb_samples or not total_samples:
        return VendorSummary(
            provider=provider,
            median_ttfb_ms=math.nan,
            p95_ttfb_ms=math.nan,
            mean_ttfb_ms=math.nan,
            median_total_ms=math.nan,
            sample_count=0,
        )
    return VendorSummary(
        provider=provider,
        median_ttfb_ms=ttfb_report.median * 1000.0,
        p95_ttfb_ms=ttfb_report.p95 * 1000.0,
        mean_ttfb_ms=ttfb_report.mean * 1000.0,
        median_total_ms=total_report.median * 1000.0,
        sample_count=len(ttfb_samples),
    )


def _consume_stream(
    gen: Iterator[tuple[bytes, float | None]],
) -> tuple[float | None, float, int]:
    """Return TTFB (seconds), total wall time (seconds), total bytes."""
    t0 = perf_counter()
    ttfb_s: float | None = None
    total_bytes = 0
    for chunk, tag in gen:
        total_bytes += len(chunk)
        if tag is not None:
            ttfb_s = tag
    total_s = perf_counter() - t0
    return ttfb_s, total_s, total_bytes


def run_vendor_benchmark(
    texts: list[str],
    n: int,
    *,
    randomize_order: bool = True,
    eleven_stream_fn: StreamLeg | None = None,
    openai_stream_fn: StreamLeg | None = None,
    rng: random.Random | None = None,
    eleven_model_id: str | None = None,
    eleven_output_format: str | None = None,
    openai_model_id: str | None = None,
    openai_voice: str | None = None,
    openai_response_format: str | None = None,
) -> VendorBenchmarkReport:
    """Run ``n`` paired rounds (each round hits both providers, order shuffled when enabled)."""
    if n < 1:
        msg = "n must be at least 1"
        raise ValueError(msg)
    if not texts:
        msg = "texts must not be empty"
        raise ValueError(msg)

    settings = get_settings()
    voice_id = settings.default_pt_voice_id
    if not voice_id:
        msg = "DEFAULT_PT_VOICE_ID must be set in the environment for the ElevenLabs benchmark leg."
        raise ValueError(msg)

    el_model = eleven_model_id or settings.tts_model_id
    el_fmt = eleven_output_format or settings.tts_output_format
    oa_model = openai_model_id or settings.openai_tts_model_id
    oa_voice = openai_voice or settings.openai_tts_voice
    oa_fmt_str = openai_response_format or settings.openai_tts_response_format
    oa_fmt = parse_openai_response_format(oa_fmt_str)

    rnd = rng or random.Random()  # noqa: S311 — benchmark ordering, not security-sensitive
    runs: list[VendorRun] = []

    for round_idx in range(n):
        text = texts[round_idx % len(texts)]
        text_id = str(round_idx % len(texts))
        order: list[Literal["elevenlabs", "openai"]] = ["elevenlabs", "openai"]
        if randomize_order:
            rnd.shuffle(order)

        for prov in order:
            if prov == "elevenlabs":
                if eleven_stream_fn is not None:
                    gen = eleven_stream_fn(text)
                else:
                    gen = eleven_http_stream(
                        text,
                        voice_id=voice_id,
                        model_id=el_model,
                        output_format=el_fmt,
                    )
                ttfb_s, total_s, byte_count = _consume_stream(gen)
                runs.append(
                    VendorRun(
                        provider="elevenlabs",
                        model_id=el_model,
                        voice=voice_id,
                        output_format=el_fmt,
                        text_id=text_id,
                        ttfb_ms=(ttfb_s or 0.0) * 1000.0,
                        total_ms=total_s * 1000.0,
                        byte_count=byte_count,
                        region=None,
                    )
                )
            else:
                if openai_stream_fn is not None:
                    gen = openai_stream_fn(text)
                else:
                    gen = stream_openai_tts(
                        text,
                        model_id=oa_model,
                        voice=oa_voice,
                        response_format=oa_fmt,
                    )
                ttfb_s, total_s, byte_count = _consume_stream(gen)
                runs.append(
                    VendorRun(
                        provider="openai",
                        model_id=oa_model,
                        voice=oa_voice,
                        output_format=oa_fmt_str,
                        text_id=text_id,
                        ttfb_ms=(ttfb_s or 0.0) * 1000.0,
                        total_ms=total_s * 1000.0,
                        byte_count=byte_count,
                        region=None,
                    )
                )

    eleven_ttfb = [r.ttfb_ms / 1000.0 for r in runs if r.provider == "elevenlabs"]
    eleven_tot = [r.total_ms / 1000.0 for r in runs if r.provider == "elevenlabs"]
    openai_ttfb = [r.ttfb_ms / 1000.0 for r in runs if r.provider == "openai"]
    openai_tot = [r.total_ms / 1000.0 for r in runs if r.provider == "openai"]

    hypothesis = (
        "Lower time-to-first-byte on streaming TTS tends to feel more responsive "
        "in conversational voice UX."
    )
    caveats = (
        "Measurements are local (clock, network, SDK versions). "
        "Do not treat a single run as a definitive platform comparison."
    )

    summaries = [
        _summary_for_provider("elevenlabs", eleven_ttfb, eleven_tot),
        _summary_for_provider("openai", openai_ttfb, openai_tot),
    ]

    return VendorBenchmarkReport(
        runs=runs,
        summaries=summaries,
        hypothesis=hypothesis,
        caveats=caveats,
    )


def comparison_from_vendor_report(
    report: VendorBenchmarkReport,
    *,
    tie_epsilon_ms: float = 0.5,
) -> dict[str, Any]:
    """Compare providers on median streaming TTFB (lower milliseconds = faster first audio).

    Returns a plain dict suitable for JSON and UI copy. ``margin_ms`` is always expressed as
    how much faster the winning side is on median TTFB for this run (non-negative).
    """

    el = next((s for s in report.summaries if s.provider == "elevenlabs"), None)
    oa = next((s for s in report.summaries if s.provider == "openai"), None)
    if el is None or oa is None:
        return {
            "outcome": "insufficient_data",
            "reason": "missing_provider_summary",
            "metric": "median_ttfb_ms",
        }

    el_med = float(el.median_ttfb_ms)
    oa_med = float(oa.median_ttfb_ms)
    if math.isnan(el_med) or math.isnan(oa_med):
        return {
            "outcome": "insufficient_data",
            "reason": "nan_median",
            "metric": "median_ttfb_ms",
        }

    if abs(el_med - oa_med) < tie_epsilon_ms:
        return {
            "outcome": "tie",
            "metric": "median_ttfb_ms",
            "elevenlabs_median_ms": el_med,
            "openai_median_ms": oa_med,
            "tie_epsilon_ms": tie_epsilon_ms,
        }

    if el_med < oa_med:
        margin_ms = oa_med - el_med
        margin_pct = (margin_ms / oa_med * 100.0) if oa_med > 0 else None
        return {
            "outcome": "elevenlabs_faster",
            "metric": "median_ttfb_ms",
            "elevenlabs_median_ms": el_med,
            "openai_median_ms": oa_med,
            "margin_ms": margin_ms,
            "margin_pct_vs_slower": margin_pct,
        }

    margin_ms = el_med - oa_med
    margin_pct = (margin_ms / el_med * 100.0) if el_med > 0 else None
    return {
        "outcome": "openai_faster",
        "metric": "median_ttfb_ms",
        "elevenlabs_median_ms": el_med,
        "openai_median_ms": oa_med,
        "margin_ms": margin_ms,
        "margin_pct_vs_slower": margin_pct,
    }


def benchmark_report_to_serializable(report: VendorBenchmarkReport) -> dict[str, Any]:
    """Convert report to plain dict for JSON output."""
    return report.model_dump()
