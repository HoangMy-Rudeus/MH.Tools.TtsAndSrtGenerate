# GUI Desktop App Design — customtkinter

**Date:** 2026-06-12  
**Status:** Approved  
**Scope:** Add a `src/gui/` desktop GUI that coexists with the existing `src/tui/` console UI.

---

## Goals

- Provide a polished desktop GUI (`python main.py gui`) alongside the existing TUI (`python main.py tui`).
- Reuse all existing backend seams unchanged.
- Add three new capabilities not in the TUI: Script Library, Voice Browser, embedded Audio Player.
- Support Dark / Light / System theme switching.

## Non-Goals

- Replacing or modifying the TUI.
- Web or mobile UI.
- Real-time waveform visualization.
- Overwrite-confirmation dialog in Editor (silent overwrite, consistent with TUI v2).

---

## Architecture

### Package Structure

```
src/gui/
  __init__.py
  app.py              # TtsGuiApp(ctk.CTk) — main window, sidebar, panel switching
  state.py            # AppState — same shape as TUI's, same backend types
  panels/
    __init__.py
    queue.py          # QueuePanel
    editor.py         # EditorPanel
    config.py         # ConfigPanel
    history.py        # HistoryPanel
    library.py        # LibraryPanel (new)
    voices.py         # VoiceBrowserPanel (new)
  widgets/
    __init__.py
    audio_player.py   # AudioPlayerWidget — embedded in HistoryPanel + VoiceBrowserPanel
    line_form.py      # LineFormDialog (CTkToplevel) — used by EditorPanel
tests/gui/
  __init__.py
  test_queue_panel.py
  test_editor_panel.py
  test_history_panel.py
  test_library_panel.py
```

### Backend Seams (reused unchanged from `src/tui/`)

| Module | Used by |
|--------|---------|
| `runner.py` — `GenerationRunner`, `PipelineRunner`, `FakeRunner` | QueuePanel |
| `player.py` — `AudioPlayer`, `FfplayPlayer`, `FakePlayer` | AudioPlayerWidget |
| `config_io.py` — `load_config`, `save_config` | ConfigPanel, `app.py` |
| `history_store.py` — `HistoryStore`, `HistoryRecord` | HistoryPanel |
| `script_io.py` — `save_script`, `script_to_dict` | EditorPanel |
| `models.py` — `QueueItem`, `QueueStatus`, `build_queue_item` | QueuePanel, LibraryPanel |

### Launch Command

Added to `main.py`:

```bash
python main.py gui
python main.py gui -c config/default.yaml -o output/
```

Options mirror the `tui` command: `-c/--config` and `-o/--output`.

---

## Main Window & Sidebar

**Window:** 1100 × 700 px, resizable. Last size/position persisted in `~/.tts_gui_state.json`.

**Layout:**

```
┌──────────────────────────────────────────────────────┐
│ ┌──────────┐ ┌────────────────────────────────────┐  │
│ │ TTS &    │ │                                    │  │
│ │ SRT      │ │         Active Panel               │  │
│ │          │ │                                    │  │
│ │ ● Queue  │ │                                    │  │
│ │ ○ Library│ │                                    │  │
│ │ ○ Editor │ │                                    │  │
│ │ ○ Config │ │                                    │  │
│ │ ○ History│ │                                    │  │
│ │ ○ Voices │ │                                    │  │
│ │          │ │                                    │  │
│ │ ──────── │ │                                    │  │
│ │ ☀ Theme  │ │                                    │  │
│ └──────────┘ └────────────────────────────────────┘  │
└──────────────────────────────────────────────────────┘
  200px            remainder
```

- Active panel button highlighted with accent color.
- Theme toggle (bottom of sidebar) cycles: Dark → Light → System. Calls `ctk.set_appearance_mode()`.
- Only one panel is visible at a time; others are hidden via `pack_forget` / `pack`.

---

## Panels

### QueuePanel

**Layout:** Top toolbar (Add Topic, Remove, Run All buttons) + scrollable table (CTkScrollableFrame) with one row per `QueueItem` showing topic name, colored status badge, and progress bar.

**Behavior:**
- `Add Topic` — `CTkFileDialog` filtered to `*.json`; selected file validated via `build_queue_item`; error shown inline on failure.
- `Remove` — removes selected non-running item.
- `Run All` — starts a `threading.Thread` that calls `runner.run()` sequentially; progress posted via `app.after(0, cb)`; status badges update in real time.
- Status badge colors: grey=queued, blue=running, green=done, red=failed.

**State mutations:** writes to `AppState.queue`; appends to `AppState.history` on completion.

---

### EditorPanel

**Layout:** Two columns.
- Left (40%): metadata fields (lesson_id, title, language, level) + scrollable line list.
- Right (60%): line form (speaker dropdown, text box, emotion dropdown, pause_after_ms, speech_rate) + Add / Delete / Move Up / Move Down / Save buttons.

**Behavior:**
- Selecting a line in the list populates the right-side form.
- `Add` creates a new line and opens the form for it.
- `Save` calls `ScriptValidator().validate_or_raise()`, then `save_script(script, topics/<lesson_id>.json)`. Shows success/error label. On success, calls an optional `on_save` callback (passed at construction) so LibraryPanel can refresh its file list.
- `LineFormDialog` (`CTkToplevel`) used when adding a new line (modal).

---

### ConfigPanel

**Layout:** Scrollable form (`CTkScrollableFrame`).

Fields:
- Engine: radio buttons (`edge` / `kokoro`)
- Audio: sample_rate (entry), normalize_to (entry), output_format (radio: `mp3` / `wav`)
- Synthesis: default_pause_ms, initial_silence_ms, max_retries (entries)
- Edge voices: one row per speaker — speaker label + editable voice name entry

**Behavior:**
- `Save` reads all fields, calls `save_config(cfg, config_path)`. Success/error label shown inline. Updates `AppState.config` in memory.
- `Reset` reloads from disk (discards unsaved changes).

---

### HistoryPanel

**Layout:** Two columns.
- Left (40%): scrollable run list (newest first), colored green/red by success.
- Right (60%): detail panel — input/output paths, engine, duration; embedded `AudioPlayerWidget`; `Re-queue` button.

**Behavior:**
- Selecting a run populates the detail panel and passes `audio_file` path to `AudioPlayerWidget`.
- `Re-queue` calls `build_queue_item(rec.script_path)` and appends to `AppState.queue`. Switches to QueuePanel on success.
- Loads from `HistoryStore.list()` on mount; refreshes when QueuePanel completes a run.

---

### LibraryPanel (new)

**Layout:** Two columns.
- Left (35%): scrollable list of all `*.json` files in `topics/` (lesson_id + title).
- Right (65%): read-only script preview — metadata + line list (speaker, text).

**Behavior:**
- `Open in Editor` — loads the script into `EditorPanel` and switches to it.
- `Duplicate` — copies file to `topics/<lesson_id>_copy.json`.
- `Delete` — shows `CTkMessagebox` confirmation, then deletes file and refreshes list.
- Refreshes list when `EditorPanel` saves a script (via the `on_save` callback wired at construction in `app.py`).
- Shows "topics/ not found" label if directory is absent.

---

### VoiceBrowserPanel (new)

**Layout:**
- Top bar: engine radio (Edge / Kokoro) + language filter dropdown.
- Scrollable table: voice name, gender, locale, sample text preview.
- Bottom: `Preview` button + `Copy Name` button + embedded `AudioPlayerWidget`.

**Behavior:**
- Engine/language change reloads the voice list. Edge: calls `src.engines.edge.list_voices_sync(language)` (returns list of dicts with `ShortName`, `Gender`, `Locale`). Kokoro: reads `DEFAULT_KOKORO_VOICES` dict from `src.engines.kokoro` (static, no network).
- `Preview` — synthesizes "Hello, this is a preview." using the selected voice in a `threading.Thread`; saves to a temp file; plays via `AudioPlayerWidget`. Shows spinner while synthesizing.
- `Copy Name` — copies the voice name string to the clipboard.

---

## Widgets

### AudioPlayerWidget

Reusable `CTkFrame` embedded in HistoryPanel and VoiceBrowserPanel.

**Controls:** Play button, Stop button, progress bar (0–100%), current/total time label.

**Behavior:**
- `load(path)` — sets the file path; resets UI. Calls `ffprobe` to get duration.
- `play()` — calls `FfplayPlayer.play(path)`; starts an `app.after` polling loop (every 500 ms) to update the progress bar by comparing elapsed time to duration.
- `stop()` — calls `FfplayPlayer.stop()`; cancels polling loop.
- Shows "ffplay not found" label if `shutil.which("ffplay")` is None.

### LineFormDialog

`CTkToplevel` modal for adding a new script line in EditorPanel.

Fields: speaker (dropdown), text (entry), emotion (dropdown), pause_after_ms (entry), speech_rate (entry). `OK` validates and returns a `ScriptLine`; `Cancel` returns None.

---

## AppState

```python
@dataclass
class AppState:
    config: Config
    config_path: Path
    output_dir: Path
    history: HistoryStore
    runner: GenerationRunner = field(default_factory=PipelineRunner)
    player: AudioPlayer = field(default_factory=FfplayPlayer)
    queue: list[QueueItem] = field(default_factory=list)
```

Identical shape to `src/tui/state.py`. Held by `TtsGuiApp` and passed to panels at construction.

---

## Threading Model

- **Main thread:** all widget rendering and event handling (tkinter requirement).
- **Generation thread:** `threading.Thread` spawned by QueuePanel for `run_all`. Progress callbacks use `app.after(0, cb)` to post back to main thread.
- **Voice preview thread:** `threading.Thread` spawned by VoiceBrowserPanel for synthesis. Result (temp file path) posted back via `app.after`.
- **Rule:** no direct widget mutation from background threads — always use `app.after`.

---

## Testing

customtkinter has no headless test runner. Strategy:

- `tests/gui/` panel tests call panel methods directly (no widget rendering) with `FakeRunner` and `FakePlayer` injected. State mutations and data-flow logic are verified this way.
- Existing `tests/tui/` suite covers all shared backend seams — no duplication.
- Manual smoke test: `python main.py gui` to verify layout, theme toggle, generation, audio playback.

**New test files:**
- `tests/gui/test_queue_panel.py` — run-all state mutations, failure handling
- `tests/gui/test_editor_panel.py` — save/validate, line add/delete/reorder
- `tests/gui/test_history_panel.py` — re-queue, history load
- `tests/gui/test_library_panel.py` — list, duplicate, delete

---

## Dependencies

Add to `requirements.txt`:

```
customtkinter>=5.2.0
```

No other new dependencies. `ffprobe` (already required by pydub) used by `AudioPlayerWidget` for duration.
