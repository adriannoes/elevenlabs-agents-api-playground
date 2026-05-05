# TTS vendor comparison — methodology

This document describes the **local, reproducible** streaming comparison between **ElevenLabs** HTTP chunked TTS and **OpenAI** streaming speech implemented in this repository (`eleven_demo.benchmarks.tts_vendor`). It exists so readers can interpret numbers without overclaiming: results are **machine- and network-dependent**, not a universal ranking.

## Purpose

Exercise the **interactive voice path**: short Portuguese (Brazil) utterances typical of customer care, with emphasis on **time-to-first-byte (TTFB)** on the first audio chunk and total wall time to drain the stream. The comparison informs UX expectations (perceived responsiveness), not contractual SLAs.

## Hypothesis (embedded in the report JSON)

Lower TTFB on streaming TTS tends to feel more responsive in conversational voice UX. The benchmark emits this as the `hypothesis` field in the serialized report; treat it as a **design intuition**, not a proven causal claim.

## What is measured

| Metric | Definition |
| --- | --- |
| **TTFB** | Wall time from the start of the streaming call until the **first non-empty audio chunk** arrives (local `perf_counter`, seconds → milliseconds in output). |
| **Total time** | Wall time until the full stream is consumed. |
| **Byte count** | Sum of payload bytes received for that run. |

Aggregates in the summary: **median / p95 / mean** TTFB and **median** total time per provider, across all runs for that leg.

## Model and format defaults

Values come from `eleven_demo.config.Settings` unless overridden by CLI flags or Gradio controls.

| Leg | Model ID (default) | Voice | Output / response format |
| --- | --- | --- | --- |
| **ElevenLabs** | `eleven_flash_v2_5` (`TTS_MODEL_ID`) | `DEFAULT_PT_VOICE_ID` (required) | `mp3_22050_32` (`TTS_OUTPUT_FORMAT`) |
| **OpenAI** | `gpt-4o-mini-tts` (`OPENAI_TTS_MODEL_ID`) | `coral` (`OPENAI_TTS_VOICE`) | `mp3` by default; CLI/UI may select `pcm` instead (`OPENAI_TTS_RESPONSE_FORMAT`) |

Confirm current ElevenLabs model IDs and latency guidance in the official docs: [Models](https://elevenlabs.io/docs/overview/models), [Latency optimization](https://elevenlabs.io/docs/eleven-api/guides/how-to/best-practices/latency-optimization). OpenAI parameters align with the [Text to speech guide](https://platform.openai.com/docs/guides/text-to-speech) (`audio.speech` streaming).

## PT-BR utterance set

Canonical strings live in `VENDOR_CANONICAL_TEXT_SETS` in `src/eleven_demo/benchmarks/tts_vendor.py`. At the time of writing the CLI and Gradio default is **`short-pt-br`**:

1. `Olá, encontrei sua conta. Posso te ajudar com a segunda via?`
2. `Entendi. Vou verificar isso agora.`
3. `Certo, por segurança vou confirmar alguns dados.`

Each **round** picks one phrase (cycling by round index). Within the round, **ElevenLabs** and **OpenAI** runs are executed in **random order** (`randomize_order=True`) to reduce systematic bias from back-to-back thermal or network state.

## Prerequisites

- `ELEVENLABS_API_KEY`, `DEFAULT_PT_VOICE_ID` — required for the ElevenLabs leg.
- `OPENAI_API_KEY` — required for the OpenAI leg (optional for the rest of the repo).

See `.env.example`.

## Environment fields to record with each published run

When you save a JSON artifact or paste results into this doc, add a short **run context** block (outside the JSON if you prefer) so others can interpret variance:

| Field | Example |
| --- | --- |
| **Date (UTC)** | `2026-04-29` |
| **City / region** | `São Paulo, BR` |
| **Network** | `Ethernet` / `Wi‑Fi` / `VPN on/off` |
| **Machine** | `Apple M3, 16GB` |
| **Python** | `3.12.x` (`python --version`) |
| **SDK / package notes** | `elevenlabs` + `openai` versions from `uv pip list` |

Do **not** paste API keys, voice IDs tied to production tenants, or customer data into this document or committed artifacts.

## Caveats (also in report JSON)

- Single runs are **noisy**; prefer several rounds (`n` ≥ 5 for exploratory stability).
- Path differs from telephony (codecs, jitter buffers, device playback); **browser and PSTN** stacks add their own latency.
- Voice choice, text length, and model revisions change outcomes; this benchmark fixes a **narrow** PT-BR CX slice.
- The serialized report includes a `caveats string` from code: treat measurements as local and **not** a definitive cross-vendor verdict.

## How to rerun

**CLI** (writes JSON and prints a Rich table):

```bash
uv run python scripts/tts_vendor_benchmark.py --n 5 --text-set short-pt-br --out artifacts/benchmarks/tts-vendor-latest.json
```

Optional overrides:

```bash
uv run python scripts/tts_vendor_benchmark.py --n 10 --eleven-model eleven_flash_v2_5 --openai-model gpt-4o-mini-tts --openai-format mp3
```

**Gradio**: open **`Vendor Benchmark`** in `uv run python apps/gradio_app.py`, set rounds, text set, and OpenAI format, then **Run vendor benchmark**. The UI uses the same `run_vendor_benchmark` function.

**Artifact path**: default output is `artifacts/benchmarks/tts-vendor-latest.json` (gitignored or local-only; regenerate on each machine).

## Results (paste your JSON below)

After a run, paste the contents of your artifact (or a redacted excerpt). Full shape matches `VendorBenchmarkReport.model_dump()`:

- `runs[]`: per-run `provider`, `model_id`, `voice`, `output_format`, `text_id`, `ttfb_ms`, `total_ms`, `byte_count`
- `summaries[]`: aggregated stats per provider
- `hypothesis`, `caveats`: strings

Example structure (numbers are illustrative only):

```json
{
  "runs": [
    {
      "provider": "elevenlabs",
      "model_id": "eleven_flash_v2_5",
      "voice": "<your-default-pt-voice-id>",
      "output_format": "mp3_22050_32",
      "text_id": "0",
      "ttfb_ms": 120.0,
      "total_ms": 450.0,
      "byte_count": 12345,
      "region": null
    }
  ],
  "summaries": [
    {
      "provider": "elevenlabs",
      "median_ttfb_ms": 118.5,
      "p95_ttfb_ms": 210.0,
      "mean_ttfb_ms": 125.0,
      "median_total_ms": 440.0,
      "sample_count": 5
    },
    {
      "provider": "openai",
      "median_ttfb_ms": 95.0,
      "p95_ttfb_ms": 180.0,
      "mean_ttfb_ms": 102.0,
      "median_total_ms": 400.0,
      "sample_count": 5
    }
  ],
  "hypothesis": "Lower time-to-first-byte on streaming TTS tends to feel more responsive in conversational voice UX.",
  "caveats": "Measurements are local (clock, network, SDK versions). Do not treat a single run as a definitive platform comparison."
}
```

---

## Code references

- Core logic: `src/eleven_demo/benchmarks/tts_vendor.py`
- OpenAI stream: `src/eleven_demo/benchmarks/openai_tts.py`
- ElevenLabs stream: `src/eleven_demo/tts/stream.py`
- CLI: `scripts/tts_vendor_benchmark.py`
- UI tab: `apps/gradio_app.py` (**Vendor Benchmark**)
