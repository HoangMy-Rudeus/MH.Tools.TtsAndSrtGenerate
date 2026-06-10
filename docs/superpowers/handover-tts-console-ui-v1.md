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
| 1 | Add Textual dependency + scaffolding | DONE | `6302cc5` |
| 2 | `Config.to_dict()` + `config_io` (YAML) | DONE | `2b51113` |
| 3 | `HistoryStore` | DONE | `77ccb57` |
| 4 | Queue models + validation | DONE | `2876624` |
| 5 | Generation runner seam | DONE | `155abf1` |
| 6 | `AppState` | DONE | `f8b516b` |
| 7 | `TtsApp` shell + screen switching + ffmpeg check | DONE | `a8eb64c` |
| 8 | Queue screen (add/run/progress) | TODO (next) | — |
| 9 | Config screen (edit/save) | TODO | — |
| 10 | History screen (list/view/open/re-run) | TODO | — |
| 11 | Wire `tui` CLI command | TODO | — |
| 12 | Final verification + README | TODO | — |

**Suite status:** `python -m pytest -q` → 30 passed (as of Task 7).

Legend: TODO · IN PROGRESS · DONE · BLOCKED

## Decisions / deviations from plan
- Installed **Textual 8.2.7** (plan floor was 0.60.0). APIs used so far (App, Screen,
  ModalScreen, DataTable, `@work(thread=True)`, `call_from_thread`, `run_test`/`Pilot`,
  `notify`) are present in 8.x. Still verify `DataTable.cursor_row`/`move_cursor`/
  `RowHighlighted` in Tasks 8 & 10.
- **pytest-asyncio 1.4.0** installed; `pytest.ini` sets `asyncio_mode = auto`.

## Environment notes
- ffmpeg installed via winget but **not on PATH**; bin dir:
  `C:\Users\Rudeus\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.1-full_build\bin`
  Prepend to PATH for any end-to-end audio run.
- Python: pythoncore-3.14 at `C:\Users\Rudeus\AppData\Local\Python\pythoncore-3.14-64\`.
- `pytest` + (for TUI tests) `pytest-asyncio` required.

## Open follow-ups (v2 / later)
- Live Edge voice-browser modal in Config screen (v1 ships an editable text area).
- v2 plan: in-TUI script Editor + audio replay (`ffplay`).
