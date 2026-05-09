# Exploring this repository

This is a **hands-on learning lab** for [ElevenAgents](https://elevenlabs.io/docs/eleven-agents/overview) and [ElevenAPI](https://elevenlabs.io/docs/api-reference/introduction). It is not a production service or a compliance benchmark. The focus is Brazilian-market **voice scenarios** (telecom, banking, healthcare), latency measurement, and how SDK primitives fit together.

If you cloned the repo to **study** the platform, use this page as a short orientation, then follow the [end-to-end walkthrough](walkthrough.md).

## Quick commands

After [Quick start](../README.md#quick-start) (clone, `uv sync --extra dev`, `.env` with `ELEVENLABS_API_KEY` and voice/agent variables as needed):

```bash
uv run python scripts/demo_prepare.py
```

```bash
uv run python apps/gradio_app.py
```

The first command verifies the API key and provisions or updates the three demo agents; the second opens the Gradio playground.

## Where to read next

- [Walkthrough](walkthrough.md) — full path through surfaces and scripts.
- [Technical exploration report](reports/technical-exploration-report.md) — architecture and evidence snapshot.
- [Learning experience memo](../product/learning-experience.md) — field notes from integrating against public docs and the SDK.

## Design choices in this lab

- **Single SDK entry** — All ElevenLabs access goes through `eleven_demo.client.get_client()` (retries on 429/5xx, no ad-hoc client constructors).
- **Integration tests** — HTTP traffic is replayed with VCR cassettes where possible so CI stays deterministic and does not consume credits on every run.
- **Browser and Next.js** — The optional `apps/web` app mints **signed URLs** server-side so the browser never receives `ELEVENLABS_API_KEY`.
- **Post-call data** — This repo does not run a long-lived **post-call webhook** HTTP receiver. Recent conversations can be inspected with [`scripts/conversations_list.py`](../scripts/conversations_list.py); for a production-style webhook design, see [Post-call webhooks pattern](patterns/post-call-webhooks.md).

## Going further

When you have walked through the demo and want **ideas for what to try next** (still as learning, not as shipping this repo as a product), see [Extending this lab](extending-this-lab.md).
