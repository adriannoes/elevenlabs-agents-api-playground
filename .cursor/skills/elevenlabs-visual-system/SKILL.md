---
name: elevenlabs-visual-system
description: Apply ElevenLabs-inspired visual design guidance for the local Gradio demo. Use when creating or editing apps/gradio_app.py, docs/design/visual-system.md, docs/design/assets/logos or symbols, UI copy, demo tabs, CSS, visual tokens, brand usage, logo usage, or any localhost demo experience for ElevenAgents or ElevenAPI.
license: MIT
compatibility: Local UI and branding for this repo; no API call required unless the edited tab invokes ElevenLabs APIs.
---

# ElevenLabs Visual System

Product-agnostic UX skills from ElevenLabs live at [github.com/elevenlabs/skills](https://github.com/elevenlabs/skills); this file is demo-specific styling only.

## Source of Truth

Before making UI or brand-related changes, read:

- `docs/design/visual-system.md` (canonical paths: **`docs/design/assets/logos/`**, **`docs/design/assets/symbols/`**)
- Official brand page: `https://elevenlabs.io/brand`

Treat `docs/design/visual-system.md` as the local implementation guide. Treat the official brand
page as the legal / brand source of truth. Store checked-in official downloads under
`docs/design/assets/logos/` or `docs/design/assets/symbols/` only.

## Core Rule

The Gradio app is **brand-inspired**, not an official ElevenLabs product. Never imply official
ownership or endorsement.

## Naming

Use exact written forms:

- `ElevenLabs`
- `ElevenAgents`
- `ElevenAPI`
- `ElevenCreative`

Avoid:

- `Eleven Labs`
- `Eleven Agents`
- `Eleven API`
- `Elevenlabs`
- all-caps variants
- text approximations of the `11` symbol

## Visual Direction

For ElevenAgents / voice-agent areas:

- Use blue accents.
- Prefer soft gradients, circles, spheres, orb-like status elements, waveforms, and generous
  whitespace.
- Make readiness / listening / responding states clear with text labels and color.

For ElevenAPI / benchmark areas:

- Use monochrome / neutral palettes.
- Favor crisp tables, metric cards, request metadata, compact charts, and minimal decoration.
- Keep benchmark UI evidence-based: raw samples, median, p95, caveats.

## Logo and Symbol Guardrails

- Do not recreate the ElevenLabs logo or symbol in CSS, SVG, ASCII, icons, or typography.
- Do not recolor, rotate, stretch, outline, shadow, distort, or animate official assets.
- If assets are needed, use only assets downloaded from the official brand page and checked into
  `docs/design/assets/logos/` or `docs/design/assets/symbols/` (never approximate in CSS/SVG).
- Keep required clearance around official assets.
- Prefer text labels over logo usage unless a brand asset is truly necessary.

## Implementation Pattern

When editing `apps/gradio_app.py`:

1. Use `gr.Blocks(theme=gr.themes.Soft())`.
2. Add a concise landing/header area with:
   - demo purpose
   - API-key readiness chips
   - agent ID readiness
   - links to report / benchmark docs
   - note that the UI is brand-inspired, not official
3. Use local CSS variables from `docs/design/visual-system.md`.
4. Keep CSS colocated in `apps/gradio_app.py` while compact.
5. Move CSS to `apps/static/demo.css` only if it becomes hard to read.

## Verification Checklist

- [ ] Platform names are correct.
- [ ] No official logo/symbol misuse.
- [ ] Agent tabs visually differ from API/benchmark tabs.
- [ ] Color is not the only status signal.
- [ ] Missing credentials show setup guidance, not stack traces.
- [ ] UI still works on laptop-width viewport.
