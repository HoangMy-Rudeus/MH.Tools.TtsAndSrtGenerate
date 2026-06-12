~# Using the Console UI (TUI)

How to launch, navigate, and use the interactive terminal interface.

## Prerequisites

- Dependencies installed (`pip install -r requirements.txt`)
- **FFmpeg on PATH** — required for audio generation and replay.  
  Check: `ffmpeg -version`. If missing, see [Installation Guide](INSTALLATION.md#installing-ffmpeg).
- Topic scripts in `topics/` (JSON files). A sample is at `topics/conversation_1.json`.

## Launching the UI

```bash
python main.py tui
```

With a custom config file or output directory:

```bash
python main.py tui -c config/default.yaml -o output/
```

The app opens on the **Queue** screen. Press `q` at any time to quit.

> If FFmpeg is not on PATH, a warning toast appears on startup. The UI still opens but audio
> generation will fail at the stitching step.

---

## Screens and Key Bindings

### Queue (home screen)

Manage the generation queue and run topics.

| Key | Action |
|-----|--------|
| `a` | Add a topic — opens a file picker over `topics/`; picks a `.json` script, validates it |
| `e` | Open the **Editor** to author a new script |
| `d` | Remove the selected (non-running) item |
| `r` | Run all queued topics sequentially with live progress |
| `c` | Open **Config** screen |
| `h` | Open **History** screen |
| `q` | Quit |

Items move through statuses: `queued` → `running` → `done` / `failed`. A progress bar shows
per-item progress in real time. Failed items record an error message; run continues to the next item.

### Editor (`e` from Queue)

Author a conversation script line-by-line.

| Key | Action |
|-----|--------|
| `a` | Add a line — opens a per-line modal (speaker, text, emotion, pause, speech rate) |
| `e` | Edit the selected line |
| `d` | Delete the selected line |
| `k` / `j` | Move selected line up / down |
| `s` | Validate and save to `topics/<lesson_id>.json` |
| `Esc` | Back to Queue |

Fill in **lesson_id** and **title** at the top before saving. The saved file is immediately
available to add to the Queue via `a`.

### Config (`c`)

Edit and persist the YAML configuration.

| Key / Control | Action |
|---------------|--------|
| `Ctrl+S` or Save button | Save changes to the config file |
| `Esc` | Back (unsaved changes are lost) |

Editable fields: engine (`edge`/`kokoro`), audio sample rate, normalize level, output format
(`mp3`/`wav`), synthesis pause/silence/retry settings, and the speaker→voice map.  
Changes take effect on the **next** generation run.

### History (`h`)

Browse past generation runs, replay audio, or re-queue a script.

| Key | Action |
|-----|--------|
| `↑` / `↓` | Navigate runs (newest first) |
| `o` | Show the output folder path of the selected run |
| `p` | Play the audio file via ffplay |
| `s` | Stop playback |
| `Enter` | Re-queue the selected script (sends it back to the Queue) |
| `Esc` | Back |

The detail panel on the right shows input/output paths for the selected run.

---

## Typical Workflow

1. **Launch** — `python main.py tui`
2. **Add topics** — press `a`, navigate to a `.json` file, press Enter to confirm
3. **Run** — press `r`; watch progress bars fill up
4. **Review** — press `h` to open History; navigate to the run and press `p` to hear the audio
5. **Adjust config** — press `c`, update the engine or voice map, save with `Ctrl+S`
6. **Author new scripts** — press `e` from the Queue screen

---

## Troubleshooting

### "ffmpeg/ffprobe not found" warning on startup

FFmpeg is not on PATH. Generation will fail. Install and add to PATH — see
[Installation Guide](INSTALLATION.md#installing-ffmpeg).  
Windows gotcha: `winget install Gyan.FFmpeg` installs but may not add to PATH automatically.
Add `...\ffmpeg-*-full_build\bin` manually and open a new terminal.

### File picker shows no `.json` files

The picker starts in `topics/`. If that directory is empty or doesn't exist, navigate to where
your scripts are, or create `topics/` and put scripts there.

### Script fails validation when adding to queue

The validator checks structure, duplicate IDs, required fields, and valid speaker IDs. Open the
file and fix the reported error, or use the Editor to rebuild the script.

### Audio replay (`p`) does nothing

`ffplay` is part of FFmpeg. Confirm `ffplay -version` works. If the run failed (status `FAIL`),
there is no audio file to play.
