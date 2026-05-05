"""Time-to-first-byte sampling and latency aggregates (no numpy)."""

from __future__ import annotations

import math
import statistics
from collections.abc import Callable, Iterator
from functools import wraps
from time import perf_counter
from typing import ParamSpec

from pydantic import BaseModel, ConfigDict, Field

P = ParamSpec("P")


class LatencyReport(BaseModel):
    """Collects TTFB samples (seconds) and exposes summary statistics."""

    model_config = ConfigDict(extra="forbid")

    samples: list[float] = Field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.samples)

    @property
    def mean(self) -> float:
        if not self.samples:
            return math.nan
        return float(statistics.mean(self.samples))

    @property
    def median(self) -> float:
        if not self.samples:
            return math.nan
        return float(statistics.median(self.samples))

    @property
    def min(self) -> float:
        if not self.samples:
            return math.nan
        return float(min(self.samples))

    @property
    def max(self) -> float:
        if not self.samples:
            return math.nan
        return float(max(self.samples))

    @property
    def p95(self) -> float:
        if not self.samples:
            return math.nan
        xs = sorted(self.samples)
        idx = int(len(xs) * 0.95)
        if idx >= len(xs):
            idx = len(xs) - 1
        return float(xs[idx])


def measure_ttfb(
    report: LatencyReport,
) -> Callable[
    [Callable[P, Iterator[bytes]]],
    Callable[P, Iterator[bytes]],
]:
    """Decorate a generator that yields audio chunks; record TTFB (seconds) on first yield."""

    def decorator(fn: Callable[P, Iterator[bytes]]) -> Callable[P, Iterator[bytes]]:
        @wraps(fn)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> Iterator[bytes]:
            gen = fn(*args, **kwargs)
            t0 = perf_counter()
            first = True
            for chunk in gen:
                if first:
                    report.samples.append(perf_counter() - t0)
                    first = False
                yield chunk

        return wrapper

    return decorator
