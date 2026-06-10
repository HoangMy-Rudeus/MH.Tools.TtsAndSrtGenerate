# Handover — Console UI (TUI) v2 (Editor + Audio Replay)

**Purpose:** Track v2 implementation progress for pause/resume.

- **Branch:** `feature/console-ui-v2` (off `main`, which has v1 merged)
- **Plan:** `docs/superpowers/plans/2026-06-11-tts-console-ui-v2.md` (6 tasks, TDD)
- **Spec:** `docs/superpowers/specs/2026-06-11-tts-console-ui-v2-design.md`

## How to resume
1. `git checkout feature/console-ui-v2`
2. Find the next `TODO` task below; open the plan at that task and execute its steps.
3. After a task: tick plan checkboxes, mark `DONE` here with the commit SHA, set next `IN PROGRESS`.
4. `python -m pytest -q` must be green before stopping.

## Status

| Task | Title | Status | Commit |
|------|-------|--------|--------|
| 1 | `script_io` (serialize + save Script) | DONE | `ada17f3` |
| 2 | `player` (ffplay wrapper + Fake) | DONE | `51d243d` |
| 3 | Wire `player` into AppState + TtsApp | DONE | `184ea50` |
| 4 | Audio replay in History screen | DONE | `44ff39f` |
| 5 | Editor screen + line-form modal | DONE | `2980db1` |
| 6 | Queue→Editor binding + verify + README | DONE | (this commit) |

Legend: TODO · IN PROGRESS · DONE · BLOCKED

**v2 COMPLETE.** All 6 tasks done. `python -m pytest -q` → 42 passed.
Branch `feature/console-ui-v2` ready to merge to `main`.

## Decisions (locked)
- Editor editing model: **per-line modal form** (DataTable of lines + add/edit modal).
- Audio replay via **ffplay** subprocess (non-blocking; stop on key / screen unmount / app exit).

## Environment notes
- Same as v1: ffmpeg (incl. `ffplay`) installed via winget, NOT on PATH. Bin dir:
  `C:\Users\Rudeus\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.1-full_build\bin`
- Baseline suite (v1 merged): 35 passing.

## Open follow-ups
- Overwrite-confirm modal when saving over an existing `topics/<id>.json` (v2 currently overwrites
  silently — see plan self-review).
- Optional: load an existing topic file into the Editor for editing (primary flow is authoring new).
