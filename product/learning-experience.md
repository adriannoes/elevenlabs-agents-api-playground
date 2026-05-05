> A first-person memo from a developer who spent a few days building a real Python integration against the ElevenLabs platform, using only the public docs, to learn the product end-to-end. Some of the friction here is the same friction a customer integration team surfaces when shipping to production — written as a field note, not a bug report.

**Repo**: <https://github.com/adriannoes/elevenlabs-agents-api-playground>

---

## Why this exists

I wanted hands-on intuition for how ElevenAgents and ElevenAPI fit together when you have to ship something realistic — Brazilian-market voice agents in telecom, banking, and healthcare, with proper tests, a Gradio playground, and a TTS latency benchmark vs another vendor. The repo above is that lab.

I deliberately constrained myself to **only the public surfaces** I would have as a new developer: the [official documentation](https://elevenlabs.io/docs), the installed `elevenlabs` Python SDK, and the [official `elevenlabs/skills` GitHub bundle](https://github.com/elevenlabs/skills). No internal channels, no office hours, no Discord shortcuts. The point was to feel the developer journey, not to pass it.

What follows is what I noticed while doing that — written as a field note, not a bug report. If I noticed it as a single developer, customer integration teams will too, and at meaningful scale.

---

## How I navigated the platform

I started with the docs alone. Mid-way through, I discovered the [`elevenlabs/skills`](https://github.com/elevenlabs/skills) bundle — specifically because the [ElevenAPI quickstart on the docs site itself](https://elevenlabs.io/docs/eleven-api/quickstart) opens with:

> "Use the [ElevenLabs text-to-speech skill](https://github.com/elevenlabs/skills/tree/main/text-to-speech) to generate speech from your AI coding assistant: `npx skills add elevenlabs/skills --skill text-to-speech`"

That is a strong, deliberate signal. The docs are explicitly promoting the skills bundle as the recommended onboarding path for any developer working inside an AI coding assistant. So I added it to my exploration: I read every skill in the bundle, compared its examples to my own ad-hoc cookbook, and pulled in patterns that were missing locally (the front-matter conventions, the voice-isolator workflow, and the explicit `@elevenlabs/elevenlabs-js` warning).

After spending time across all of these surfaces, I converged on this hierarchy of trust:

1. **Official docs** (`elevenlabs.io/docs`) — `llms.txt` as the index, then the specific page (`/docs/overview/models`, `/docs/api-reference/...`, `/docs/eleven-agents/...`). **Canonical** for model IDs, deprecation, parameter schemas, and endpoint behavior.
2. **Installed SDK** — `inspect.signature(client.X.Y)` against the version pinned in `pyproject.toml`. Tells me what code can actually run today; used to break ties when docs and intuition disagree.
3. **`elevenlabs/skills` bundle** — promoted by the docs as the recommended onboarding entry point for AI coding assistants. Effectively the first developer-facing artifact I touched after installing the SDK. Should inherit from (1).
4. **Local cookbooks I'd written for myself** — convenience layer; assumed to drift over time and re-verified against (1) and (2) before each milestone.

I encoded this lookup protocol as a Cursor skill in the repo ([`.cursor/skills/elevenlabs-docs/SKILL.md`](https://github.com/adriannoes/elevenlabs-agents-api-playground/blob/main/.cursor/skills/elevenlabs-docs/SKILL.md)) so future contributors don't have to re-derive it.

The "source of truth" question only matters when surfaces disagree. The points below are where I noticed that, after re-fetching every page on 2026-05-05 to make sure the observations still hold.

---

## What I noticed: places where the surfaces could be more in sync

Each row was verified directly against the URL on the right, on 2026-05-05. All of these surfaces are ElevenLabs-owned and consistent with each other in intent — these are observations about places where I'd love to see them synchronized so a new developer can't accidentally land on the wrong path.

### 1. Turbo models — two ElevenLabs surfaces give different recommendations

The upstream skill [`text-to-speech/SKILL.md`](https://github.com/elevenlabs/skills/blob/main/text-to-speech/SKILL.md) lists `eleven_turbo_v2_5` and `eleven_turbo_v2` in its Models table next to Flash, with no deprecation note:

> `eleven_turbo_v2_5` | 32 | ~250-300ms | Balanced quality/speed
>
> `eleven_turbo_v2` | English | ~250-300ms | English-only, balanced

The canonical [Models page](https://elevenlabs.io/docs/overview/models) lists the same two IDs under **Deprecated models** with this guidance:

> "The `eleven_turbo_v2_5` and `eleven_turbo_v2` models are functionally equivalent to the `eleven_flash_v2_5` and `eleven_flash_v2` models respectively, except the latency on the Flash models is lower on average. We recommend using the Flash models over Turbo models in all use cases."

Both pages are accurate in isolation; they just point in different directions. A developer who follows the docs site's quickstart instruction to `npx skills add elevenlabs/skills` will land on the bundle's table first.

### 2. STT model IDs are easy to copy stale

The current realtime STT model per [`/docs/overview/models`](https://elevenlabs.io/docs/overview/models) is `scribe_v2_realtime`. The current batch model is `scribe_v2`. `scribe_v1` is listed in that same page as: *"State-of-the-art speech recognition. Outclassed by v2 models."*

The upstream [`speech-to-text/SKILL.md`](https://github.com/elevenlabs/skills/blob/main/speech-to-text/SKILL.md) is aligned on the model IDs (`scribe_v2`, `scribe_v2_realtime`) — which is exactly the consistency I'd love to see applied across the rest of the bundle. One smaller drift on the same surface, worth flagging because it's the kind of number a developer will pin in code: the canonical [Models page](https://elevenlabs.io/docs/overview/models) advertises *"Keyterm prompting, up to 1000 terms"* for Scribe v2, while the skill caps it at *"up to 100 terms"* — same feature, 10× difference.

The silent-failure dimension: nothing in the SDK rejects `scribe_v1`. Requests succeed, transcripts come back, costs accumulate. A developer who found `scribe_v1` in an older cookbook (including, frankly, an early version of mine) won't get a runtime signal that they're on a non-recommended model.

### 3. The skills bundle is on the critical path for new developers

[`/docs/eleven-api/quickstart`](https://elevenlabs.io/docs/eleven-api/quickstart) opens with:

> "Use the [ElevenLabs text-to-speech skill](https://github.com/elevenlabs/skills/tree/main/text-to-speech) to generate speech from your AI coding assistant: `npx skills add elevenlabs/skills --skill text-to-speech`"

[`/docs/eleven-api/guides/cookbooks/voice-isolator`](https://elevenlabs.io/docs/eleven-api/guides/cookbooks/voice-isolator) opens with the same pattern, recommending the voice-isolator skill.

This is great — it's a deliberate, modern developer-experience choice and I appreciated landing on it. The flip side: the bundle is now load-bearing for the documentation experience itself. Drift in a single skill (like point 1) is felt on Day 0 of integration, not in some advanced corner.

### 4. Three different `elevenlabs*` JS packages, no single map between them

Three distinct npm packages share the `elevenlabs` namespace, and a new developer has to figure out which one belongs to which surface:

- `elevenlabs` — the deprecated v1.x package the [`elevenlabs/skills` README](https://github.com/elevenlabs/skills/blob/main/README.md) explicitly warns about: *"Always use `@elevenlabs/elevenlabs-js`. Do not use `npm install elevenlabs` (that's an outdated v1.x package)."*
- `@elevenlabs/elevenlabs-js` — the **ElevenAPI** SDK (TTS, STT, voice isolation, etc.). Used in the [ElevenAPI quickstart](https://elevenlabs.io/docs/eleven-api/quickstart) and across the skills bundle.
- `@elevenlabs/client` — the **ElevenAgents** client (Conversation, WebRTC/WebSocket). The [JavaScript SDK page under `/eleven-agents/libraries`](https://elevenlabs.io/docs/eleven-agents/libraries/java-script) installs this one with `npm install @elevenlabs/client`.

The deprecation warning lives only in the skills README. The ElevenAPI and ElevenAgents docs each correctly use their own package, but neither one cross-links to the other or to the warning. A developer who searches npm directly for "elevenlabs" — or who jumps from the ElevenAPI quickstart to the Agents SDK page expecting the same import — has to triangulate the relationship from scratch.

---

## Why this matters at deployment scale

Each individual point is small. Any experienced developer would shrug, re-check the docs, swap an ID, and move on — minutes lost.

What's worth surfacing is the **pattern** these points share, because of how the platform positions its own surfaces:

- The docs themselves promote the **`elevenlabs/skills` bundle as the recommended Day-0 entry** for AI-coding-assistant developers (per the ElevenAPI quickstart). That makes the bundle effectively part of the documentation experience, not just an adjacent asset.
- The bundle, the API reference, the model lifecycle page, and any cookbook pages a developer reads are **multiple authoritative surfaces for the same facts** (model IDs, package names, deprecation). When they don't move together, the developer gets the version that arrived first.
- Several of the relevant differences are **silent at runtime** — `scribe_v1` and `eleven_turbo_v2_5` both still work; the SDK doesn't surface that they're not the recommended choice.

For a team integrating ElevenLabs into a customer product, this turns into:

- A handful of minutes per developer per onboarding to triangulate "which model should I actually pin in this scenario?"
- A trickle of POCs that ship with deprecated models because the first-found example used them.
- Friction concentrated at the moment someone is trying to convert a POC into a production rollout, not at the friendly demo stage.

The cost isn't in any single drift. It's in **the repeated time tax of explaining which surface to trust on a given day**.

---

## Things that worked beautifully

To stay calibrated — these stood out as best-in-class while I was building:

- [`/docs/llms.txt`](https://elevenlabs.io/docs/llms.txt) is an underrated developer asset. Index-first navigation made fetching the right page in a Cursor agent loop trivial. Most platforms don't ship this.
- [`/docs/overview/models`](https://elevenlabs.io/docs/overview/models) is exceptionally clear. The deprecation table with explicit replacement suggestions ("use `eleven_flash_v2_5` instead of `eleven_turbo_v2_5`") is the right pattern — I just want every other surface to obey it.
- The [Agents Platform docs](https://elevenlabs.io/docs/eleven-agents/overview) separate **Configure / Deploy / Monitor** (the URL paths still read `/build/`, `/integrate/`, `/operate/`) in a way that mirrors how a customer team actually divides the work. That mental model alone shortened my repo's scenario design by a couple of evenings.
- The Python SDK's namespacing under `client.conversational_ai.*` for agents and KB matches what the docs describe. When I had to confirm a method name, `inspect.signature(...)` and the docs agreed. That's a low bar that is somehow rare in voice/AI SDKs.

---

## What only live smoke tests surfaced

After the docs-driven implementation was in place, the most useful learning came from running a small paid smoke test against the live platform. The unit tests had the right shape, but the live API exposed integration details that mocks did not.

First, Agents webhook tools required a stricter `request_body_schema` than a direct Pydantic JSON Schema dump. The API correctly rejected the payload and showed exactly where the schema was wrong, but I had to inspect the installed SDK types to learn the subset it expected: literal properties with descriptions, no `title`, no `additionalProperties`, and no `anyOf` for nullable values. A complete Python example for webhook tool schemas would save customer teams time here.

Second, `simulate_conversation` behaved like a real platform feature rather than a simple unit-test helper. Sending `partial_conversation_history=None` failed where an empty list was expected, and the default simulated user persona behaved like an AI assistant until I explicitly prompted it to act like a Brazilian customer. That is useful power, but the docs could make the "realistic simulated user" pattern more obvious, including the first-turn empty-history shape and realistic timeout expectations for longer simulations.

Third, Voice Isolator worked well, but the first live call failed because the generated audio was below the minimum duration. The API error was clear and actionable; the cookbook would be even better if it mentioned the minimum input duration before the first request.

Fourth, Voice Library labels were not stable enough for a naive locale filter. `voices_pt_br.py` reached the API successfully, but no voices came back with the expected PT-BR metadata. The right product behavior was a fallback: show a small sample and ask the developer to set `DEFAULT_PT_VOICE_ID` manually. If Voice Library search is meant to support locale-based selection, a documented set of stable labels or a recommended "find a Portuguese voice" snippet would reduce onboarding friction.

None of these were blockers. They were the normal last-mile integration details a solutions or integration engineer would uncover with a customer team. The broader lesson is that the ElevenLabs docs are strong for navigation and concepts, but production-shaped examples benefit from including the exact runtime contract: accepted schema shape, minimum input constraints, timeout expectations, and realistic simulation prompts.

---

## Discovering `elevenlabs/ui`

*Verified package URLs and cross-links below on 2026-05-05.*

### When / how the registry showed up

After the Gradio skeleton landed (**Task 6.1** in the companion repo) and embed paths were clear, the next step was a **second adoption path**: the same provisioned Telecom agent in a **Next.js** shape, which is how many product teams ship. The registry showed up primarily as a **public GitHub project** and docs site — [elevenlabs/ui](https://github.com/elevenlabs/ui) and [ui.elevenlabs.io](https://ui.elevenlabs.io/) — not through the [elevenlabs-python](https://github.com/elevenlabs/elevenlabs-python) README (that file stays focused on HTTP clients and `Conversation` patterns). Installation is documented as `npx @elevenlabs/cli@latest components add <component-name>`, or with shadcn: run `npx shadcn@latest add` plus a registry JSON URL such as https://ui.elevenlabs.io/r/orb.json (swap `orb` for another component name), per the [ElevenLabs UI README](https://github.com/elevenlabs/ui/blob/main/README.md).

### What the registry exposes

The catalog publishes agent/audio-oriented components on top of [shadcn/ui](https://ui.shadcn.com/) and Tailwind; the index is [Components · ElevenLabs UI](https://ui.elevenlabs.io/docs/components).

**Names from the exploration checklist (catalog / docs naming):** `orb`, `conversation`, `conversation-bar`, `message`, `transcript-viewer`, `live-waveform`, `waveform`, `voice-button`, `voice-picker`, `mic-selector`, `audio-player`, `scrub-bar`, `speech-input`, `response`, `shimmering-text`, `bar-visualizer`, `matrix`.

**Consumed in this repo’s `apps/web/`:** `Orb`, `ConversationBar`, and `LiveWaveform` in [`components/telecom-agent-console.tsx`](https://github.com/adriannoes/elevenlabs-agents-api-playground/blob/main/apps/web/components/telecom-agent-console.tsx) (shadcn-style copies under `components/ui/`).

| Package / area | Role | Link |
| --- | --- | --- |
| `@elevenlabs/react` | Hooks (e.g. `useConversation`) for Agents | [npm `@elevenlabs/react`](https://www.npmjs.com/package/@elevenlabs/react) |
| `@elevenlabs/elevenlabs-js` | Server client for signed URLs in the Route Handler | [npm `@elevenlabs/elevenlabs-js`](https://www.npmjs.com/package/@elevenlabs/elevenlabs-js) |
| `three` | 3D for Orb | [three.js](https://github.com/mrdoob/three.js) |
| `@react-three/fiber` | React renderer for Three.js | [R3F](https://github.com/pmndrs/react-three-fiber) |
| `@react-three/drei` | Scene helpers | [drei](https://github.com/pmndrs/drei) |
| `lucide-react` | Icons | [lucide-react](https://lucide.dev/) |
| shadcn/ui + Tailwind | Registry component pattern | [shadcn/ui](https://ui.shadcn.com/), [Tailwind](https://tailwindcss.com/) |
| Next.js 14+ | App Router host | [Next.js](https://nextjs.org/) |

Direct deps match [`apps/web/package.json`](https://github.com/adriannoes/elevenlabs-agents-api-playground/blob/main/apps/web/package.json). **`framer-motion`** does not appear in this app’s `pnpm-lock.yaml` for the three components above; other registry blocks may add it — run `pnpm why framer-motion` after pulling more components.

### Decision

The UI registry **complements** Gradio: Python + `uv` remain the breadth surface for ElevenAPI, scenarios, and tests. Optional **`apps/web/`** is one conversation page — **not** a mandate to migrate the repo to React. ADR-style notes: [tech-stack-decisions.md](https://github.com/adriannoes/elevenlabs-agents-api-playground/blob/main/engineering/architecture/tech-stack-decisions.md) (`elevenlabs/ui` evaluation).

### Friction after Task 6.7 (implemented)

- **Dual toolchain:** `pnpm` and Node 20+ beside `uv` and Python; two lockfiles (`pnpm-lock.yaml` vs `uv.lock`).
- **Signed URL boundary:** [`app/api/signed-url/route.ts`](https://github.com/adriannoes/elevenlabs-agents-api-playground/blob/main/apps/web/app/api/signed-url/route.ts) keeps `ELEVENLABS_API_KEY` server-side; audit client bundles for accidental `NEXT_PUBLIC_*` secrets.
- **Env parity:** Python uses `.env`; Next uses `.env.local` — same variable names, two files ([apps/web/README.md](https://github.com/adriannoes/elevenlabs-agents-api-playground/blob/main/apps/web/README.md)).
- **Bundle size:** `three` + R3F stacks are heavy; fine for one demo page, watch before mobile-first reuse.
- **Quality gates:** Node surface sits **outside** Python pre-commit / coverage — optional `pnpm --dir apps/web build` per Task **8.0**.

### How `elevenlabs/ui`, `elevenlabs/skills`, and `elevenlabs-python` relate

Parallel public entry points: [elevenlabs/ui](https://github.com/elevenlabs/ui) targets **React** installs ([`npx @elevenlabs/cli@latest components add …`](https://github.com/elevenlabs/ui/blob/main/README.md)); [elevenlabs/skills](https://github.com/elevenlabs/skills) is the bundle promoted from the [ElevenAPI quickstart](https://elevenlabs.io/docs/eleven-api/quickstart); [elevenlabs-python](https://github.com/elevenlabs/elevenlabs-python) documents the **Python SDK** and points at [API reference](https://elevenlabs.io/docs/api-reference), not the UI kit — expected, since **`elevenlabs/ui`** is a **Next.js** concern. Teams still combine them with shared **agent IDs** and **signed URLs**, as wired between `apps/gradio_app.py` and `apps/web/`.

---

## A few low-effort mechanisms that would help

I'm offering these as a developer who'd be glad to be wrong about scope, not as prescriptions:

1. A **single source-of-truth file for model IDs** generated from `/docs/overview/models` and consumed by every cookbook page and every `elevenlabs/skills` bundle, so the deprecation table can never lag.
2. A **"last verified against docs vN"** footer on each cookbook page and skill `SKILL.md`, with a CI check that compares against the live docs index.
3. A small **"if you're new here"** pointer at the top of the docs landing page that maps the three JS packages to their surfaces (`@elevenlabs/elevenlabs-js` for ElevenAPI, `@elevenlabs/client` for ElevenAgents, deprecated `elevenlabs` for neither) — the same warning the skills bundle already carries, plus the cross-link the Agents page is missing today.
4. A **drift-check GitHub Action** in `elevenlabs/skills` that diffs each skill's model table against `/docs/overview/models` weekly and opens an issue or PR when they disagree. (Happy to prototype this; the diff is mechanical.)

None of this is novel. All of it is the kind of small mechanism that turns "developer friction" into "developer delight" without changing the product.

---

## About the companion repository

<https://github.com/adriannoes/elevenlabs-agents-api-playground>

It's a Python lab built to explore the platform end-to-end against three Brazilian-market voice scenarios. Highlights worth a quick look:

- **`src/eleven_demo/client.py`** — single `get_client()` factory with REST retries on 429 / 5xx and a 30 s timeout. One way in, no scattered SDK calls.
- **`src/eleven_demo/scenarios/{telecom,banking,healthcare}.py`** — typed scenario contracts with idempotent `provision()`, server tools as Pydantic models, and a Healthcare scenario that uploads a small fictional KB and computes a RAG index.
- **`src/eleven_demo/benchmarks/`** + **`scripts/tts_vendor_benchmark.py`** — TTFB benchmark comparing ElevenLabs Flash v2.5 against an OpenAI TTS baseline. Headline metric is time-to-first-byte because that's what users actually feel in conversation.
- **`apps/web/`** — optional Next.js page using the official [`elevenlabs/ui`](https://github.com/elevenlabs/ui) registry (`Orb`, `ConversationBar`, `LiveWaveform`) and a server-side signed URL; same Telecom `agent_id` as Gradio.
- **`.cursor/skills/`** — the four skills I wrote during the work, including the `elevenlabs-docs` lookup protocol that surfaced everything in this memo. They follow the [Agent Skills](https://agentskills.io/specification) front matter convention so they could, in principle, be installed alongside the upstream bundle.
- **Tests** — unit tests across config, retry behavior, scenarios, tools, and metrics. Integration tests use VCR cassettes so CI can replay without burning API credits.

The goal of the repo was learning, not shipping. The goal of this memo is to make some of that learning useful to the people who maintain the platform.
