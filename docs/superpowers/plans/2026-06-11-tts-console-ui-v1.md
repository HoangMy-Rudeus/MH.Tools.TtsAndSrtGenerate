# Console UI (TUI) v1 Implementation Plan — ✅ COMPLETE

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Add a full-screen Textual console UI that wraps the existing TTS pipeline with a Queue (pick existing topic files), Config editor, live generation, and a History view.

**Architecture:** A new `src/tui/` package layered on top of the existing `Pipeline`/`Config`/`ScriptValidator`. A thin, mockable `runner` seam drives `Pipeline.generate()` inside a Textual worker thread; the pipeline's existing `on_progress` callback updates a live queue. New `HistoryStore` (JSON) and `config_io` (YAML load/save) modules persist state. No changes to synthesis/stitching logic.

**Tech Stack:** Python 3.13+, Textual (TUI), pydub/edge-tts (existing pipeline), PyYAML, pytest + Textual's `App.run_test()`/`Pilot` for headless UI tests.

**Reference spec:** `docs/superpowers/specs/2026-06-11-tts-console-ui-design.md`

**Scope:** v1 only. Non-goals (deferred to v2): in-TUI script Editor, audio replay, script editing, parallel generation, history deletion.

---

## File structure

```
src/tui/
  __init__.py
  models.py         # QueueStatus enum, QueueItem dataclass, build_queue_item()
  config_io.py      # load_config(), save_config()
  history_store.py  # HistoryRecord dataclass, HistoryStore
  runner.py         # GenerationRunner protocol, PipelineRunner, FakeRunner (test helper)
  state.py          # AppState
  app.py            # TtsApp(App)
  screens/
    __init__.py
    queue.py        # QueueScreen + AddTopicScreen modal
    config.py       # ConfigScreen
    history.py      # HistoryScreen
tests/tui/
  __init__.py
  test_config_io.py
  test_history_store.py
  test_models.py
  test_runner.py
  test_app.py
  test_queue_screen.py
  test_config_screen.py
  test_history_screen.py
```

Existing files modified: `src/models/config.py` (add `to_dict()`), `main.py` (add `tui` command), `requirements.txt` (add `textual`).

---

## Task 1: Add Textual dependency and test scaffolding

**Files:**
- Modify: `requirements.txt`
- Create: `tests/tui/__init__.py`
- Create: `src/tui/__init__.py`

- [x] **Step 1: Add the dependency**

Edit `requirements.txt`, add under "Core dependencies":

```
textual>=0.60.0        # Console UI (TUI) framework
```

- [x] **Step 2: Install it**

Run: `python -m pip install "textual>=0.60.0"`
Expected: installs textual and its dependency `rich`.

- [x] **Step 3: Create empty package markers**

Create `src/tui/__init__.py`:

```python
"""Console UI (TUI) for the TTS & SRT generator."""
```

Create `tests/tui/__init__.py`:

```python
```

- [x] **Step 4: Verify Textual imports**

Run: `python -c "import textual; print(textual.__version__)"`
Expected: prints a version >= 0.60.0.

- [x] **Step 5: Commit**

```bash
git add requirements.txt src/tui/__init__.py tests/tui/__init__.py
git commit -m "build: add textual dependency and tui package scaffolding"
```

---

## Task 2: `Config.to_dict()` and `config_io` (YAML load/save)

**Files:**
- Modify: `src/models/config.py`
- Create: `src/tui/config_io.py`
- Test: `tests/tui/test_config_io.py`

- [x] **Step 1: Write the failing test**

Create `tests/tui/test_config_io.py`:

```python
"""Tests for TUI config load/save."""

from src.models.config import Config
from src.tui.config_io import load_config, save_config


def test_to_dict_round_trips_with_from_dict():
    cfg = Config()
    cfg.engine = "kokoro"
    cfg.edge.voices["female_us_1"] = "en-US-AriaNeural"
    cfg.audio.output_format = "wav"
    cfg.synthesis.max_retries = 5

    rebuilt = Config.from_dict(cfg.to_dict())

    assert rebuilt.engine == "kokoro"
    assert rebuilt.edge.voices["female_us_1"] == "en-US-AriaNeural"
    assert rebuilt.audio.output_format == "wav"
    assert rebuilt.synthesis.max_retries == 5


def test_save_then_load_returns_equal_config(tmp_path):
    cfg = Config()
    cfg.engine = "kokoro"
    cfg.audio.normalize_to = -14.0
    path = tmp_path / "config.yaml"

    save_config(cfg, path)
    loaded = load_config(path)

    assert loaded.engine == "kokoro"
    assert loaded.audio.normalize_to == -14.0
    assert loaded.edge.voices == cfg.edge.voices


def test_load_missing_file_returns_defaults(tmp_path):
    loaded = load_config(tmp_path / "does_not_exist.yaml")
    assert loaded.engine == "edge"
```

- [x] **Step 2: Run to verify it fails**

Run: `python -m pytest tests/tui/test_config_io.py -v`
Expected: FAIL — `ImportError` (`config_io` missing) and `Config` has no `to_dict`.

- [x] **Step 3: Add `to_dict()` to Config**

In `src/models/config.py`, add this method to the `Config` dataclass (after `from_dict`):

```python
    def to_dict(self) -> dict:
        """Serialize to a plain dict matching the from_dict / YAML structure."""
        return {
            "engine": self.engine,
            "edge": {
                "default_voice": self.edge.default_voice,
                "voices": dict(self.edge.voices),
            },
            "kokoro": {
                "model_path": self.kokoro.model_path,
                "voices_path": self.kokoro.voices_path,
                "default_voice": self.kokoro.default_voice,
                "voices": dict(self.kokoro.voices),
            },
            "audio": {
                "sample_rate": self.audio.sample_rate,
                "normalize_to": self.audio.normalize_to,
                "output_format": self.audio.output_format,
            },
            "synthesis": {
                "default_pause_ms": self.synthesis.default_pause_ms,
                "initial_silence_ms": self.synthesis.initial_silence_ms,
                "max_retries": self.synthesis.max_retries,
            },
        }
```

- [x] **Step 4: Create `config_io.py`**

Create `src/tui/config_io.py`:

```python
"""Load and save the YAML configuration used by the pipeline."""

from pathlib import Path

import yaml

from ..models.config import Config


def load_config(path: str | Path) -> Config:
    """Load a Config from a YAML file, or return defaults if it does not exist."""
    p = Path(path)
    if not p.exists():
        return Config()
    with open(p, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return Config.from_dict(data)


def save_config(config: Config, path: str | Path) -> None:
    """Serialize a Config to a YAML file (creating parent dirs as needed)."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        yaml.safe_dump(config.to_dict(), f, sort_keys=False, allow_unicode=True)
```

- [x] **Step 5: Run to verify it passes**

Run: `python -m pytest tests/tui/test_config_io.py -v`
Expected: PASS (3 tests).

- [x] **Step 6: Commit**

```bash
git add src/models/config.py src/tui/config_io.py tests/tui/test_config_io.py
git commit -m "feat(tui): add Config.to_dict and YAML config load/save"
```

---

## Task 3: `HistoryStore`

**Files:**
- Create: `src/tui/history_store.py`
- Test: `tests/tui/test_history_store.py`

- [x] **Step 1: Write the failing test**

Create `tests/tui/test_history_store.py`:

```python
"""Tests for the run history store."""

from src.tui.history_store import HistoryRecord, HistoryStore


def _record(lesson_id="lesson_1", success=True):
    return HistoryRecord(
        timestamp="2026-06-11T10:00:00Z",
        lesson_id=lesson_id,
        title="Title",
        engine="edge",
        duration_ms=1000,
        line_count=2,
        script_path="topics/a.json",
        audio_file="output/a.mp3",
        srt_file="output/a.srt",
        subtitle_file="output/a_subtitles.json",
        timeline_file="output/a_timeline.json",
        success=success,
        error=None,
    )


def test_load_missing_file_returns_empty(tmp_path):
    store = HistoryStore(tmp_path / "history.json")
    assert store.load() == []


def test_append_then_load_round_trips(tmp_path):
    store = HistoryStore(tmp_path / "history.json")
    rec = _record()
    store.append(rec)

    loaded = store.load()
    assert len(loaded) == 1
    assert loaded[0] == rec


def test_list_returns_newest_first(tmp_path):
    store = HistoryStore(tmp_path / "history.json")
    store.append(_record(lesson_id="first"))
    store.append(_record(lesson_id="second"))

    listed = store.list()
    assert [r.lesson_id for r in listed] == ["second", "first"]
```

- [x] **Step 2: Run to verify it fails**

Run: `python -m pytest tests/tui/test_history_store.py -v`
Expected: FAIL — `ImportError` (module missing).

- [x] **Step 3: Create `history_store.py`**

Create `src/tui/history_store.py`:

```python
"""Persisted run history stored as a JSON array."""

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional


@dataclass
class HistoryRecord:
    """A single completed (or failed) generation run."""

    timestamp: str
    lesson_id: str
    title: str
    engine: str
    duration_ms: int
    line_count: int
    script_path: str
    audio_file: Optional[str]
    srt_file: Optional[str]
    subtitle_file: Optional[str]
    timeline_file: Optional[str]
    success: bool
    error: Optional[str] = None


class HistoryStore:
    """Reads/writes HistoryRecords to a JSON file."""

    def __init__(self, path: str | Path):
        self.path = Path(path)

    def load(self) -> list[HistoryRecord]:
        """Return all records in insertion order (oldest first)."""
        if not self.path.exists():
            return []
        with open(self.path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [HistoryRecord(**row) for row in data]

    def list(self) -> list[HistoryRecord]:
        """Return all records newest-first (for display)."""
        return list(reversed(self.load()))

    def append(self, record: HistoryRecord) -> None:
        """Append a record and persist."""
        records = self.load()
        records.append(record)
        self._save(records)

    def _save(self, records: list[HistoryRecord]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump([asdict(r) for r in records], f, indent=2, ensure_ascii=False)
```

- [x] **Step 4: Run to verify it passes**

Run: `python -m pytest tests/tui/test_history_store.py -v`
Expected: PASS (3 tests).

- [x] **Step 5: Commit**

```bash
git add src/tui/history_store.py tests/tui/test_history_store.py
git commit -m "feat(tui): add HistoryStore for persisted run history"
```

---

## Task 4: Queue models and validation

**Files:**
- Create: `src/tui/models.py`
- Test: `tests/tui/test_models.py`

- [x] **Step 1: Write the failing test**

Create `tests/tui/test_models.py`:

```python
"""Tests for TUI queue models."""

import json

import pytest

from src.services.validator import ValidationError
from src.tui.models import QueueItem, QueueStatus, build_queue_item


def _write_script(path, lesson_id="lesson_x", title="My Title", text="Hello!"):
    data = {
        "lesson_id": lesson_id,
        "title": title,
        "lines": [{"id": 1, "speaker": "female_us_1", "text": text}],
    }
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_build_queue_item_from_valid_file(tmp_path):
    p = _write_script(tmp_path / "ok.json")
    item = build_queue_item(p)

    assert item.title == "My Title"
    assert item.lesson_id == "lesson_x"
    assert item.script_path == str(p)
    assert item.status == QueueStatus.QUEUED
    assert item.progress == 0.0


def test_build_queue_item_invalid_raises(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text(json.dumps({"lesson_id": "", "title": "", "lines": []}), encoding="utf-8")

    with pytest.raises(ValidationError):
        build_queue_item(p)
```

- [x] **Step 2: Run to verify it fails**

Run: `python -m pytest tests/tui/test_models.py -v`
Expected: FAIL — `ImportError` (module missing).

- [x] **Step 3: Create `models.py`**

Create `src/tui/models.py`:

```python
"""UI-side queue state models."""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional

from ..services.validator import ScriptValidator


class QueueStatus(str, Enum):
    """Lifecycle status of a queued topic."""

    QUEUED = "queued"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


@dataclass
class QueueItem:
    """A topic waiting to be (or being) generated."""

    script_path: str
    title: str
    lesson_id: str
    status: QueueStatus = QueueStatus.QUEUED
    progress: float = 0.0
    duration_ms: int = 0
    error: Optional[str] = None


def build_queue_item(script_path: str | Path) -> QueueItem:
    """
    Load + validate a script file and build a QueueItem.

    Raises ValidationError if the script is invalid (engine-independent checks:
    structure, duplicate IDs, emotion, speech_rate, etc.).
    """
    validator = ScriptValidator()  # no engine -> voice-name checks are skipped
    script = validator.load_script(script_path)
    validator.validate_or_raise(script)
    return QueueItem(
        script_path=str(script_path),
        title=script.title,
        lesson_id=script.lesson_id,
    )
```

- [x] **Step 4: Run to verify it passes**

Run: `python -m pytest tests/tui/test_models.py -v`
Expected: PASS (2 tests).

- [x] **Step 5: Commit**

```bash
git add src/tui/models.py tests/tui/test_models.py
git commit -m "feat(tui): add QueueItem model and build_queue_item validation"
```

---

## Task 5: Generation runner seam

**Files:**
- Create: `src/tui/runner.py`
- Test: `tests/tui/test_runner.py`

The runner isolates the TUI from the pipeline so tests never hit the network/ffmpeg. `PipelineRunner` is the real implementation; `FakeRunner` is a test helper that lives in `runner.py` so screens can import it for headless tests.

- [x] **Step 1: Write the failing test**

Create `tests/tui/test_runner.py`:

```python
"""Tests for the generation runner seam."""

from src.tui.runner import FakeRunner


def test_fake_runner_emits_progress_and_returns_result(tmp_path):
    runner = FakeRunner(total_lines=3, duration_ms=4200)
    seen = []

    result = runner.run(
        script_path="topics/a.json",
        output_dir=str(tmp_path),
        config=None,
        on_progress=lambda current, total: seen.append((current, total)),
    )

    assert seen == [(1, 3), (2, 3), (3, 3)]
    assert result.success is True
    assert result.duration_ms == 4200


def test_fake_runner_can_simulate_failure(tmp_path):
    runner = FakeRunner(total_lines=1, fail_with="boom")
    result = runner.run("topics/a.json", str(tmp_path), None, lambda c, t: None)

    assert result.success is False
    assert result.error == "boom"
```

- [x] **Step 2: Run to verify it fails**

Run: `python -m pytest tests/tui/test_runner.py -v`
Expected: FAIL — `ImportError` (module missing).

- [x] **Step 3: Create `runner.py`**

Create `src/tui/runner.py`:

```python
"""Generation runner seam — wraps Pipeline so the TUI can stay decoupled/testable."""

from pathlib import Path
from typing import Callable, Optional, Protocol

from ..models.config import Config
from ..pipeline import Pipeline, PipelineResult

ProgressCallback = Callable[[int, int], None]


class GenerationRunner(Protocol):
    """Runs one script to completion, reporting (current, total) line progress."""

    def run(
        self,
        script_path: str,
        output_dir: str,
        config: Config,
        on_progress: ProgressCallback,
    ) -> PipelineResult:
        ...


class PipelineRunner:
    """Real runner backed by the existing Pipeline."""

    def run(
        self,
        script_path: str,
        output_dir: str,
        config: Config,
        on_progress: ProgressCallback,
    ) -> PipelineResult:
        pipeline = Pipeline(config=config)

        def cb(current: int, total: int, result) -> None:
            on_progress(current, total)

        try:
            return pipeline.generate(script_path, output_dir, on_progress=cb)
        finally:
            pipeline.cleanup()


class FakeRunner:
    """Test runner: emits synthetic progress and returns a canned PipelineResult."""

    def __init__(self, total_lines: int = 1, duration_ms: int = 1000,
                 fail_with: Optional[str] = None):
        self.total_lines = total_lines
        self.duration_ms = duration_ms
        self.fail_with = fail_with

    def run(self, script_path, output_dir, config, on_progress) -> PipelineResult:
        lesson_id = Path(script_path).stem
        for i in range(1, self.total_lines + 1):
            on_progress(i, self.total_lines)
        if self.fail_with:
            return PipelineResult(
                success=False, lesson_id=lesson_id, title=lesson_id,
                audio_file=None, srt_file=None, timeline_file=None,
                subtitle_file=None, duration_ms=0, error=self.fail_with,
            )
        return PipelineResult(
            success=True, lesson_id=lesson_id, title=lesson_id,
            audio_file=f"{output_dir}/{lesson_id}.mp3",
            srt_file=f"{output_dir}/{lesson_id}.srt",
            timeline_file=f"{output_dir}/{lesson_id}_timeline.json",
            subtitle_file=f"{output_dir}/{lesson_id}_subtitles.json",
            duration_ms=self.duration_ms,
        )
```

- [x] **Step 4: Run to verify it passes**

Run: `python -m pytest tests/tui/test_runner.py -v`
Expected: PASS (2 tests).

- [x] **Step 5: Commit**

```bash
git add src/tui/runner.py tests/tui/test_runner.py
git commit -m "feat(tui): add generation runner seam with Pipeline + Fake implementations"
```

---

## Task 6: `AppState`

**Files:**
- Create: `src/tui/state.py`
- Test: covered indirectly by Task 7's app test (no standalone test — pure container).

- [x] **Step 1: Create `state.py`**

Create `src/tui/state.py`:

```python
"""Shared application state held by TtsApp and read/written by screens."""

from dataclasses import dataclass, field
from pathlib import Path

from ..models.config import Config
from .history_store import HistoryStore
from .models import QueueItem
from .runner import GenerationRunner, PipelineRunner


@dataclass
class AppState:
    """Live state shared across screens."""

    config: Config
    config_path: Path
    output_dir: Path
    history: HistoryStore
    runner: GenerationRunner = field(default_factory=PipelineRunner)
    queue: list[QueueItem] = field(default_factory=list)
```

- [x] **Step 2: Verify it imports**

Run: `python -c "from src.tui.state import AppState; print('ok')"`
Expected: prints `ok`.

- [x] **Step 3: Commit**

```bash
git add src/tui/state.py
git commit -m "feat(tui): add AppState shared-state container"
```

---

## Task 7: `TtsApp` shell with screen switching and ffmpeg check

**Files:**
- Create: `src/tui/app.py`
- Create: `src/tui/screens/__init__.py`
- Create placeholder screens so the app imports: see steps below.
- Test: `tests/tui/test_app.py`

- [x] **Step 1: Create the screens package marker**

Create `src/tui/screens/__init__.py`:

```python
```

- [x] **Step 2: Write the failing test**

Create `tests/tui/test_app.py`:

```python
"""Tests for the top-level TtsApp shell."""

import pytest

from src.models.config import Config
from src.tui.app import TtsApp
from src.tui.history_store import HistoryStore
from src.tui.runner import FakeRunner


def _make_app(tmp_path):
    return TtsApp(
        config=Config(),
        config_path=tmp_path / "config.yaml",
        output_dir=tmp_path / "output",
        runner=FakeRunner(),
        history_store=HistoryStore(tmp_path / "history.json"),
    )


@pytest.mark.asyncio
async def test_app_starts_on_queue_screen(tmp_path):
    app = _make_app(tmp_path)
    async with app.run_test() as pilot:
        assert app.screen.__class__.__name__ == "QueueScreen"


@pytest.mark.asyncio
async def test_app_switches_to_config_and_history(tmp_path):
    app = _make_app(tmp_path)
    async with app.run_test() as pilot:
        await pilot.press("c")
        assert app.screen.__class__.__name__ == "ConfigScreen"
        await pilot.press("escape")
        await pilot.press("h")
        assert app.screen.__class__.__name__ == "HistoryScreen"
```

Note: this test requires `pytest-asyncio`. Add it: `python -m pip install pytest-asyncio` and create `pytest.ini` if not present (Step 3).

- [x] **Step 3: Configure pytest-asyncio**

Run: `python -m pip install pytest-asyncio`

Create `pytest.ini` at repo root (if it does not exist):

```ini
[pytest]
asyncio_mode = auto
```

Add to `requirements.txt` (under a new "# Dev/test" section):

```
pytest>=8.0
pytest-asyncio>=0.23
```

- [x] **Step 4: Create minimal screens so the app imports**

Create `src/tui/screens/queue.py`:

```python
"""Queue screen (home)."""

from textual.screen import Screen
from textual.widgets import Header, Footer, Static


class QueueScreen(Screen):
    """Lists queued topics and runs them. (Filled out in Task 8.)"""

    def compose(self):
        yield Header()
        yield Static("Queue", id="queue-placeholder")
        yield Footer()
```

Create `src/tui/screens/config.py`:

```python
"""Config screen."""

from textual.screen import Screen
from textual.widgets import Header, Footer, Static


class ConfigScreen(Screen):
    """Edit + save configuration. (Filled out in Task 9.)"""

    BINDINGS = [("escape", "app.pop_screen", "Back")]

    def compose(self):
        yield Header()
        yield Static("Config", id="config-placeholder")
        yield Footer()
```

Create `src/tui/screens/history.py`:

```python
"""History screen."""

from textual.screen import Screen
from textual.widgets import Header, Footer, Static


class HistoryScreen(Screen):
    """Lists past runs. (Filled out in Task 10.)"""

    BINDINGS = [("escape", "app.pop_screen", "Back")]

    def compose(self):
        yield Header()
        yield Static("History", id="history-placeholder")
        yield Footer()
```

- [x] **Step 5: Create `app.py`**

Create `src/tui/app.py`:

```python
"""Top-level Textual application."""

import shutil
from pathlib import Path
from typing import Optional

from textual.app import App

from ..models.config import Config
from .history_store import HistoryStore
from .runner import GenerationRunner, PipelineRunner
from .screens.config import ConfigScreen
from .screens.history import HistoryScreen
from .screens.queue import QueueScreen
from .state import AppState


class TtsApp(App):
    """TTS & SRT generator console UI."""

    TITLE = "TTS & SRT Generator"

    BINDINGS = [
        ("c", "open_config", "Config"),
        ("h", "open_history", "History"),
        ("q", "quit", "Quit"),
    ]

    def __init__(
        self,
        config: Config,
        config_path: str | Path,
        output_dir: str | Path,
        runner: Optional[GenerationRunner] = None,
        history_store: Optional[HistoryStore] = None,
    ):
        super().__init__()
        output_dir = Path(output_dir)
        self.state = AppState(
            config=config,
            config_path=Path(config_path),
            output_dir=output_dir,
            history=history_store or HistoryStore(output_dir / "history.json"),
            runner=runner or PipelineRunner(),
        )

    def on_mount(self) -> None:
        if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
            self.notify(
                "ffmpeg/ffprobe not found on PATH — audio stitching will fail. "
                "Install ffmpeg and restart.",
                title="Missing dependency",
                severity="warning",
                timeout=10,
            )
        self.push_screen(QueueScreen())

    def action_open_config(self) -> None:
        self.push_screen(ConfigScreen())

    def action_open_history(self) -> None:
        self.push_screen(HistoryScreen())
```

- [x] **Step 6: Run to verify it passes**

Run: `python -m pytest tests/tui/test_app.py -v`
Expected: PASS (2 tests). The `c`/`h` bindings push screens; `escape` pops back.

- [x] **Step 7: Commit**

```bash
git add src/tui/app.py src/tui/screens/ tests/tui/test_app.py pytest.ini requirements.txt
git commit -m "feat(tui): add TtsApp shell with screen switching and ffmpeg check"
```

---

## Task 8: Queue screen — add topic, run all, live progress

**Files:**
- Modify: `src/tui/screens/queue.py`
- Test: `tests/tui/test_queue_screen.py`

The queue uses a `DataTable` (one row per item) and runs generation in a threaded worker. An `AddTopicScreen` modal uses a `DirectoryTree` to pick a `*.json` file; selection is validated via `build_queue_item`.

- [x] **Step 1: Write the failing test**

Create `tests/tui/test_queue_screen.py`:

```python
"""Tests for the Queue screen."""

import json

import pytest

from src.models.config import Config
from src.tui.app import TtsApp
from src.tui.history_store import HistoryStore
from src.tui.models import QueueItem, QueueStatus
from src.tui.runner import FakeRunner
from src.tui.screens.queue import QueueScreen


def _make_app(tmp_path, runner):
    return TtsApp(
        config=Config(),
        config_path=tmp_path / "config.yaml",
        output_dir=tmp_path / "output",
        runner=runner,
        history_store=HistoryStore(tmp_path / "history.json"),
    )


def _enqueue(app, script_path, title="T", lesson_id="L"):
    app.state.queue.append(
        QueueItem(script_path=str(script_path), title=title, lesson_id=lesson_id)
    )


@pytest.mark.asyncio
async def test_run_all_completes_items_and_records_history(tmp_path):
    app = _make_app(tmp_path, FakeRunner(total_lines=2, duration_ms=3000))
    async with app.run_test() as pilot:
        _enqueue(app, tmp_path / "a.json", lesson_id="a")
        screen = app.screen
        assert isinstance(screen, QueueScreen)
        screen.refresh_table()
        await pilot.press("enter")        # run all
        await pilot.pause()
        # worker is threaded; wait for it to finish
        await app.workers.wait_for_complete()
        await pilot.pause()

        assert app.state.queue[0].status == QueueStatus.DONE
        assert app.state.queue[0].progress == 1.0
        history = app.state.history.list()
        assert len(history) == 1
        assert history[0].success is True
        assert history[0].lesson_id == "a"


@pytest.mark.asyncio
async def test_run_all_marks_failure_and_continues(tmp_path):
    app = _make_app(tmp_path, FakeRunner(total_lines=1, fail_with="network down"))
    async with app.run_test() as pilot:
        _enqueue(app, tmp_path / "a.json", lesson_id="a")
        app.screen.refresh_table()
        await pilot.press("enter")
        await app.workers.wait_for_complete()
        await pilot.pause()

        assert app.state.queue[0].status == QueueStatus.FAILED
        assert app.state.queue[0].error == "network down"
        assert app.state.history.list()[0].success is False
```

- [x] **Step 2: Run to verify it fails**

Run: `python -m pytest tests/tui/test_queue_screen.py -v`
Expected: FAIL — `QueueScreen` has no `refresh_table` / no run behavior.

- [x] **Step 3: Implement the Queue screen**

Replace `src/tui/screens/queue.py` with:

```python
"""Queue screen (home): add topics, run them, show live progress."""

from datetime import datetime
from pathlib import Path

from textual import work
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.message import Message
from textual.screen import ModalScreen, Screen
from textual.widgets import (
    Button,
    DataTable,
    DirectoryTree,
    Footer,
    Header,
    Label,
    Static,
)

from ..history_store import HistoryRecord
from ..models import QueueItem, QueueStatus, build_queue_item
from ...services.validator import ValidationError


class AddTopicScreen(ModalScreen[QueueItem]):
    """Modal file picker for *.json topic scripts; dismisses with a QueueItem or None."""

    BINDINGS = [("escape", "cancel", "Cancel")]

    def __init__(self, start_dir: str):
        super().__init__()
        self.start_dir = start_dir

    def compose(self) -> ComposeResult:
        with Vertical(id="add-topic-dialog"):
            yield Label("Select a topic script (*.json)")
            yield DirectoryTree(self.start_dir, id="topic-tree")
            yield Static("", id="add-topic-error")

    def on_directory_tree_file_selected(
        self, event: DirectoryTree.FileSelected
    ) -> None:
        path = str(event.path)
        if not path.endswith(".json"):
            self.query_one("#add-topic-error", Static).update("Pick a .json file.")
            return
        try:
            item = build_queue_item(path)
        except (ValidationError, ValueError, FileNotFoundError) as exc:
            self.query_one("#add-topic-error", Static).update(f"Invalid: {exc}")
            return
        self.dismiss(item)

    def action_cancel(self) -> None:
        self.dismiss(None)


class QueueScreen(Screen):
    """Home screen: the generation queue."""

    BINDINGS = [
        ("a", "add_topic", "Add topic"),
        ("d", "remove_topic", "Remove"),
        ("enter", "run_all", "Run all"),
    ]

    class ItemProgress(Message):
        """Posted from the worker thread to update one item's progress."""

        def __init__(self, index: int, progress: float) -> None:
            super().__init__()
            self.index = index
            self.progress = progress

    def compose(self) -> ComposeResult:
        yield Header()
        table = DataTable(id="queue-table", cursor_type="row")
        table.add_columns("Topic", "Status", "Progress")
        yield table
        yield Static("", id="queue-status")
        yield Footer()

    def on_mount(self) -> None:
        self.refresh_table()

    @property
    def queue(self) -> list[QueueItem]:
        return self.app.state.queue

    def refresh_table(self) -> None:
        table = self.query_one("#queue-table", DataTable)
        table.clear()
        for item in self.queue:
            bar = self._bar(item.progress)
            table.add_row(Path(item.script_path).name, item.status.value, bar)

    @staticmethod
    def _bar(progress: float) -> str:
        filled = int(round(progress * 10))
        return "█" * filled + "░" * (10 - filled) + f" {int(progress * 100):3d}%"

    # --- actions ---

    def action_add_topic(self) -> None:
        topics_dir = str(Path("topics")) if Path("topics").exists() else "."

        def _on_close(item: QueueItem | None) -> None:
            if item is not None:
                self.queue.append(item)
                self.refresh_table()

        self.app.push_screen(AddTopicScreen(topics_dir), _on_close)

    def action_remove_topic(self) -> None:
        table = self.query_one("#queue-table", DataTable)
        if table.cursor_row is None or not self.queue:
            return
        row = table.cursor_row
        if 0 <= row < len(self.queue) and self.queue[row].status != QueueStatus.RUNNING:
            del self.queue[row]
            self.refresh_table()

    def action_run_all(self) -> None:
        if any(i.status == QueueStatus.RUNNING for i in self.queue):
            return
        if not any(i.status == QueueStatus.QUEUED for i in self.queue):
            return
        self.run_queue()

    # --- worker ---

    @work(thread=True, exclusive=True)
    def run_queue(self) -> None:
        state = self.app.state
        for index, item in enumerate(self.queue):
            if item.status != QueueStatus.QUEUED:
                continue
            item.status = QueueStatus.RUNNING
            self.app.call_from_thread(self.refresh_table)

            def on_progress(current: int, total: int, _idx=index) -> None:
                self.post_message(self.ItemProgress(_idx, current / total))

            result = state.runner.run(
                script_path=item.script_path,
                output_dir=str(state.output_dir),
                config=state.config,
                on_progress=on_progress,
            )

            item.duration_ms = result.duration_ms
            if result.success:
                item.status = QueueStatus.DONE
                item.progress = 1.0
            else:
                item.status = QueueStatus.FAILED
                item.error = result.error

            state.history.append(
                HistoryRecord(
                    timestamp=datetime.utcnow().isoformat() + "Z",
                    lesson_id=result.lesson_id,
                    title=result.title,
                    engine=state.config.engine,
                    duration_ms=result.duration_ms,
                    line_count=0,
                    script_path=item.script_path,
                    audio_file=result.audio_file,
                    srt_file=result.srt_file,
                    subtitle_file=result.subtitle_file,
                    timeline_file=result.timeline_file,
                    success=result.success,
                    error=result.error,
                )
            )
            self.app.call_from_thread(self.refresh_table)
            self.app.call_from_thread(
                self.query_one("#queue-status", Static).update,
                f"{'done' if result.success else 'FAILED'}: {result.lesson_id}",
            )

    def on_queue_screen_item_progress(self, message: "QueueScreen.ItemProgress") -> None:
        if 0 <= message.index < len(self.queue):
            self.queue[message.index].progress = message.progress
            self.refresh_table()
```

- [x] **Step 4: Run to verify it passes**

Run: `python -m pytest tests/tui/test_queue_screen.py -v`
Expected: PASS (2 tests).

- [x] **Step 5: Run the full suite**

Run: `python -m pytest -q`
Expected: all tests pass (existing + new).

- [x] **Step 6: Commit**

```bash
git add src/tui/screens/queue.py tests/tui/test_queue_screen.py
git commit -m "feat(tui): implement queue screen with add-topic, run-all worker, live progress"
```

---

## Task 9: Config screen — edit and save

**Files:**
- Modify: `src/tui/screens/config.py`
- Test: `tests/tui/test_config_screen.py`

v1 edits the scalar fields and persists via `save_config`; voice-map editing uses a simple `speaker_id=voice` per-line text area (full per-engine table + live Edge voice browser is a refinement; the editable text area keeps v1 testable and complete). Engine and output_format use `Select`.

- [x] **Step 1: Write the failing test**

Create `tests/tui/test_config_screen.py`:

```python
"""Tests for the Config screen."""

import pytest

from src.models.config import Config
from src.tui.app import TtsApp
from src.tui.config_io import load_config
from src.tui.history_store import HistoryStore
from src.tui.runner import FakeRunner
from src.tui.screens.config import ConfigScreen


def _make_app(tmp_path):
    return TtsApp(
        config=Config(),
        config_path=tmp_path / "config.yaml",
        output_dir=tmp_path / "output",
        runner=FakeRunner(),
        history_store=HistoryStore(tmp_path / "history.json"),
    )


@pytest.mark.asyncio
async def test_config_save_persists_changes(tmp_path):
    app = _make_app(tmp_path)
    async with app.run_test() as pilot:
        await pilot.press("c")
        screen = app.screen
        assert isinstance(screen, ConfigScreen)

        # change max_retries and save programmatically (UI inputs verified below)
        screen.query_one("#max_retries").value = "7"
        screen.query_one("#default_pause_ms").value = "555"
        screen.action_save()
        await pilot.pause()

    saved = load_config(tmp_path / "config.yaml")
    assert saved.synthesis.max_retries == 7
    assert saved.synthesis.default_pause_ms == 555
    # in-memory config also updated
    assert app.state.config.synthesis.max_retries == 7
```

- [x] **Step 2: Run to verify it fails**

Run: `python -m pytest tests/tui/test_config_screen.py -v`
Expected: FAIL — placeholder ConfigScreen has no inputs / no `action_save`.

- [x] **Step 3: Implement the Config screen**

Replace `src/tui/screens/config.py` with:

```python
"""Config screen: edit engine / voices / language / audio / synthesis params and save."""

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Input, Label, Select, Static, TextArea


class ConfigScreen(Screen):
    """Edit configuration and persist it to the YAML config path."""

    BINDINGS = [("escape", "app.pop_screen", "Back"), ("ctrl+s", "save", "Save")]

    def compose(self) -> ComposeResult:
        cfg = self.app.state.config
        yield Header()
        with VerticalScroll(id="config-form"):
            yield Label("Engine")
            yield Select(
                [("edge", "edge"), ("kokoro", "kokoro")],
                value=cfg.engine, id="engine", allow_blank=False,
            )

            yield Label("Audio: sample_rate")
            yield Input(str(cfg.audio.sample_rate), id="sample_rate")
            yield Label("Audio: normalize_to (dBFS)")
            yield Input(str(cfg.audio.normalize_to), id="normalize_to")
            yield Label("Audio: output_format")
            yield Select(
                [("mp3", "mp3"), ("wav", "wav")],
                value=cfg.audio.output_format, id="output_format", allow_blank=False,
            )

            yield Label("Synthesis: default_pause_ms")
            yield Input(str(cfg.synthesis.default_pause_ms), id="default_pause_ms")
            yield Label("Synthesis: initial_silence_ms")
            yield Input(str(cfg.synthesis.initial_silence_ms), id="initial_silence_ms")
            yield Label("Synthesis: max_retries")
            yield Input(str(cfg.synthesis.max_retries), id="max_retries")

            yield Label("Edge voices (one 'speaker_id=voice' per line)")
            yield TextArea(self._voices_text(cfg.edge.voices), id="edge_voices")

            yield Button("Save", id="save-btn", variant="primary")
            yield Static("", id="config-msg")
        yield Footer()

    @staticmethod
    def _voices_text(voices: dict) -> str:
        return "\n".join(f"{k}={v}" for k, v in voices.items())

    @staticmethod
    def _parse_voices(text: str) -> dict:
        out = {}
        for line in text.splitlines():
            line = line.strip()
            if not line or "=" not in line:
                continue
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip()
        return out

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save-btn":
            self.action_save()

    def action_save(self) -> None:
        from ..config_io import save_config

        cfg = self.app.state.config
        try:
            cfg.engine = str(self.query_one("#engine", Select).value)
            cfg.audio.sample_rate = int(self.query_one("#sample_rate", Input).value)
            cfg.audio.normalize_to = float(self.query_one("#normalize_to", Input).value)
            cfg.audio.output_format = str(self.query_one("#output_format", Select).value)
            cfg.synthesis.default_pause_ms = int(self.query_one("#default_pause_ms", Input).value)
            cfg.synthesis.initial_silence_ms = int(self.query_one("#initial_silence_ms", Input).value)
            cfg.synthesis.max_retries = int(self.query_one("#max_retries", Input).value)
            cfg.edge.voices = self._parse_voices(self.query_one("#edge_voices", TextArea).text)
            save_config(cfg, self.app.state.config_path)
        except (ValueError, OSError) as exc:
            self.query_one("#config-msg", Static).update(f"Save failed: {exc}")
            return
        self.query_one("#config-msg", Static).update("Saved.")
```

- [x] **Step 4: Run to verify it passes**

Run: `python -m pytest tests/tui/test_config_screen.py -v`
Expected: PASS (1 test).

- [x] **Step 5: Commit**

```bash
git add src/tui/screens/config.py tests/tui/test_config_screen.py
git commit -m "feat(tui): implement config screen with save-to-YAML"
```

---

## Task 10: History screen — list, view input/output, open, re-run

**Files:**
- Modify: `src/tui/screens/history.py`
- Test: `tests/tui/test_history_screen.py`

- [x] **Step 1: Write the failing test**

Create `tests/tui/test_history_screen.py`:

```python
"""Tests for the History screen."""

import pytest

from src.models.config import Config
from src.tui.app import TtsApp
from src.tui.history_store import HistoryRecord, HistoryStore
from src.tui.runner import FakeRunner
from src.tui.screens.history import HistoryScreen


def _record(lesson_id="a"):
    return HistoryRecord(
        timestamp="2026-06-11T10:00:00Z", lesson_id=lesson_id, title="T",
        engine="edge", duration_ms=1000, line_count=2,
        script_path="topics/a.json", audio_file="output/a.mp3",
        srt_file="output/a.srt", subtitle_file="output/a_subtitles.json",
        timeline_file="output/a_timeline.json", success=True, error=None,
    )


def _make_app(tmp_path):
    store = HistoryStore(tmp_path / "history.json")
    store.append(_record("a"))
    store.append(_record("b"))
    return TtsApp(
        config=Config(),
        config_path=tmp_path / "config.yaml",
        output_dir=tmp_path / "output",
        runner=FakeRunner(),
        history_store=store,
    )


@pytest.mark.asyncio
async def test_history_lists_newest_first(tmp_path):
    app = _make_app(tmp_path)
    async with app.run_test() as pilot:
        await pilot.press("h")
        screen = app.screen
        assert isinstance(screen, HistoryScreen)
        table = screen.query_one("#history-table")
        assert table.row_count == 2
        # newest first -> first data row is lesson "b"
        assert screen.records[0].lesson_id == "b"


@pytest.mark.asyncio
async def test_history_rerun_enqueues_script(tmp_path):
    app = _make_app(tmp_path)
    async with app.run_test() as pilot:
        await pilot.press("h")
        screen = app.screen
        screen.query_one("#history-table").move_cursor(row=0)
        screen.action_rerun()
        await pilot.pause()
        assert len(app.state.queue) == 1
        assert app.state.queue[0].script_path == "topics/a.json"  # 'b' is newest? see note
```

Note on the second test's expectation: the cursor starts at row 0 which is the newest record (`b`). Adjust the assertion to `lesson_id == "b"`'s script path. Since both fixtures use `topics/a.json` as `script_path`, the assertion on `script_path` holds regardless; if you give them distinct paths, expect the row-0 (newest) one. Keep `script_path="topics/a.json"` for both as written so the assertion is unambiguous.

- [x] **Step 2: Run to verify it fails**

Run: `python -m pytest tests/tui/test_history_screen.py -v`
Expected: FAIL — placeholder HistoryScreen has no table/records/action_rerun.

- [x] **Step 3: Implement the History screen**

Replace `src/tui/screens/history.py` with:

```python
"""History screen: list past runs, view input/output, open outputs, re-run."""

from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Header, Static

from ..models import build_queue_item
from ...services.validator import ValidationError


class HistoryScreen(Screen):
    """Browse persisted run history."""

    BINDINGS = [
        ("escape", "app.pop_screen", "Back"),
        ("o", "open_outputs", "Show outputs"),
        ("enter", "rerun", "Re-run"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        self.records = self.app.state.history.list()
        with Horizontal():
            table = DataTable(id="history-table", cursor_type="row")
            table.add_columns("When", "Title", "Engine", "Dur(s)", "Status")
            yield table
            yield Static("Select a run.", id="history-detail")
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#history-table", DataTable)
        for rec in self.records:
            table.add_row(
                rec.timestamp, rec.title, rec.engine,
                f"{rec.duration_ms / 1000:.1f}",
                "OK" if rec.success else "FAIL",
            )
        if self.records:
            self._show_detail(0)

    def _selected(self):
        table = self.query_one("#history-table", DataTable)
        row = table.cursor_row
        if row is None or not (0 <= row < len(self.records)):
            return None
        return self.records[row]

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        if event.cursor_row is not None and 0 <= event.cursor_row < len(self.records):
            self._show_detail(event.cursor_row)

    def _show_detail(self, index: int) -> None:
        rec = self.records[index]
        lines = [
            f"[b]{rec.title}[/b] ({rec.lesson_id})",
            f"script: {rec.script_path}",
            f"audio:  {rec.audio_file}",
            f"srt:    {rec.srt_file}",
            f"subs:   {rec.subtitle_file}",
            f"timeline: {rec.timeline_file}",
        ]
        if not rec.success:
            lines.append(f"[red]error: {rec.error}[/red]")
        self.query_one("#history-detail", Static).update("\n".join(lines))

    def action_open_outputs(self) -> None:
        rec = self._selected()
        if rec is None:
            return
        target = rec.audio_file or rec.srt_file
        msg = f"output dir: {Path(target).parent}" if target else "no outputs"
        self.query_one("#history-detail", Static).update(msg)

    def action_rerun(self) -> None:
        rec = self._selected()
        if rec is None:
            return
        try:
            item = build_queue_item(rec.script_path)
        except (ValidationError, ValueError, FileNotFoundError) as exc:
            self.query_one("#history-detail", Static).update(f"Cannot re-run: {exc}")
            return
        self.app.state.queue.append(item)
        self.query_one("#history-detail", Static).update(
            f"Re-queued {rec.lesson_id}. Go to Queue (esc) and press enter to run."
        )
```

- [x] **Step 4: Run to verify it passes**

Run: `python -m pytest tests/tui/test_history_screen.py -v`
Expected: PASS (2 tests).

Note: `action_rerun` calls `build_queue_item`, which reads `rec.script_path` from disk. In the test the path `topics/a.json` must exist and be valid, OR adjust the test to point `script_path` at a real fixture file created in `tmp_path`. **Before running, update `_record` in the test to write a valid script to `tmp_path` and use that path** (mirror `_write_script` from `tests/tui/test_models.py`). This keeps the re-run test hermetic.

- [x] **Step 5: Commit**

```bash
git add src/tui/screens/history.py tests/tui/test_history_screen.py
git commit -m "feat(tui): implement history screen with detail, open-outputs, re-run"
```

---

## Task 11: Wire the `tui` CLI command

**Files:**
- Modify: `main.py`

- [x] **Step 1: Add the command**

In `main.py`, after the existing imports add:

```python
from src.tui.app import TtsApp
from src.tui.config_io import load_config
```

Then add a new command (after the `generate` command):

```python
@cli.command()
@click.option(
    "-c", "--config", "config_path",
    type=click.Path(),
    default="config/default.yaml",
    help="Path to configuration file (created/updated by the Config screen)",
)
@click.option(
    "-o", "--output",
    type=click.Path(),
    default="output",
    help="Output directory (default: output/)",
)
def tui(config_path: str, output: str) -> None:
    """Launch the interactive console UI."""
    cfg = load_config(config_path)
    app = TtsApp(config=cfg, config_path=config_path, output_dir=output)
    app.run()
```

- [x] **Step 2: Smoke-test the import path**

Run: `python -c "import main; print('tui' in main.cli.commands)"`
Expected: prints `True`.

- [x] **Step 3: Manual launch check (interactive — run yourself)**

Run: `python main.py tui`
Expected: the TUI opens on the Queue screen; `a` opens the file picker over `topics/`, `c`/`h` switch to Config/History, `q` quits. If ffmpeg is not on PATH you'll see a warning toast.

- [x] **Step 4: Commit**

```bash
git add main.py
git commit -m "feat(tui): add 'tui' CLI command to launch the console UI"
```

---

## Task 12: Final verification

- [x] **Step 1: Run the whole suite**

Run: `python -m pytest -q`
Expected: all tests pass (existing pipeline/srt/validator tests + all `tests/tui/*`).

- [x] **Step 2: End-to-end manual run (with ffmpeg on PATH)**

Run `python main.py tui`, add `topics/conversation_1.json`, press `enter`, watch progress complete, then open History (`h`) and confirm the run is listed with its output paths. Confirm `output/<lesson_id>_subtitles.json` exists.

- [x] **Step 3: Update docs**

Add a short "Console UI" section to `README.md` describing `python main.py tui` and the three screens. Commit:

```bash
git add README.md
git commit -m "docs: document the console UI (tui) command"
```

---

## Self-review notes (for the implementer)

- **Spec coverage:** Queue/add/validate (Tasks 4, 8), live progress + sequential run + continue-on-failure (Task 8), History list/view/open/re-run (Task 10), Config edit/save incl. voices/audio/synthesis (Task 9), ffmpeg startup check (Task 7), persistence (Tasks 2, 3), runner seam for testability (Task 5). **Language config + live Edge voice browser** are represented minimally in v1 (engine + editable voice map); the full per-engine voice-browser modal using `list_voices_sync(language)` is a follow-up refinement — implement it by adding a "Browse voices" button to the Config screen that opens a modal listing `src.engines.edge.list_voices_sync(language)` results, if desired within v1.
- **v2 (separate plan):** in-TUI script Editor and audio replay (`ffplay`) are intentionally excluded here.
- **Textual API note:** verify `DataTable.cursor_row`, `move_cursor`, and `RowHighlighted` against the installed Textual version; if the API differs, adjust the small number of call sites in Tasks 8 and 10 (the logic and tests are otherwise version-independent).
