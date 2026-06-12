# Using the Desktop GUI

How to launch, navigate, and use the customtkinter desktop application.

## Prerequisites

- Dependencies installed (`pip install -r requirements.txt` — includes `customtkinter>=5.2.0`)
- **FFmpeg on PATH** — required for audio generation and replay.  
  Check: `ffmpeg -version`. If missing, see [Installation Guide](INSTALLATION.md#installing-ffmpeg).
- Topic scripts in `topics/` (JSON files). A sample is at `topics/conversation_1.json`.

## Launching the GUI

```bash
python main.py gui
```

With a custom config file or output directory:

```bash
python main.py gui -c config/default.yaml -o output/
```

The window opens at 1 100 × 700 px on the **Queue** panel. Close the window with the OS close button — size and position are remembered across restarts.

> If FFmpeg is not on PATH, an orange warning banner appears at the top of the window. The GUI still opens but audio generation will fail at the stitching step.

---

## Layout

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
  200 px           remainder
```

Click any sidebar button to switch panels. The active panel button is highlighted. The **☀ Theme** button at the bottom cycles: Dark → Light → System.

---

## Panels

### Queue

Add topic scripts, monitor generation progress, and run all queued items.

| Control | Action |
|---------|--------|
| **Add Topic** | Opens a file picker filtered to `*.json`; validates the selected script |
| **Remove** | Removes the selected (non-running) item |
| **▶ Run All** | Runs all `queued` items sequentially with live progress bars |

Status badges: grey = queued, blue = running, green = done, red = failed.

Click any row to select it. After a run completes the History panel refreshes automatically.

---

### Library

Browse all `*.json` scripts in the `topics/` folder.

| Control | Action |
|---------|--------|
| **Open in Editor** | Loads the selected script into the Editor panel and switches to it |
| **Duplicate** | Copies the file to `topics/<lesson_id>_copy.json` |
| **Delete** | Prompts for the lesson ID to confirm, then deletes the file |

The right pane shows a read-only preview of the selected script's metadata and lines. The list refreshes whenever the Editor saves a script.

---

### Editor

Author or edit a conversation script line by line.

| Control | Action |
|---------|--------|
| **Add** | Opens a modal form (speaker, text, emotion, pause_after_ms, speech_rate) |
| **Delete** | Removes the selected line |
| **▲ Up / ▼ Down** | Reorders the selected line |
| **💾 Save** | Validates and saves to `topics/<lesson_id>.json`; notifies Library to refresh |

Fill in **lesson_id** and **title** at the top before saving. The saved file is immediately available to add to the Queue.

To open an existing script for editing, use **Library → Open in Editor** rather than creating from scratch.

---

### Config

Edit and persist the YAML configuration.

| Control | Action |
|---------|--------|
| **💾 Save** | Writes all fields back to the config file; updates in-memory config |
| **↺ Reset** | Reloads config from disk, discarding unsaved changes |

Editable sections: engine (`edge`/`kokoro`), audio (sample rate, normalize level, output format), synthesis (pause/silence/retry settings), and the speaker→voice name map. Changes take effect on the **next** generation run.

---

### History

Browse past generation runs, replay audio, or re-queue a script.

| Control | Action |
|---------|--------|
| Click a run | Shows its metadata (paths, engine, duration) in the detail pane |
| **▶ Play** | Plays the run's audio file via the embedded player |
| **■ Stop** | Stops playback |
| **Re-queue** | Adds the script back to the Queue and switches to the Queue panel |

Runs are listed newest-first. Green = successful, red = failed. The panel refreshes when you switch to it.

---

### Voices

Browse available voices and preview synthesis.

| Control | Action |
|---------|--------|
| Engine radio | Switch between Edge (cloud) and Kokoro (local, static list) |
| Language entry + **Filter** | Reload the Edge voice list for a given language prefix (e.g. `en`, `en-US`) |
| Click a row | Selects a voice |
| **▶ Preview** | Synthesizes a short phrase using the selected Edge voice and plays it |
| **Copy Name** | Copies the voice's full name to the clipboard for use in Config |

Edge voice list loads from the network in a background thread. Kokoro voices are listed statically from the installed config (no model download required to browse). Preview synthesis requires a network connection for Edge; Kokoro preview is not yet supported.

---

## Typical Workflow

1. **Launch** — `python main.py gui`
2. **Add topics** — Queue panel → Add Topic → pick a `.json` file
3. **Run** — click **▶ Run All**, watch progress bars fill up
4. **Review** — switch to History, select the run, press **▶ Play**
5. **Author new scripts** — Library panel → Editor; or Editor panel directly
6. **Adjust config** — Config panel → change settings → **💾 Save**
7. **Explore voices** — Voices panel → filter by language → Preview → Copy Name → paste into Config voice map

---

## Troubleshooting

### Warning banner: "ffmpeg not found"

FFmpeg is not on PATH. Generation will fail. Install and add to PATH — see [Installation Guide](INSTALLATION.md#installing-ffmpeg).  
Windows gotcha: `winget install Gyan.FFmpeg` installs but may not add to PATH automatically — add `...\ffmpeg-*-full_build\bin` manually and open a new terminal.

### Audio player shows "ffplay not found"

`ffplay` is part of the FFmpeg package. Confirm `ffplay -version` works. The player widget is hidden until FFmpeg is installed.

### Library shows "topics/ not found or empty"

The `topics/` directory either doesn't exist or contains no `.json` files. Create a script using the Editor panel and save it, or place existing scripts in `topics/`.

### Edge voice list fails to load

Requires an internet connection. If on a restricted network, switch to Kokoro in the engine radio to browse local voices instead.

### Script fails validation in Queue

The validator checks structure, duplicate IDs, required fields, and valid speaker IDs. Click the failed item to see the error message, fix the `.json` file, then re-add it.
