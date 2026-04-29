# Tech Stack Decisions

This document records the approved technology choices for the `eleven-demo` repository, with the trade-offs that led to each choice. PRDs and tasks reference this file; do not propose changes without a matching ADR-style update here first.

## Summary

| Layer | Choice | Why |
|---|---|---|
| Language | Python 3.13 | Latest stable, broad library support, ElevenLabs SDK is Python-first. |
| Package manager | uv | Fast resolver, single binary, lockfile reproducibility, modern (Astral). |
| Data validation | Pydantic v2 | De-facto standard for Python typed data; SDK already uses it. |
| Settings | pydantic-settings | Typed env loading, validation at startup. |
| HTTP client | httpx (transitive) | Async-first, used by the ElevenLabs SDK internally. |
| WebSocket client | websockets | Reference Python implementation, asyncio-native. |
| Demo UI | Gradio | Fastest path to a polished AI demo with audio I/O; minutes to add a tab. |
| Backend service | FastAPI (minimal) | Used only for the WebSocket bridge demo. ASGI native, plays well with `websockets`. |
| ASGI server | Uvicorn | Standard pair for FastAPI. |
| CLI output | rich | Pretty tables and progress bars without HTML overhead. |
| Linting + formatting | ruff | Replaces flake8, isort, black, pylint; single tool, 10-100x faster. |
| Type checking | mypy (strict) | Strict for `src/`, relaxed for `tests/` and `scripts/`. |
| Test runner | pytest | Industry standard. |
| Async tests | pytest-asyncio | `asyncio_mode = "auto"`. |
| Parallel tests | pytest-xdist | Fast unit loop with `-n auto`. |
| HTTP recording | pytest-vcr (vcrpy) | Records ElevenLabs API responses once; replays in CI without burning credits. |
| Coverage | pytest-cov | Single dedicated invocation (no xdist) per the testing-standards rule. |
| Pre-commit | pre-commit + ruff + gitleaks + detect-private-key | Catches lints and secrets before commit. |

## Decision details and rejected alternatives

### UI framework: Gradio (chosen) vs Streamlit vs Next.js

- **Gradio**: ~30 lines for a working multi-tab demo with audio in/out. ElevenLabs ships Gradio examples in their docs.
- **Streamlit**: equally fast for dashboards, weaker on audio I/O, harder to embed external widgets like the ElevenLabs JS SDK.
- **Next.js**: best polish, but adds a TypeScript codebase, build step, and ~10x more setup cost. Out of scope for a hands-on exploration repo.

**Rejected alternatives**: Streamlit, Next.js, Reflex.

### Package manager: uv (chosen) vs pip vs Poetry

- **uv**: 10-100x faster than pip; single static binary; deterministic lockfile.
- **pip**: ubiquitous but slow, no lockfile by default, dependency resolution can be brittle.
- **Poetry**: solid lockfile, but slower and heavier than uv.

**Rejected alternatives**: pip-tools, Poetry, Hatch CLI.

### TTS model selection (default): `eleven_flash_v2_5`

- **Flash v2.5**: lowest TTFB (~75-150 ms), good enough quality for conversational demos, supports Brazilian Portuguese.
- **Multilingual v2**: higher quality, significantly higher latency. Use for the Healthcare scenario and Voice Library exploration.
- **v3**: most expressive (tags, emotion). Use for marketing-style demos in the TTS Playground tab.
- **Turbo v2.5**: balanced; this is what ElevenAgents uses by default.

Pinned in `.env.example`; per-call overrides allowed.

### Output format default: `mp3_22050_32`

- Smallest payload that still sounds clean for voice. Halves bandwidth vs `mp3_44100_128` and meaningfully reduces perceived TTFB.

### Test recording: VCR cassettes (chosen) vs pure mocks

- **VCR**: real-shape responses, future-proof against SDK changes. One-time recording cost (a few credits).
- **Pure mocks**: zero credits but tend to drift from reality and miss real bugs.

**Rule**: integration tests use VCR; unit tests use pure mocks.

### Async vs sync ElevenLabs SDK calls

- **Sync**: scripts and unit tests. Easier to read and debug.
- **Async (`websockets` directly)**: only for streaming TTS, STT realtime, and Agents conversation WebSocket.

The `eleven_demo.client` module exposes both surfaces from the same factory.

### Post-call analysis without an HTTP webhook receiver

- **Chosen**: Operational exploration uses `client.conversations.list` / conversation retrieval from a small CLI (`scripts/conversations_list.py`) when needed; analysis fields align with [Agent analysis](https://elevenlabs.io/docs/eleven-agents/customization/agent-analysis) documentation.
- **Rejected for this repo**: Running a dedicated HTTP endpoint for [post-call webhooks](https://elevenlabs.io/docs/eleven-agents/workflows/post-call-webhooks) — adds deployment surface (TLS, signature verification, uptime) beyond the demo scope while providing marginal benefit for local exploration.

Document webhook flows in narrative docs so production integrations remain discussable without implementing them here.

## Out of scope (explicit non-goals)

- TypeScript / Next.js / React frontends.
- Mobile (iOS / Android / React Native).
- Real telephony (Twilio / SIP / Plivo / Vonage). The Gradio app simulates the conversation surface; integration is documented but not wired.
- Voice biometrics. Mentioned as a talking point for Banking, not implemented.
- Multi-tenant production deployment. Single-developer local exploration.

## Update process

1. Open a PR titled `chore(architecture): adjust tech-stack — <change>`.
2. Update this file with rationale and rejected alternatives.
3. Update `pyproject.toml` and `uv.lock` in the same PR.
4. If the change affects a generated PRD or task list, regenerate it.
