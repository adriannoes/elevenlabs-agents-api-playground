# Task Template

Use this template when generating task lists with `.cursor/commands/generate-tasks.md`. It enforces explicit context for each sub-task so a junior developer (or weaker AI model) can execute without re-reading the PRD.

## Top-level structure

```markdown
# Task List — [PRD Name]

**Source PRD**: `product/prd/prd-[feature-name].md`

## Relevant Files

- `path/to/source/file.py` — Brief description of why this file is touched.
- `tests/path/to/test_file.py` — Unit tests for `file.py`.

### Notes

- Unit tests live in `tests/unit/` mirroring `src/eleven_demo/` layout.
- Integration tests live in `tests/integration/` and use VCR cassettes.
- Run a focused test with `uv run pytest tests/unit/test_xxx.py -v`.

## Tasks

- [ ] 1.0 Parent task title
  **Acceptance criteria:**
  - Specific, verifiable outcome owned by this parent task.
  - Another verifiable outcome.

  - [ ] 1.1 Sub-task with detailed format (see below)
  - [ ] 1.2 Another sub-task

- [ ] 2.0 Parent task title
  **Acceptance criteria:**
  - ...

  - [ ] 2.1 ...
```

## Detailed sub-task format

```markdown
- [ ] X.Y [Action verb] [specific item]
  - **File**: `path/to/file.py` (create new | modify existing)
  - **What**: [Detailed description of what to create or modify.]
  - **Why**: [Context — why this is needed, how it fits the bigger picture.]
  - **Pattern**: [Reference to existing code or skill, e.g. "Follow snippet in `.cursor/skills/elevenlabs-api-cookbook/SKILL.md` section 'TTS sync convert'".]
  - **Verify**: [How to confirm it works — exact command or expected output.]
  - **Integration** (optional): [How this output is consumed elsewhere — e.g. "Imported by `scripts/tts_demo.py`".]
```

## Dependencies block (when applicable)

For any task that is part of a flow, add this block at the top of the parent task:

```markdown
**Trigger / entry point:** What invokes this work (user action, cron job, previous task, etc.).
**Enables:** What this task unblocks (other tasks, features, schema fields, APIs).
**Depends on:** What must already exist (other tasks, environment variables, files).
```

## Good vs Bad sub-tasks

### Bad (too vague)
```markdown
- [ ] 1.1 Add TTS sync function
```

### Good (explicit and contextual)
```markdown
- [ ] 1.1 Implement synchronous text-to-speech function
  - **File**: `src/eleven_demo/tts/sync.py` (create new)
  - **What**: Function `synthesize(text: str, voice_id: str, model_id: str = "eleven_flash_v2_5", output_format: str = "mp3_22050_32") -> bytes` that calls `client.text_to_speech.convert` and returns concatenated audio bytes.
  - **Why**: Foundation for all non-streaming demos. Used by `scripts/tts_demo.py` and the Gradio TTS Playground tab.
  - **Pattern**: Follow snippet in `.cursor/skills/elevenlabs-api-cookbook/SKILL.md` under "Sync convert (file output)". Wrap in `try/except elevenlabs.core.ApiError` per `.cursor/rules/elevenlabs-conventions.mdc` rule 7.
  - **Verify**: `uv run pytest tests/unit/tts/test_sync.py -v` passes; `uv run python -c "from eleven_demo.tts.sync import synthesize; print(len(synthesize('hi', voice_id='JBFqnCBsd6RMkjVDRZzb')))"` prints a non-zero integer.
  - **Integration**: Returned bytes consumed by `scripts/tts_demo.py` (writes to `out.mp3`) and `apps/gradio_app.py` (TTS Playground tab).
```

## Acceptance criteria rules

- Every parent task has its own AC.
- AC must be **verifiable** (a command, an observable behavior, or a clear binary condition).
- AC must describe an outcome **owned by that task** — never another task's outcome.

## Status conventions

- `[ ]` = pending
- `[x]` = completed
- `[~]` = in progress (optional, useful when pausing mid-parent)
- `[-]` = cancelled / no longer needed

## Workflow with `.cursor/commands/development.md`

When using the `/development` command to execute the list:

1. Open the task list file.
2. Read the next pending sub-task (File / What / Why / Pattern / Verify).
3. Implement.
4. Run the Verify command.
5. Mark sub-task as `[x]`.
6. Stop and confirm with the user before starting the next sub-task (per `/development`).

When all sub-tasks of a parent are `[x]`, mark the parent `[x]` too. Update the "Relevant Files" section as new files are created.
