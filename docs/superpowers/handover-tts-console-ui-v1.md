# Handover — Console UI (TUI) v1 Implementation

**Purpose:** Track implementation progress so work can pause and resume cleanly across sessions.

- **Branch:** `feature/console-ui-v1` (off `main`)
- **Plan:** `docs/superpowers/plans/2026-06-11-tts-console-ui-v1.md` (12 tasks, TDD, bite-sized)
- **Spec:** `docs/superpowers/specs/2026-06-11-tts-console-ui-design.md`
- **Execution skill:** `superpowers:executing-plans` (inline, commit per task)

## How to resume
1. `git checkout feature/console-ui-v1`
2. Read this file's **Status** table to find the next `TODO` task.
3. Open the plan, go to that task, execute its steps exactly (write failing test → run → implement → run → commit).
4. After completing a task: tick its plan checkboxes, mark it `DONE` here with the commit SHA, and set the next task `IN PROGRESS`.
5. Run `python -m pytest -q` to confirm the suite is green before stopping.

## Status

| Task | Title | Status | Commit |
|------|-------|--------|--------|
| 1 | Add Textual dependency + scaffolding | TODO | — |
| 2 | `Config.to_dict()` + `config_io` (YAML) | TODO | — |
| 3 | `HistoryStore` | TODO | — |
| 4 | Queue models + validation | TODO | — |
| 5 | Generation runner seam | TODO | — |
| 6 | `AppState` | TODO | — |
| 7 | `TtsApp` shell + screen switching + ffmpeg check | TODO | — |
| 8 | Queue screen (add/run/progress) | TODO | — |
| 9 | Config screen (edit/save) | TODO | — |
| 10 | History screen (list/view/open/re-run) | TODO | — |
| 11 | Wire `tui` CLI command | TODO | — |
| 12 | Final verification + README | TODO | — |

Legend: TODO · IN PROGRESS · DONE · BLOCKED

## Decisions / deviations from plan
- (none yet)

## Environment notes
- ffmpeg installed via winget but **not on PATH**; bin dir:
  `C:\Users\Rudeus\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.1-full_build\bin`
  Prepend to PATH for any end-to-end audio run.
- Python: pythoncore-3.14 at `C:\Users\Rudeus\AppData\Local\Python\pythoncore-3.14-64\`.
- `pytest` + (for TUI tests) `pytest-asyncio` required.

## Open follow-ups (v2 / later)
- Live Edge voice-browser modal in Config screen (v1 ships an editable text area).
- v2 plan: in-TUI script Editor + audio replay (`ffplay`).
