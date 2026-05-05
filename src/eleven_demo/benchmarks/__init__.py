"""Vendor TTS benchmark package."""

from eleven_demo.benchmarks.openai_tts import parse_openai_response_format, stream_openai_tts
from eleven_demo.benchmarks.tts_vendor import (
    VendorBenchmarkReport,
    VendorRun,
    VendorSummary,
    benchmark_report_to_serializable,
    comparison_from_vendor_report,
    run_vendor_benchmark,
)

__all__ = [
    "VendorBenchmarkReport",
    "VendorRun",
    "VendorSummary",
    "benchmark_report_to_serializable",
    "comparison_from_vendor_report",
    "parse_openai_response_format",
    "run_vendor_benchmark",
    "stream_openai_tts",
]
