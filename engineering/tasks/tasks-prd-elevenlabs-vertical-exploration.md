# Exploration delivery record — ElevenLabs Vertical Exploration

**Source PRD**: [product/prd/prd-elevenlabs-vertical-exploration.md](../../product/prd/prd-elevenlabs-vertical-exploration.md)

This document records **what was planned and delivered** against the PRD: phases, completed subtasks, primary files, and a verification hook. It is **not** the full line-by-line implementation brief used during build-for detail design, see the [technical exploration report](../../docs/reports/technical-exploration-report.md) and [tech stack ADR](../architecture/tech-stack-decisions.md).

---

## What shipped (summary)

- **Library** (`src/eleven_demo/`): `Settings`, `get_client()` with retry, TTS/STT, voices, metrics, agents (factory, tools, KB, simulate), Telecom/Banking/Healthcare scenarios, vendor benchmark (ElevenLabs vs OpenAI).
- **Scripts** (`scripts/`): exploration CLIs, provisioning, `conversations_list`, `generate_evidence_report.py`.
- **Apps**: `apps/gradio_app.py` (primary), `apps/web/` (Next.js + [`elevenlabs/ui`](https://github.com/elevenlabs/ui)), `apps/ws_bridge/`.
- **Tests**: `tests/unit/` + `tests/integration/` with VCR; coverage gate ≥80% on the library (integration excluded).
- **Docs**: `docs/scenarios/`, `docs/walkthrough.md`, `docs/benchmarks/tts-vendor-comparison.md`, `docs/reports/technical-exploration-report.md`, `docs/design/`.

**Quick map**

```text
src/eleven_demo/    Library
scripts/            CLIs
apps/               Gradio, web, ws_bridge
tests/              unit + integration + cassettes
docs/               walkthrough, scenarios, report, design
engineering/        this file, ADRs
.cursor/skills/     Local skills (Agent Skills spec)
```

---

## 1.0 Library foundation — client and config

**Bar**: `get_client()` retries 429/5xx; `Settings` uses `SecretStr`; unit tests; ruff clean.

- [x] **1.1 Scaffold package tree**
  - **Files**: `src/eleven_demo/**/__init__.py`, `tests/__init__.py`, `tests/unit/__init__.py`, `tests/integration/__init__.py`
  - **Outcome**: Importable packages; hatch/pytest collect without layout errors.
  - **Verify**: `uv run python -c "import eleven_demo"`

- [x] **1.2 Settings module**
  - **Files**: `src/eleven_demo/config.py`, `tests/unit/test_config.py`
  - **Outcome**: `pydantic-settings`, `.env`, required API key, TTS/STT defaults aligned with [models docs](https://elevenlabs.io/docs/overview/models).
  - **Verify**: `uv run pytest tests/unit/test_config.py -v`

- [x] **1.3 SDK factory with retry**
  - **Files**: `src/eleven_demo/client.py`, `tests/unit/test_client.py`
  - **Outcome**: Memoized `get_client()`, 30s timeout, `_with_retry` on eligible sync REST paths.
  - **Verify**: `uv run pytest tests/unit/test_client.py -v`

- [x] **1.4 Shared fixtures (`conftest`)**
  - **Files**: `tests/conftest.py`
  - **Outcome**: Skip integration without API key when no cassette; `mock_eleven_client`; clear settings/client cache between tests.
  - **Verify**: `uv run pytest --collect-only -q`

- [x] **1.5 Unit tests — config**
  - **Files**: `tests/unit/test_config.py`
  - **Outcome**: Env defaults/overrides, `SecretStr`, missing-key validation.
  - **Verify**: `uv run pytest tests/unit/test_config.py -v`

- [x] **1.6 Unit tests — retry**
  - **Files**: `tests/unit/test_client.py`
  - **Outcome**: Immediate success, retry on 429, attempt limit, no retry on non-retryable 4xx.
  - **Verify**: `uv run pytest tests/unit/test_client.py -v`

---

## 2.0 TTS and STT

**Bar**: Sync + HTTP stream + WebSocket TTS; batch + realtime STT; VCR integration for TTS sync/stream and batch STT.

- [x] **2.1 Synchronous TTS**
  - **Files**: `src/eleven_demo/tts/sync.py`, `tests/unit/tts/test_sync.py`
  - **Outcome**: `synthesize()` + metadata (`with_raw_response`, character billing).
  - **Verify**: `uv run pytest tests/unit/tts/test_sync.py -v`

- [x] **2.2 HTTP streaming TTS + TTFB**
  - **Files**: `src/eleven_demo/tts/stream.py`, `tests/unit/tts/test_stream.py`
  - **Outcome**: Iterator `(chunk, ttfb | None)` with TTFB on first chunk.
  - **Verify**: `uv run pytest tests/unit/tts/test_stream.py -v`

- [x] **2.3 WebSocket TTS (input streaming)**
  - **Files**: `src/eleven_demo/tts/ws.py`, `tests/unit/tts/test_ws.py`
  - **Outcome**: Async `ws_stream`; auth via header.
  - **Verify**: `uv run pytest tests/unit/tts/test_ws.py -v`

- [x] **2.4 Batch STT**
  - **Files**: `src/eleven_demo/stt/batch.py`, `src/eleven_demo/stt/types.py`, `tests/integration/stt/test_batch.py`
  - **Outcome**: `transcribe()` with PT-BR-friendly defaults; VCR cassette.
  - **Verify**: `uv run pytest tests/integration/stt/test_batch.py -v`

- [x] **2.5 Realtime STT (WebSocket)**
  - **Files**: `src/eleven_demo/stt/realtime.py`, `tests/unit/stt/test_realtime.py`
  - **Outcome**: Partial/committed events; default model `scribe_v2_realtime` via settings.
  - **Verify**: `uv run pytest tests/unit/stt/test_realtime.py -v`

- [x] **2.6 Integration — TTS sync + stream**
  - **Files**: `tests/integration/tts/test_integration_sync.py`, `test_integration_stream.py`, `cassettes/`
  - **Outcome**: Valid MP3 bytes + metadata; filtered headers in VCR.
  - **Verify**: `uv run pytest tests/integration/tts -v`

- [x] **2.7 Integration — batch STT + sample audio**
  - **Files**: `data/samples/hello-pt-br.mp3`, `tests/integration/stt/test_batch.py`
  - **Outcome**: Transcript contains expected substring (cassette).
  - **Verify**: `uv run pytest tests/integration/stt -v`

---

## 3.0 Voice catalog, metrics, exploration CLIs

- [x] **3.1 PT-BR Voice Library catalog**
  - **Files**: `src/eleven_demo/voices/catalog.py`, `tests/unit/voices/test_catalog.py`
  - **Outcome**: `VoiceCard`, `list_pt_br_voices`.
  - **Verify**: `uv run pytest tests/unit/voices/test_catalog.py -v`

- [x] **3.2 Latency metrics**
  - **Files**: `src/eleven_demo/metrics/latency.py`, `tests/unit/metrics/test_latency.py`
  - **Outcome**: `LatencyReport`, p95/mean/median.
  - **Verify**: `uv run pytest tests/unit/metrics/test_latency.py -v`

- [x] **3.3 CLI `tts_demo.py`**
  - **Files**: `scripts/tts_demo.py`
  - **Outcome**: Synthesis + Rich panel (cost, request id).
  - **Verify**: `uv run python scripts/tts_demo.py "Hello." --out artifacts/smoke.mp3` (with API key)

- [x] **3.4 CLI `tts_stream_ttfb.py`**
  - **Files**: `scripts/tts_stream_ttfb.py`
  - **Outcome**: N runs, TTFB table + aggregates.
  - **Verify**: `uv run python scripts/tts_stream_ttfb.py --n 3`

- [x] **3.5 CLI `stt_demo.py`**
  - **Files**: `scripts/stt_demo.py`
  - **Outcome**: Transcript + word table (sample rows).
  - **Verify**: `uv run python scripts/stt_demo.py data/samples/hello-pt-br.mp3`

- [x] **3.6 CLI `voices_pt_br.py`**
  - **Files**: `scripts/voices_pt_br.py`
  - **Outcome**: Rich table of PT-BR voices.
  - **Verify**: `uv run python scripts/voices_pt_br.py`

- [x] **3.7 OpenAI settings (optional benchmark)**
  - **Files**: `pyproject.toml`, `.env.example`, `src/eleven_demo/config.py`, `tests/unit/test_config.py`
  - **Outcome**: Optional `openai_api_key`; configurable OpenAI TTS model/voice/format.
  - **Verify**: `uv run pytest tests/unit/test_config.py -v`

- [x] **3.8 OpenAI streaming TTS adapter**
  - **Files**: `src/eleven_demo/benchmarks/openai_tts.py`, `tests/unit/benchmarks/test_openai_tts.py`
  - **Outcome**: `stream_openai_tts`, TTFB on first chunk; clear error without key.
  - **Verify**: `uv run pytest tests/unit/benchmarks/test_openai_tts.py -v`

- [x] **3.9 Vendor benchmark report models**
  - **Files**: `src/eleven_demo/benchmarks/tts_vendor.py`, `tests/unit/benchmarks/test_tts_vendor.py`
  - **Outcome**: `VendorRun`, `VendorSummary`, `VendorBenchmarkReport`, `VENDOR_CANONICAL_TEXT_SETS`, randomized provider order per round.
  - **Verify**: `uv run pytest tests/unit/benchmarks/test_tts_vendor.py -v`

- [x] **3.10 CLI `tts_vendor_benchmark.py`**
  - **Files**: `scripts/tts_vendor_benchmark.py`
  - **Outcome**: JSON + Rich table; clean exit without `OPENAI_API_KEY` or `DEFAULT_PT_VOICE_ID`.
  - **Verify**: `uv run python scripts/tts_vendor_benchmark.py --n 2` (with both keys and voice id)

- [x] **3.11 Vendor benchmark integration (optional VCR)**
  - **Files**: `tests/integration/benchmarks/`, `cassettes/`
  - **Outcome**: Record/replay with filtered headers (ElevenLabs + OpenAI).
  - **Verify**: `uv run pytest tests/integration/benchmarks -v`

- [x] **3.12 CLI Voice Isolator**
  - **Files**: `scripts/voice_isolator_demo.py`, `tests/unit/test_voice_isolator.py`
  - **Outcome**: Clean audio + metrics panel; mocked unit tests.
  - **Verify**: `uv run pytest tests/unit/test_voice_isolator.py -v`

---

## 4.0 ElevenAgents — factory, tools, KB, simulate

**SDK notes (keep when bumping `elevenlabs`)**

- Namespace: `get_client().conversational_ai.{agents,knowledge_base}`.
- Simulate module file: `conversation_sim.py`; public `from eleven_demo.agents import simulate`.
- Multi-turn: one `simulate_conversation` call per user line, chaining `partial_conversation_history`.
- KB: `create_from_text` / `create_from_file`; RAG via `get_or_create_rag_indexes`; `ensure_kb_file_uploaded` dedupes by name.
- `SimulationResult.conversation_id` may be `None` depending on platform payload.

- [x] **4.1 Agent factory (CRUD + upsert)**
  - **Files**: `src/eleven_demo/agents/factory.py`, `tests/unit/agents/test_factory.py`
  - **Outcome**: Create/update/list/delete; name-based idempotent `upsert_agent`.
  - **Verify**: `uv run pytest tests/unit/agents/test_factory.py -v`

- [x] **4.2 Server tools + Pydantic mocks**
  - **Files**: `src/eleven_demo/agents/tools.py`, `tests/unit/agents/test_tools.py`
  - **Outcome**: Telecom/banking/healthcare schemas + `TOOLS_REGISTRY`; no unnecessary raw PII echo.
  - **Verify**: `uv run pytest tests/unit/agents/test_tools.py -v`

- [x] **4.3 Knowledge base**
  - **Files**: `src/eleven_demo/agents/kb.py`, `tests/unit/agents/test_kb.py`
  - **Outcome**: Text/file upload, listing, RAG compute.
  - **Verify**: `uv run pytest tests/unit/agents/test_kb.py -v`

- [x] **4.4 Simulate wrapper**
  - **Files**: `src/eleven_demo/agents/conversation_sim.py`, `tests/unit/agents/test_simulate.py`
  - **Outcome**: Typed `SimulationResult`; multiple user lines.
  - **Verify**: `uv run pytest tests/unit/agents/test_simulate.py -v`

- [x] **4.5 Unit tests — agents**
  - **Files**: `tests/unit/agents/`
  - **Outcome**: Factory/tools/KB/simulate coverage.
  - **Verify**: `uv run pytest tests/unit/agents -v`

---

## 5.0 Vertical scenarios

- [x] **5.1 `Scenario` contract**
  - **Files**: `src/eleven_demo/scenarios/base.py`, `tests/unit/scenarios/test_base.py`
  - **Outcome**: Pydantic model + `_build_conversation_config`; `TOOL_NAMES` / `KB_IDS` aliases.
  - **Verify**: `uv run pytest tests/unit/scenarios/test_base.py -v`

- [x] **5.2 Telecom**
  - **Files**: `src/eleven_demo/scenarios/telecom.py`, `tests/unit/scenarios/test_telecom.py`
  - **Outcome**: Lookup + transfer tools; `upsert_agent` provisioning.
  - **Verify**: `uv run pytest tests/unit/scenarios/test_telecom.py -v`

- [x] **5.3 Banking + ZRM**
  - **Files**: `src/eleven_demo/scenarios/banking.py`, `tests/unit/scenarios/test_banking.py`
  - **Outcome**: Authenticated flow + banking tools; privacy `platform_settings`.
  - **Verify**: `uv run pytest tests/unit/scenarios/test_banking.py -v`

- [x] **5.4 Healthcare + KB seeds + RAG**
  - **Files**: `src/eleven_demo/scenarios/healthcare.py`, `data/kb/healthcare/*.md`, `tests/unit/scenarios/test_healthcare.py`
  - **Outcome**: Seed upload, RAG index, KB-linked agent; ZRM documented.
  - **Verify**: `uv run pytest tests/unit/scenarios/test_healthcare.py -v`

- [x] **5.5 Provision + simulate CLIs**
  - **Files**: `scripts/agent_create.py`, `scripts/agent_simulate.py`
  - **Outcome**: `telecom|banking|healthcare`; prints `agent_id` + simulate Rich panel.
  - **Verify**: `uv run python scripts/agent_create.py telecom` (with `.env`)

- [x] **5.6 Per-scenario integration regression**
  - **Files**: `tests/integration/scenarios/`, `tests/integration/scenarios/_support.py`, `cassettes/`
  - **Outcome**: 3-turn simulate; assert tool/shape signals, not free-text LLM wording.
  - **Verify**: `uv run pytest tests/integration/scenarios -v`

---

## 6.0 Demo surfaces

- [x] **6.1 Gradio skeleton (6 tabs) + visual system**
  - **Files**: `apps/gradio_app.py`, `docs/design/visual-system.md`, `docs/design/assets/`
  - **Outcome**: Tabs, theme, ElevenAgents / ElevenAPI naming; local design tokens.
  - **Verify**: `uv run python apps/gradio_app.py` (local smoke)

- [x] **6.2 TTS Playground tab**
  - **Files**: `apps/gradio_app.py`
  - **Outcome**: Voice, settings, formats (incl. telephony), normalization, models, JSON metadata.
  - **Verify**: Generate audio in UI

- [x] **6.3 Telecom + Banking tabs (widget + signed URL)**
  - **Files**: `apps/gradio_app.py`, `docs/scenarios/telecom.md`, `banking.md`
  - **Outcome**: ConvAI embed; “why this matters” Markdown panel.
  - **Verify**: Start conversation in UI

- [x] **6.4 Healthcare tab + RAG sources panel**
  - **Files**: `apps/gradio_app.py`, `docs/scenarios/healthcare.md`
  - **Outcome**: KB document list wired to scenario seeds.
  - **Verify**: Widget + source list

- [x] **6.5 Latency tab**
  - **Files**: `apps/gradio_app.py`
  - **Outcome**: Chart + samples + aggregate JSON (Flash/Multilingual).
  - **Verify**: “Run benchmark” in UI

- [x] **6.6 Vendor benchmark tab**
  - **Files**: `apps/gradio_app.py`
  - **Outcome**: `run_vendor_benchmark`; hint if OpenAI missing; short methodology copy.
  - **Verify**: With both keys, rows for both providers

- [x] **6.7 Next.js + `elevenlabs/ui` (stretch)**
  - **Files**: `apps/web/**` (App Router, `telecom-agent-console`, `/api/signed-url`, pnpm)
  - **Outcome**: `Orb`, `ConversationBar`, `LiveWaveform`; same `DEMO_AGENT_ID_TELECOM` as Gradio; key server-only.
  - **Verify**: `pnpm --dir apps/web dev` and `pnpm build`

- [x] **6.8 FastAPI WebSocket bridge (stretch)**
  - **Files**: `apps/ws_bridge/main.py`, `tests/unit/apps/ws_bridge/test_main.py`
  - **Outcome**: `/healthz`, `/ws/tts` proxy to TTS WS; local dev only.
  - **Verify**: `uv run pytest tests/unit/apps/ws_bridge/test_main.py -v`

---

## 7.0 Documentation and narrative

- [x] **7.1 Telecom storytelling** — `docs/scenarios/telecom.md` (FR-30: persona, problem, flow, ROI, risks, refs).
- [x] **7.2 Banking storytelling** — `docs/scenarios/banking.md` (BACEN/LGPD/PCI/ZRM posture).
- [x] **7.3 Healthcare storytelling** — `docs/scenarios/healthcare.md` (KB, RAG, LGPD).
- [x] **7.4 End-to-end walkthrough** — `docs/walkthrough.md` (Gradio, optional React, bridge, skills).
- [x] **7.5 README polish** — `README.md` (quick start, two surfaces, links, project tree under 350 lines per PRD).
- [x] **7.6 Post-call without webhook** — `scripts/conversations_list.py`; ADR in `tech-stack-decisions.md`; walkthrough link.
- [x] **7.7 TTS vendor methodology** — `docs/benchmarks/tts-vendor-comparison.md`.
- [x] **7.8 Technical exploration report** — `docs/reports/technical-exploration-report.md`.
- [x] **7.9 `elevenlabs/ui` discovery** — optional local notes at repo root (gitignored) or narrative in `docs/reports/`.

---

## 8.0 Release gates and evidence

Run after phases 1–7 land (full snapshot also in [technical report §6](../../docs/reports/technical-exploration-report.md)):

| Gate | Command / action |
| --- | --- |
| Fast tests | `uv run pytest -n auto --junitxml=artifacts/reports/pytest.xml -m "not integration"` |
| Coverage ≥80% | `uv run pytest --cov=src/eleven_demo --cov-report=xml:artifacts/reports/coverage.xml --cov-report=html:artifacts/reports/htmlcov --cov-fail-under=80 -m "not integration"` |
| Lint / format | `uv run ruff check .` and `uv run ruff format --check .` |
| Pre-commit | `uv run pre-commit run --all-files` (e.g. `tee artifacts/reports/pre-commit.txt`) |
| Integration | `uv run pytest -m integration --junitxml=artifacts/reports/integration-pytest.xml` |
| Vendor smoke | `uv run python scripts/tts_vendor_benchmark.py --n 1 --out artifacts/benchmarks/tts-vendor-latest.json` (keys + `DEFAULT_PT_VOICE_ID`) |
| Report | Refresh snapshot in `docs/reports/technical-exploration-report.md` |
| Optional Node | `pnpm --dir apps/web install --frozen-lockfile && pnpm --dir apps/web build` |

- [x] **8.1 Evidence artifacts**
  - **Files**: `scripts/generate_evidence_report.py`; outputs under `artifacts/reports/`, `artifacts/benchmarks/` (gitignored).
  - **Outcome**: JUnit, Cobertura XML/HTML, pre-commit log, optional vendor JSON; Markdown digest via script.
  - **Verify**: gates above + `uv run python scripts/generate_evidence_report.py`

**Security**: do not store API keys, PII, or full transcripts in committed artifacts.

---

## Conventions (short)

- **Tests**: daily `uv run pytest -n auto -m "not integration"`; coverage **without** xdist (see `.cursor/rules/testing-standards.mdc`).
- **Model truth**: official docs → installed SDK → [`elevenlabs/skills`](https://github.com/elevenlabs/skills) → `.cursor/skills/`.
- **Commits**: [Conventional Commits](https://www.conventionalcommits.org/).
