# TTS & SRT Generator — User Manual

A practical, end-to-end guide to setting up and using the app. It converts conversation-script
JSON files into synchronized audio plus subtitles, via a command line **and** an interactive
**console UI (TUI)**.

- New to scripts? See [Script Format](reference/SCRIPT_FORMAT.md) and the AI-readable
  [JSON input guide](reference/AI_JSON_INPUT.md).
- Detailed install options: [Installation Guide](how-to/INSTALLATION.md).

---

## 1. What it does

You provide a JSON **script** describing a multi-speaker conversation. The app:

1. Validates the script.
2. Synthesizes each line with a TTS engine (**Edge** = cloud/free, or **Kokoro** = local).
3. Stitches the audio with pauses and normalization.
4. Writes, per script `lesson_id`:
   - `<lesson_id>.mp3` (or `.wav`) — the audio
   - `<lesson_id>.srt` — SubRip subtitles
   - `<lesson_id>_subtitles.json` — `[{ "startTime", "endTime", "text" }]`, times in **seconds**
   - `<lesson_id>_timeline.json` — detailed segments (milliseconds + metadata)

---

## 2. Setup

### 2.1 Requirements
- **Python 3.10+** (3.13+ works; `audioop-lts` is pulled in automatically for 3.13+).
- **ffmpeg** (and `ffprobe`/`ffplay`, which ship with it) on your `PATH` — required to stitch and
  export audio, and to replay audio in the TUI.
- **Network** — only for the Edge engine (cloud). Kokoro is fully offline but needs model files.

### 2.2 Install the app
```bash
# from the project root
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate     # macOS/Linux

pip install -r requirements.txt
```
This installs everything needed for the CLI, the console UI (`textual`), the Edge engine
(`edge-tts`), and the tests (`pytest`, `pytest-asyncio`).

### 2.3 Install ffmpeg
See [Installation Guide → Installing FFmpeg](how-to/INSTALLATION.md#installing-ffmpeg) for every
OS. Quick versions:
```bash
winget install Gyan.FFmpeg     # Windows
brew install ffmpeg            # macOS
sudo apt install ffmpeg        # Ubuntu/Debian
```
Verify:
```bash
ffmpeg -version
```

> **Windows + winget gotcha:** winget installs ffmpeg but may **not** add it to your `PATH` until
> you open a new terminal — or it may not add it at all. If `ffmpeg -version` fails, find the
> install dir (e.g.
> `…\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_*\ffmpeg-*-full_build\bin`) and add it to
> your user `PATH`, then open a new terminal. The app warns on startup if ffmpeg is missing, and
> generation will fail at the stitching step without it.

### 2.4 (Optional) Kokoro local engine
For offline, high-quality TTS:
```bash
pip install kokoro-onnx
mkdir models
# download kokoro-v1.0.onnx and voices-v1.0.bin into ./models  (see Installation Guide)
```
Then set `engine: kokoro` in your config (Section 6) or pass `--engine kokoro`.

### 2.5 Verify the install
```bash
python main.py --help
python main.py validate topics/conversation_1.json
python -m pytest -q          # optional: run the test suite
```

---

## 3. Two ways to use the app

| | Command line (CLI) | Console UI (TUI) |
|---|---|---|
| Best for | scripting, batch jobs, automation | interactive authoring + running |
| Author scripts | external editor / AI | built-in Editor screen |
| Run | `generate` / `batch` | Queue screen (run all) |
| Review past runs | inspect output files | History screen (+ audio replay) |
| Launch | `python main.py <command>` | `python main.py tui` |

---

## 4. Command line (CLI)

General form: `python main.py [--verbose] <command> [options]`.

### 4.1 `generate` — one script → outputs
```bash
python main.py generate topics/conversation_1.json -o output/
python main.py generate topics/conversation_1.json --engine edge --format mp3
python main.py generate topics/conversation_1.json -c config/default.yaml
```
| Option | Default | Meaning |
|--------|---------|---------|
| `-o, --output` | `output` | Output directory |
| `-e, --engine` | from config | `edge` or `kokoro` |
| `-c, --config` | built-in defaults | Path to a YAML config |
| `-f, --format` | `mp3` | `mp3` or `wav` |

### 4.2 `batch` — every script in a directory
```bash
python main.py batch topics/ -o output/ --engine edge
```
Processes each `*.json` and reports per-file success/failure.

### 4.3 `validate` — check a script without generating
```bash
python main.py validate topics/conversation_1.json
```
Prints validation errors, or the lesson id/title/line count/language if valid.

### 4.4 `voices` — list available voices
```bash
python main.py voices --engine edge --language en
python main.py voices --engine kokoro
```

### 4.5 `init-config` — write a starter config
```bash
python main.py init-config -o config/default.yaml
```

### 4.6 `tui` — launch the console UI
```bash
python main.py tui
python main.py tui -c config/default.yaml -o output/
```

---

## 5. Console UI (TUI)

Launch with `python main.py tui`. Global keys: `c` Config, `h` History, `q` quit. If ffmpeg is
missing you'll see a warning toast on startup.

### 5.1 Queue (home screen)
The list of topics to generate.

| Key | Action |
|-----|--------|
| `a` | Add a topic — opens a file picker over `topics/`; the script is validated on select |
| `e` | Open the **Editor** to author a new script |
| `d` | Remove the selected topic |
| `r` (or `Enter`) | Run all queued topics **sequentially**, with a live progress bar per item |

A topic that fails (network/synthesis/ffmpeg) is marked `failed` and the queue **continues** to the
next one. Completed runs are recorded in History.

### 5.2 Editor (`e` from Queue)
Author a conversation script without leaving the app.

- Top fields: `lesson_id`, `title`, `language`, `level`.
- Lines table + per-line modal form:

| Key | Action |
|-----|--------|
| `a` | Add a line — modal: speaker, text, emotion, pause_after_ms, speech_rate |
| `e` | Edit the selected line |
| `d` | Delete the selected line |
| `k` / `j` | Move the selected line up / down (reorder) |
| `s` | Validate and save to `topics/<lesson_id>.json` |
| `Esc` | Back to Queue |

Saving validates the whole script; if invalid, the error is shown and nothing is written.

### 5.3 Config (`c`)
Edit settings and save them back to your YAML config; changes apply to the next run.

- **Engine** (edge/kokoro), **Audio** (`sample_rate`, `normalize_to`, `output_format`),
  **Synthesis** (`default_pause_ms`, `initial_silence_ms`, `max_retries`), and the
  **Edge voice map** (`speaker_id=voice`, one per line).
- `Ctrl+S` or the **Save** button writes the file. `Esc` goes back.

### 5.4 History (`h`)
Browse past runs (newest first); each row shows time, title, engine, duration, status.

| Key | Action |
|-----|--------|
| (select a row) | Shows the run's input/output file paths in the detail pane |
| `o` | Show the output folder for the selected run |
| `p` / `s` | Play / stop the generated audio (via `ffplay`) |
| `Enter` | Re-queue the selected run's script (then go to Queue and press `r`) |
| `Esc` | Back |

History is persisted to `output/history.json`, so it survives restarts.

---

## 6. Configuration

Configuration is a YAML file (default `config/default.yaml`). Generate one with `init-config`, edit
it by hand, or edit it from the TUI Config screen. Key sections:

```yaml
engine: "edge"            # or "kokoro"

edge:
  default_voice: "en-US-AriaNeural"
  voices:
    female_us_1: "en-US-AriaNeural"
    male_us_1: "en-US-GuyNeural"
    # …

kokoro:
  model_path: "./models/kokoro-v1.0.onnx"
  voices_path: "./models/voices-v1.0.bin"
  default_voice: "af_heart"
  voices:
    female_us_1: "af_heart"
    # …

audio:
  sample_rate: 24000
  normalize_to: -16        # dBFS
  output_format: "mp3"     # mp3 or wav

synthesis:
  default_pause_ms: 400
  initial_silence_ms: 300
  max_retries: 3
```
Full details: [Configuration Reference](reference/CONFIG_REFERENCE.md).

---

## 7. Writing scripts

A script is a JSON object with metadata + a list of lines. Minimal example:
```json
{
  "lesson_id": "greeting_001",
  "title": "A Simple Greeting",
  "lines": [
    { "id": 1, "speaker": "female_us_1", "text": "Hello! How are you?" },
    { "id": 2, "speaker": "male_us_1", "text": "I'm great, thanks!", "pause_after_ms": 600 }
  ]
}
```
- Required: `lesson_id` (letters/digits/`_`/`-`), `title`, ≥1 line; each line needs `id`, `speaker`, `text`.
- Optional per line: `voice`, `emotion` (`neutral|friendly|cheerful|serious|excited`),
  `pause_after_ms` (0–10000), `speech_rate` (0.5–2.0).
- Full spec: [Script Format](reference/SCRIPT_FORMAT.md). For AI-generated scripts:
  [AI JSON input guide](reference/AI_JSON_INPUT.md).

---

## 8. Troubleshooting

| Symptom | Cause / Fix |
|---------|-------------|
| Startup warning "ffmpeg/ffprobe not found"; generation fails at stitching | ffmpeg not on PATH. Install it and open a new terminal (Section 2.3). |
| `Line N: Unknown speaker 'X'` | The `speaker` isn't in the active engine's voice map. Use a standard speaker ID, set a `voice` override, or add the mapping in Config. |
| Audio won't play in History (`p`) | `ffplay` (part of ffmpeg) not on PATH, or the audio file was removed. |
| `No module named 'textual'` | Run `pip install -r requirements.txt` (textual is included). |
| Kokoro: "Model file not found" | Download model files into `./models/` or fix `kokoro.model_path`/`voices_path` (Section 2.4). |
| Edge: SSL/cert errors | `pip install --upgrade certifi`. |

More: [Installation Guide → Troubleshooting](how-to/INSTALLATION.md#troubleshooting-installation).

---

## 9. Where things live

```
main.py                 # CLI entry point (generate / batch / validate / voices / init-config / tui)
config/default.yaml     # configuration
topics/                 # your input scripts (*.json)
output/                 # generated audio + subtitles + history.json
src/                    # application code (pipeline, engines, services, models, tui)
docs/                   # this documentation
```
