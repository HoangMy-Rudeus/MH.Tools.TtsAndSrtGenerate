# CLAUDE.md

Guidance for Claude Code working in this repo. Keep it current.

## What this is
Batch TTS + subtitle generator: a JSON conversation script → audio (`.mp3`/`.wav`), `.srt`,
`_subtitles.json` (times in **seconds**), `_timeline.json` (ms + metadata). Two front-ends:
the CLI (`main.py`, Click) and a Textual **console UI** (`python main.py tui`).
Full guide: `docs/USER_MANUAL.md`.

## Commands
- Tests: `python -m pytest -q` (use `python -m` — bare `pytest` isn't on PATH here). Single file:
  `python -m pytest tests/tui/test_x.py -q`.
- Generate: `python main.py generate <script.json> -o output/`. Other commands: `batch`,
  `validate`, `voices`, `init-config`, `tui`.

## Environment gotchas
- Python 3.13+ (this machine: 3.14); `audioop-lts` is required on 3.13+ (already in requirements).
- **ffmpeg/ffprobe/ffplay must be on PATH** — pydub uses them to stitch/export audio; the TUI uses
  `ffplay` for replay. Without it, generation fails at the *stitch* step (the app warns on startup).
  On Windows, `winget install Gyan.FFmpeg` may not add it to PATH — add the
  `...\ffmpeg-*-full_build\bin` dir and open a new terminal.
- TUI tests need `pytest-asyncio` (configured in `pytest.ini` → `asyncio_mode = auto`).
- **.gitignore**: keep directory ignores anchored (`/models/`, not `models/`). An unanchored
  `models/` once matched `src/models/` and silently un-tracked the whole models package, breaking
  every import — the project couldn't even start.

## Architecture
- Pipeline (`src/pipeline.py`): validate → synthesize (engine) → stitch → write outputs.
  `Pipeline.generate(script_path, output_dir, on_progress=cb)` → `PipelineResult`.
- Engines (`src/engines/`): `edge` (cloud, needs network) and `kokoro` (local, needs
  `./models/*.onnx` + voices). Chosen via `Config.engine` / `--engine`.
- Models (`src/models/`): plain **dataclasses, not pydantic** (some older docs say pydantic).
  `Config.from_dict` / `to_dict` ↔ YAML.
- Subtitles/SRT: `src/utils/srt.py` (`generate_srt`, `generate_subtitle_json`).
- TUI (`src/tui/`): Textual app; screens (`queue`/`config`/`history`/`editor`) reuse the pipeline
  through a mockable `runner` seam and an injectable `player`; shared `AppState`.

## Conventions
- TDD: write the failing test → implement → commit per unit. Tests in `tests/` (+ `tests/tui/`).
- TUI tests run headless via Textual's `app.run_test()` + `Pilot`; inject `FakeRunner` / `FakePlayer`
  so tests never touch the network or ffmpeg.
- Textual gotcha: a focused `DataTable` consumes `Enter` — bind screen-level run/confirm actions to
  another key (e.g. `r`) or a priority `Binding`.
- `ScriptValidator()` with no engine skips voice-name checks (engine-independent validation).
- Planning artifacts live in `docs/superpowers/` (specs, plans, handover trackers).
