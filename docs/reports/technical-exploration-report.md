# Technical Exploration Report

**Status**: draft  
**Project**: ElevenLabs Vertical Exploration  
**Last updated**: 2026-04-30

## Executive Summary

This report summarizes a hands-on exploration of ElevenLabs ElevenAgents and ElevenAPI across
Brazilian-market voice AI scenarios. The repository combines product strategy, implementation
discipline, and measured evidence: three vertical demos, a TTS latency benchmark, automated tests,
and documentation designed to make trade-offs explicit.

The current exploration focuses on:

- Real-time voice agent workflows for Telecom, Banking, and Healthcare.
- Low-latency TTS using ElevenLabs Flash models and streaming APIs.
- Tool calling, knowledge base / RAG, simulated conversations, and post-call inspection paths.
- A contextual TTS vendor benchmark comparing ElevenLabs Flash v2.5 and OpenAI `gpt-4o-mini-tts`.
- A reproducible Python workflow with typed configuration, VCR-backed integration tests, and
  generated evidence artifacts.

## Strategic Framing

Voice AI is most compelling when the interaction feels immediate, trusted, and operationally useful.
The selected scenarios represent different enterprise pressures:

- **Telecom**: high inbound volume, repetitive account questions, and escalation management.
- **Banking**: sensitive data, authentication, fraud-related flows, and strict compliance posture.
- **Healthcare**: symptom triage, appointment routing, and knowledge-base-backed answers.

The benchmark adds a cross-vendor decision lens: latency is not the only buying criterion, but
time-to-first-byte is a concrete proxy for perceived responsiveness in interactive voice systems.

## Architecture Overview

The repository uses a small Python stack:

- `src/eleven_demo/` contains reusable library code.
- `scripts/` exposes thin CLI entry points for repeatable exploration.
- `apps/gradio_app.py` composes the capabilities into a browser-based playground.
- `tests/` verifies local behavior with unit tests and VCR-backed integration tests.
- `docs/` captures scenario storytelling, benchmark methodology, and operational notes.

Key design choices:

- One ElevenLabs client factory for SDK access and retry behavior.
- Pydantic v2 for environment configuration and tool schemas.
- Gradio for fast UI composition without a separate frontend codebase.
- FastAPI only as a stretch reference for a local WebSocket bridge.
- VCR cassettes to keep integration tests deterministic and cost-controlled.

## Demo Portfolio

| Demo | What it proves | Evidence |
|---|---|---|
| TTS Playground | Voice quality, model selection, request metadata, and cost traceability. | `scripts/tts_demo.py`, Gradio TTS tab |
| Telecom Agent | Account lookup, server tools, and controlled human handoff. | `docs/scenarios/telecom.md`, scenario regression test |
| Banking Agent | Authentication, card operations, and compliance-aware prompting. | `docs/scenarios/banking.md`, scenario regression test |
| Healthcare Agent | Knowledge base / RAG flow and medical-data posture. | `docs/scenarios/healthcare.md`, KB seed files |
| Latency Benchmark | ElevenLabs Flash TTFB behavior across repeated runs. | `scripts/tts_stream_ttfb.py`, Gradio Latency tab |
| Vendor Benchmark | Contextual ElevenLabs vs OpenAI TTS latency comparison. | `docs/benchmarks/tts-vendor-comparison.md`, benchmark JSON |

## Benchmark Results

Benchmark results are intentionally contextual. They depend on local network conditions, provider
routing, model load, voice choice, and output format. The goal is to build decision-quality
intuition, not to make universal vendor claims.

Latest expected artifact:

- `artifacts/benchmarks/tts-vendor-latest.json`

Summary fields to capture after running the benchmark:

- Date and location / network context.
- ElevenLabs model, voice, output format, median TTFB, p95 TTFB, total generation time.
- OpenAI model, voice, output format, median TTFB, p95 TTFB, total generation time.
- Caveats and any anomalous runs.

## Testing Evidence

Release evidence should be regenerated with the commands documented in the task list.

Expected artifacts:

- `artifacts/reports/pytest.xml`
- `artifacts/reports/integration-pytest.xml`
- `artifacts/reports/coverage.xml`
- `artifacts/reports/htmlcov/`
- `artifacts/reports/pre-commit.txt`

Evidence summary to fill after implementation:

- Unit test count:
- Integration test count:
- Coverage on `src/eleven_demo/`:
- Pre-commit status:
- VCR cassette status:
- Known skips:

## Product Insights

Initial hypotheses to validate while building:

- Streaming TTS matters more than full-file generation for conversational UX.
- Flash-class models are the right default for agentic, turn-by-turn voice interactions.
- Banking and Healthcare demos need privacy posture as a first-class product feature, not an add-on.
- Tool calling and knowledge-base grounding make voice agents easier to trust and operate.
- Benchmarks are most useful when paired with methodology and caveats.

## Risks and Limitations

- Live latency measurements may vary across geography, provider routing, time of day, and account tier.
- Simulated tools use synthetic data and do not represent production integrations.
- The Gradio app is a local playground, not a production frontend.
- The FastAPI WebSocket bridge is local-only unless authentication, TLS, and rate limiting are added.
- No real customer data or private health / financial information should be used in this repository.

## Next Steps

- Complete the three vertical demos and their regression tests.
- Run the ElevenLabs latency benchmark from a Brazilian network and document the results.
- Run the vendor benchmark with the same PT-BR utterance set and preserve raw output.
- Fill the testing evidence section from generated artifacts.
- Revisit scenario prompts after simulated-conversation results.
