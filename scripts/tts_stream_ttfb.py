#!/usr/bin/env python3
"""CLI: streaming TTS benchmark — prints per-call TTFB and aggregate stats."""

from __future__ import annotations

import argparse

from rich.console import Console
from rich.table import Table

from eleven_demo.config import get_settings
from eleven_demo.metrics.latency import LatencyReport
from eleven_demo.tts.stream import stream as eleven_stream

_MODEL_BY_CHOICE = {
    "flash": "eleven_flash_v2_5",
    "multilingual": "eleven_multilingual_v2",
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Streaming TTS TTFB benchmark (ElevenLabs).")
    parser.add_argument("--n", type=int, default=10, help="Number of streaming calls")
    parser.add_argument(
        "--model",
        choices=sorted(_MODEL_BY_CHOICE.keys()),
        default="flash",
        help="Logical model preset",
    )
    parser.add_argument("--text", default="Esta é uma demonstração de latência.")
    parser.add_argument("--voice-id", dest="voice_id", default=None)
    args = parser.parse_args()

    settings = get_settings()
    voice_id = args.voice_id or settings.default_pt_voice_id
    if not voice_id:
        msg = "Pass --voice-id or set DEFAULT_PT_VOICE_ID."
        raise SystemExit(msg)

    model_id = _MODEL_BY_CHOICE[args.model]
    report = LatencyReport()
    rows: list[tuple[int, float, int]] = []

    for i in range(args.n):
        total_bytes = 0
        ttfb_ms = 0.0
        for chunk, tag in eleven_stream(
            args.text,
            voice_id=voice_id,
            model_id=model_id,
            output_format=settings.tts_output_format,
        ):
            total_bytes += len(chunk)
            if tag is not None:
                ttfb_ms = tag * 1000.0
        report.samples.append(ttfb_ms / 1000.0)
        rows.append((i + 1, ttfb_ms, total_bytes))

    table = Table(title="Streaming TTS TTFB")
    table.add_column("run")
    table.add_column("ttfb_ms", justify="right")
    table.add_column("total_bytes", justify="right")
    for idx, ms, nbytes in rows:
        table.add_row(str(idx), f"{ms:.1f}", str(nbytes))

    console = Console()
    console.print(table)
    foot = (
        f"median={report.median * 1000:.1f} ms  "
        f"p95={report.p95 * 1000:.1f} ms  "
        f"mean={report.mean * 1000:.1f} ms"
    )
    console.print(foot)


if __name__ == "__main__":
    main()
