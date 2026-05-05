"""Unit tests for latency metrics."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

import pytest

import eleven_demo.metrics.latency as latency_mod
from eleven_demo.metrics.latency import LatencyReport, measure_ttfb

if TYPE_CHECKING:
    from _pytest.monkeypatch import MonkeyPatch


def test_empty_samples_yield_nan_stats() -> None:
    r = LatencyReport(samples=[])
    assert r.count == 0
    assert math.isnan(r.median)
    assert math.isnan(r.p95)
    assert math.isnan(r.mean)
    assert math.isnan(r.min)
    assert math.isnan(r.max)


def test_one_sample_median_and_p95_match() -> None:
    r = LatencyReport(samples=[0.05])
    assert r.median == pytest.approx(0.05)
    assert r.p95 == pytest.approx(0.05)
    assert r.mean == pytest.approx(0.05)
    assert r.min == pytest.approx(0.05)
    assert r.max == pytest.approx(0.05)


def test_p95_indexing_matches_task_formula() -> None:
    samples = [float(i) for i in range(1, 21)]  # 1..20
    r = LatencyReport(samples=samples)
    xs = sorted(samples)
    idx = int(len(xs) * 0.95)
    assert r.p95 == pytest.approx(xs[idx])


def test_measure_ttfb_records_time_to_first_yield(monkeypatch: MonkeyPatch) -> None:
    clock = iter([1000.0, 1000.04, 1000.04])

    monkeypatch.setattr(latency_mod, "perf_counter", lambda: next(clock))

    report = LatencyReport()

    @measure_ttfb(report)
    def gen() -> object:
        yield b"a"
        yield b"b"

    assert list(gen()) == [b"a", b"b"]
    assert len(report.samples) == 1
    assert report.samples[0] == pytest.approx(0.04)
