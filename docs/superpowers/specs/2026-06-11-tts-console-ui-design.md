# Console UI (TUI) for TTS & SRT Generator — Design Spec

- **Date:** 2026-06-11
- **Status:** Approved (design); ready for implementation planning
- **Author:** brainstormed with Claude

## Context

The project is currently a Python CLI batch tool: it loads a conversation-script JSON,
validates it, synthesizes per-line audio (Edge or Kokoro engine), stitches the audio, and
writes `.mp3`/`.wav`, `.srt`, `_subtitles.json`, and `_timeline.json` outputs. Configuration
is a YAML file (`config/default.yaml`).

The user wants an interactive **console UI** to make this easier to drive: queue multiple
topics, manage configuration (voices/language/audio/synthesis params), and review past runs.
This is a usability layer on top of the existing, working pipeline — not a rewrite.

Desired outcome: a full-screen terminal application (TUI) that wraps the existing pipeline
with a Queue, Config, and History experience, with a script Editor and audio replay to follow.

## Decisions (locked)

- **UI style:** full-screen TUI built with **Textual**.
- **Integration approach (A):** the TUI reuses the existing `Pipeline`, `Config`, and
  `ScriptValidator` directly; generation runs in a Textual worker thread. No changes to
  synthesis/stitching logic.
- **Scope is phased:**
  - **v1 (build now):** Queue (pick existing topic files) + Config + live generation + History.
  - **v2 (designed, build later):** in-TUI script Editor + audio replay.

## Architecture & file layout

New package `src/tui/`, launched by a new `tts tui` Click command in `main.py` (reuses the
existing `-c/--config` option to choose the YAML config).

```
src/tui/
  __init__.py
  app.py            # TtsApp(App): global key bindings, screen switching, holds AppState
  state.py          # AppState: live Config, queue list, HistoryStore handle
  runner.py         # generation seam: drives Pipeline in a worker thread (injectable/mockable)
  history_store.py  # load/append/list run records -> output/history.json
  config_io.py      # load + save YAML config
  models.py         # QueueItem dataclass + status enum (UI-side state)
  screens/
    __init__.py
    queue.py        # QueueScreen (home)
    config.py       # ConfigScreen
    history.py      # HistoryScreen
    editor.py       # (v2) author scripts
  widgets/
    __init__.py     # shared widgets (e.g. queue row, voice-picker modal)
```

Supporting change to existing code:
- Add `Config.to_dict()` to `src/models/config.py` (inverse of the existing `from_dict`) so the
  Config screen can serialize back to YAML. `config_io.save_config(config, path)` uses
  `yaml.safe_dump(config.to_dict(), ...)`.

New dependency: `textual` (add to `requirements.txt`; Rich comes transitively).
Audio replay (v2) uses `ffplay` (ships with the installed ffmpeg) launched via subprocess —
no extra Python dependency.

## Components & screens

### Shared state
- `AppState`: the live `Config`, the queue (`list[QueueItem]`), and a `HistoryStore` handle.
  Owned by `TtsApp`; screens read/write through it.
- `QueueItem` (dataclass): `script_path`, `title`, `lesson_id`, `status`
  (`queued | running | done | failed`), `progress` (0.0–1.0), `result` (`PipelineResult`),
  `error` (str | None).

### Queue screen (home, v1)
- A table/list of queue items showing status + a per-item progress bar.
- Key bindings: `a` add topic, `d` remove selected, `enter` run all queued (sequential),
  `c` → Config, `h` → History, `q` quit.
- **Add topic:** a file-picker modal over `topics/` (and arbitrary dirs), filtered to `*.json`.
  On select, validate with the existing `ScriptValidator.load_script` + `validate`; if invalid,
  show a modal listing errors and do **not** queue; if valid, add with its `lesson_id`/`title`.
- Footer/status line shows the most recent completed run.

### Config screen (v1)
Sectioned form, `Save` writes back to the YAML config path and updates the live `AppState.config`:
- **Engine:** edge / kokoro (radio).
- **Language:** target language; for Edge, a "browse voices" action lists available voices via
  the existing `list_voices_sync(language)`; sets default language for new scripts.
- **Voice mappings:** editable `speaker_id → voice` table per engine, incl. default voice.
- **Audio:** `sample_rate`, `normalize_to` (dBFS), `output_format` (mp3/wav).
- **Synthesis:** `default_pause_ms`, `initial_silence_ms`, `max_retries`, default `speech_rate`.

### History screen (v1)
- Table from `output/history.json` (newest first): timestamp, title, engine, duration, line
  count, status.
- Select an entry → detail pane: the input script (lines) + generated subtitle/SRT text.
- Actions: `o` open/locate output files (reveal folder / print paths), `enter` re-run
  (re-queues that script path into the Queue).
- *(v2)* `p` replay generated audio.

### v2 — Editor screen & audio replay (designed, deferred)
- **Editor:** author a conversation — lesson metadata (`lesson_id`, `title`, `level`,
  `language`, `settings`) + a line list (speaker, text, emotion, `pause_after_ms`,
  `speech_rate`). Reuses `Script`/`ScriptLine` and `ScriptValidator`; saves to
  `topics/<lesson_id>.json` via a new serializer; can queue directly.
- **Audio replay:** play a history entry's mp3/wav by launching `ffplay` as a subprocess;
  stop on key/screen change.

## Data flow — generation

1. User triggers "run all" on the Queue screen.
2. `TtsApp` starts a single Textual `@work(thread=True)` worker that iterates queued items
   **sequentially** (matches the design; keeps the UI responsive while Edge synthesis blocks).
3. Per item: `Pipeline(config=AppState.config).generate(script_path, output_dir, on_progress=cb)`.
4. The existing `on_progress(current, total, result)` callback runs in the worker thread and
   uses `app.call_from_thread(...)` (or a posted custom `Message`) to update that `QueueItem`'s
   progress bar and row.
5. On finish, the returned `PipelineResult` (success, file paths, `duration_ms`, error) updates
   the row **and** is appended to `HistoryStore` (writes `output/history.json`), refreshing the
   History view.

### History record (output/history.json)
JSON array of objects:
`{ timestamp, lesson_id, title, engine, duration_ms, line_count, script_path, audio_file,
srt_file, subtitle_file, timeline_file, success, error }`.
Timestamp is generated at append time (`datetime.utcnow().isoformat()+"Z"`, matching existing
pipeline metadata style).

## Error handling

- **ffmpeg missing:** on startup, `shutil.which("ffmpeg")` / `which("ffprobe")` → if absent,
  show a clear banner (pydub cannot decode/stitch/export audio without it; this previously
  caused a silent stitch failure).
- **Invalid script on add:** validator errors shown in a modal; file not queued.
- **Generation failure** (network, synthesis, ffmpeg, etc.): caught in the worker; item marked
  `failed` with `PipelineResult.error`; recorded in history as failed; the **queue continues**
  to the next item — one bad topic never aborts the batch.
- **Config save error** (bad path/permissions): modal error; in-memory config left unchanged.
- The worker wraps each run in try/except so unexpected exceptions surface as messages rather
  than crashing the TUI.

## Testing strategy

- **Pure unit tests (pytest, no UI runtime):**
  - `HistoryStore`: append/list/load round-trip on a temp file.
  - `config_io` / `Config.to_dict()`: round-trips with `from_dict`; `save_config` output reloads
    to an equal `Config`.
  - Queue add/validation and `QueueItem` status transitions (logic kept out of widgets so it is
    directly testable).
- **Headless TUI tests** via Textual's `App.run_test()` + `Pilot`:
  - screen switching, "add topic" with valid vs invalid files,
  - progress updates driven by a **fake runner** (the `runner.py` seam is injected, so tests
    never hit the network or ffmpeg).

## Scope boundaries (explicit non-goals for v1)

- No editing of existing scripts (pick-only) — authoring is v2.
- No parallel generation — sequential only.
- No history deletion.
- No audio replay — v2.

## Affected / new files

- **New:** `src/tui/` package (per layout above); `requirements.txt` gains `textual`.
- **Edit (existing):** `main.py` (add `tui` command); `src/models/config.py` (add `to_dict()`).
- **Unchanged:** synthesis/stitching pipeline, engines, validator, SRT/subtitle utilities.
