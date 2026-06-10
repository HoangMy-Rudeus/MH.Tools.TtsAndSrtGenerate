# Console UI (TUI) v2 — Design Spec (Editor + Audio Replay)

- **Date:** 2026-06-11
- **Status:** Approved (design)
- **Builds on:** v1 (`2026-06-11-tts-console-ui-design.md`), merged to `main`.

## Context

v1 shipped Queue + Config + live generation + History. v2 adds the two deferred pieces:
an in-TUI **script Editor** (author conversation scripts without leaving the app) and
**audio replay** (listen to a generated run from the History screen).

## Decisions (locked)

- **Editor editing model:** per-line **modal form**. A list of lines; add/edit opens a modal
  with fields (speaker dropdown, text, emotion, pause_after_ms, speech_rate). Reorder/delete via
  keys. Guided + per-field — most robust in Textual.
- **Audio replay:** launch `ffplay` (ships with ffmpeg) as a non-blocking subprocess; stop on a
  key, on leaving the screen, or on app exit.
- Reuses existing models/validation: `Script`, `ScriptLine`, `ScriptSettings`, `ScriptValidator`.

## Components

### New: `src/tui/script_io.py`
- `script_to_dict(script: Script) -> dict` — inverse of `ScriptValidator.parse_script`.
- `save_script(script: Script, path) -> None` — write pretty JSON (utf-8), create parent dirs.

### New: `src/tui/player.py`
- `AudioPlayer` protocol: `play(path: str) -> None`, `stop() -> None`.
- `FfplayPlayer` — real impl: `subprocess.Popen(["ffplay","-nodisp","-autoexit","-loglevel","quiet",path])`;
  `stop()` terminates any running process; `play()` stops the previous one first. Uses
  `shutil.which("ffplay")`; no-op with a status message if ffplay is absent.
- `FakePlayer` — test helper recording `played`/`stopped` calls (no subprocess).
- Added to `AppState` as `player: AudioPlayer = field(default_factory=FfplayPlayer)`.

### New: `src/tui/screens/editor.py`
- `EditorScreen(Screen)`:
  - Metadata inputs: `lesson_id`, `title`, `level`, `language`; settings: `initial_silence_ms`,
    `default_pause_ms`, default `speech_rate`.
  - `DataTable` of lines (columns: `#`, speaker, text preview).
  - Bindings: `a` add line, `e` edit selected, `d` delete, `k`/`j` move up/down, `s` save,
    `escape` back.
  - In-memory state: `self.lines: list[ScriptLine]`.
- `LineFormScreen(ModalScreen[ScriptLine])`:
  - Fields: speaker `Select` (standard IDs + current value), text `Input`, emotion `Select`
    (5 values), `pause_after_ms` `Input`, `speech_rate` `Input`. OK/Cancel.
  - Dismisses with a `ScriptLine` (new id = `max(existing ids)+1` for add; keep id for edit) or None.
- **Save:** assemble `Script(lesson_id,title,lines,language,level,settings)`, validate with
  `ScriptValidator().validate_or_raise`; on error show messages and do not write; on success
  `save_script` to `topics/<lesson_id>.json` and offer to enqueue (append a `QueueItem`).

### Modified
- `src/tui/screens/queue.py`: add binding `e` → `app.push_screen(EditorScreen())` (new script).
- `src/tui/screens/history.py`: add `p` (play selected run's `audio_file` via `app.state.player`)
  and `s` (stop). Stop the player in `on_screen_suspend`/unmount.
- `src/tui/state.py`: add `player` field.
- `src/tui/app.py`: accept optional `player` (default `FfplayPlayer`) like `runner`.

## Data flow
- **Editor:** in-memory `list[ScriptLine]` + metadata → on save, build `Script` → validate → write
  JSON → (optional) enqueue. Reorder mutates list order only (line `id`s stay unique; list order is
  playback order).
- **Replay:** History `p` → `player.play(rec.audio_file)` spawns ffplay; `stop()`/screen-exit
  terminates it.

## Error handling
- Editor save with invalid script → modal/status lists validator errors; nothing written.
- Editor save when `lesson_id` empty/invalid → caught by validator; surfaced.
- Replay when `ffplay` missing or `audio_file` absent → status message, no crash.
- Replacing an existing `topics/<lesson_id>.json` → confirm overwrite (modal) before writing.

## Testing
- **Pure unit:** `script_io` round-trip (`script_to_dict` → `parse_script` equal); `save_script`
  reload-equal; new-line id assignment; reorder logic.
- **Player:** `FfplayPlayer` guarded when ffplay absent (no throw); `FakePlayer` records calls.
- **Headless TUI (Pilot):** Editor add-line via modal then save writes a valid file; reorder
  changes order; History `p` calls `player.play` with the entry's audio path (FakePlayer injected).

## Scope boundaries (v2 non-goals)
- No waveform/scrubbing/seek UI — play/stop only.
- No editing of arbitrary existing files mid-stream beyond load-for-edit (load existing optional;
  primary flow is authoring new + editing in session).
- No per-line "preview voice" synthesis (possible future).

## Affected / new files
- **New:** `src/tui/script_io.py`, `src/tui/player.py`, `src/tui/screens/editor.py`, tests.
- **Edit:** `src/tui/state.py`, `src/tui/app.py`, `src/tui/screens/queue.py`,
  `src/tui/screens/history.py`.
