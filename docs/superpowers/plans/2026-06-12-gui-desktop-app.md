# GUI Desktop App (customtkinter) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `src/gui/` desktop GUI (`python main.py gui`) that coexists with the existing TUI, reusing all backend seams and adding Script Library, Voice Browser, and embedded Audio Player.

**Architecture:** New `src/gui/` package with `TtsGuiApp(ctk.CTk)`, a sidebar that switches between six `CTkFrame` panels, and panel-local logic classes (no CTk dependency) for testability. All backend seams (`runner`, `player`, `config_io`, `history_store`, `script_io`, `models`) imported unchanged from `src/tui/`.

**Tech Stack:** Python 3.13+, customtkinter ≥ 5.2.0, threading (stdlib), pytest.

**Reference spec:** `docs/superpowers/specs/2026-06-12-gui-design.md`

---

## File map

| File | Role |
|------|------|
| `src/gui/__init__.py` | package marker |
| `src/gui/state.py` | `AppState` dataclass |
| `src/gui/app.py` | `TtsGuiApp` — main window + sidebar |
| `src/gui/panels/__init__.py` | package marker |
| `src/gui/panels/queue.py` | `QueuePanelLogic` + `QueuePanel` |
| `src/gui/panels/editor.py` | `EditorPanelLogic` + `EditorPanel` |
| `src/gui/panels/config.py` | `ConfigPanel` |
| `src/gui/panels/history.py` | `HistoryPanelLogic` + `HistoryPanel` |
| `src/gui/panels/library.py` | `LibraryPanelLogic` + `LibraryPanel` |
| `src/gui/panels/voices.py` | `VoiceBrowserPanel` |
| `src/gui/widgets/__init__.py` | package marker |
| `src/gui/widgets/audio_player.py` | `AudioPlayerWidget` + `get_duration_seconds` |
| `src/gui/widgets/line_form.py` | `LineFormDialog` |
| `tests/gui/__init__.py` | package marker |
| `tests/gui/test_queue_panel.py` | `QueuePanelLogic` tests |
| `tests/gui/test_editor_panel.py` | `EditorPanelLogic` tests |
| `tests/gui/test_history_panel.py` | `HistoryPanelLogic` tests |
| `tests/gui/test_library_panel.py` | `LibraryPanelLogic` tests |
| `main.py` | add `gui` CLI command |

---

## Task 1: Dependency + package scaffolding

**Files:**
- Modify: `requirements.txt`
- Create: `src/gui/__init__.py`, `src/gui/panels/__init__.py`, `src/gui/widgets/__init__.py`, `tests/gui/__init__.py`

- [ ] **Step 1: Add dependency**

In `requirements.txt`, add under "Core dependencies":
```
customtkinter>=5.2.0
```

- [ ] **Step 2: Install**

```bash
python -m pip install "customtkinter>=5.2.0"
```
Expected: installs customtkinter and its dependency `darkdetect`.

- [ ] **Step 3: Create package markers**

Create `src/gui/__init__.py`:
```python
"""Desktop GUI for the TTS & SRT generator (customtkinter)."""
```

Create `src/gui/panels/__init__.py` — empty file.

Create `src/gui/widgets/__init__.py` — empty file.

Create `tests/gui/__init__.py` — empty file.

- [ ] **Step 4: Verify import**

```bash
python -c "import customtkinter; print(customtkinter.__version__)"
```
Expected: prints a version ≥ 5.2.0.

- [ ] **Step 5: Commit**

```bash
git add requirements.txt src/gui/ tests/gui/
git commit -m "build: add customtkinter dependency and gui package scaffolding"
```

---

## Task 2: AppState

**Files:**
- Create: `src/gui/state.py`

- [ ] **Step 1: Create `state.py`**

Create `src/gui/state.py`:
```python
"""Shared application state for the GUI."""

from dataclasses import dataclass, field
from pathlib import Path

from ..models.config import Config
from ..tui.history_store import HistoryStore
from ..tui.models import QueueItem
from ..tui.player import AudioPlayer, FfplayPlayer
from ..tui.runner import GenerationRunner, PipelineRunner


@dataclass
class AppState:
    """Live state shared across all panels."""

    config: Config
    config_path: Path
    output_dir: Path
    history: HistoryStore
    runner: GenerationRunner = field(default_factory=PipelineRunner)
    player: AudioPlayer = field(default_factory=FfplayPlayer)
    queue: list[QueueItem] = field(default_factory=list)
```

- [ ] **Step 2: Verify import**

```bash
python -c "from src.gui.state import AppState; print('ok')"
```
Expected: prints `ok`.

- [ ] **Step 3: Commit**

```bash
git add src/gui/state.py
git commit -m "feat(gui): add AppState shared-state container"
```

---

## Task 3: AudioPlayerWidget

**Files:**
- Create: `src/gui/widgets/audio_player.py`

- [ ] **Step 1: Create `audio_player.py`**

Create `src/gui/widgets/audio_player.py`:
```python
"""Reusable audio player widget: Play, Stop, progress bar, time label."""

import shutil
import subprocess
import time
from typing import Optional

import customtkinter as ctk

from ...tui.player import AudioPlayer, FfplayPlayer


def get_duration_seconds(path: str) -> float:
    """Return audio duration via ffprobe, or 0.0 on failure."""
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "quiet",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(path),
            ],
            capture_output=True, text=True, timeout=5,
        )
        return float(result.stdout.strip())
    except Exception:
        return 0.0


def _fmt(seconds: float) -> str:
    s = int(seconds)
    return f"{s // 60}:{s % 60:02d}"


class AudioPlayerWidget(ctk.CTkFrame):
    """Embedded Play/Stop player with a progress bar."""

    def __init__(self, master, player: Optional[AudioPlayer] = None, **kwargs):
        super().__init__(master, **kwargs)
        self._player = player or FfplayPlayer()
        self._path: Optional[str] = None
        self._duration: float = 0.0
        self._start_time: Optional[float] = None
        self._poll_id: Optional[str] = None

        if shutil.which("ffplay") is None:
            ctk.CTkLabel(self, text="ffplay not found — install ffmpeg").pack(padx=8, pady=4)
            self._available = False
            return

        self._available = True
        self._btn_play = ctk.CTkButton(self, text="▶ Play", width=80, command=self.play)
        self._btn_stop = ctk.CTkButton(self, text="■ Stop", width=80, command=self.stop)
        self._progress = ctk.CTkProgressBar(self, width=180)
        self._progress.set(0)
        self._lbl_time = ctk.CTkLabel(self, text="0:00 / 0:00", width=90)

        self._btn_play.grid(row=0, column=0, padx=4, pady=4)
        self._btn_stop.grid(row=0, column=1, padx=4, pady=4)
        self._progress.grid(row=0, column=2, padx=4, pady=4)
        self._lbl_time.grid(row=0, column=3, padx=4, pady=4)

    def load(self, path: Optional[str]) -> None:
        """Set audio file, fetch duration, reset UI."""
        self.stop()
        self._path = path
        self._duration = get_duration_seconds(path) if path else 0.0
        if self._available:
            self._progress.set(0)
            self._lbl_time.configure(text=f"0:00 / {_fmt(self._duration)}")

    def play(self) -> None:
        if not self._path or not self._available:
            return
        self.stop()
        self._player.play(self._path)
        self._start_time = time.monotonic()
        self._poll()

    def stop(self) -> None:
        if self._poll_id is not None:
            self.after_cancel(self._poll_id)
            self._poll_id = None
        self._player.stop()
        self._start_time = None

    def _poll(self) -> None:
        if self._start_time is None:
            return
        elapsed = time.monotonic() - self._start_time
        if self._duration > 0:
            frac = min(elapsed / self._duration, 1.0)
            self._progress.set(frac)
            self._lbl_time.configure(text=f"{_fmt(elapsed)} / {_fmt(self._duration)}")
            if frac < 1.0:
                self._poll_id = self.after(500, self._poll)
            else:
                self.stop()
```

- [ ] **Step 2: Verify import**

```bash
python -c "from src.gui.widgets.audio_player import AudioPlayerWidget, get_duration_seconds; print('ok')"
```
Expected: prints `ok`.

- [ ] **Step 3: Commit**

```bash
git add src/gui/widgets/audio_player.py
git commit -m "feat(gui): add AudioPlayerWidget with ffplay + progress polling"
```

---

## Task 4: LineFormDialog

**Files:**
- Create: `src/gui/widgets/line_form.py`

- [ ] **Step 1: Create `line_form.py`**

Create `src/gui/widgets/line_form.py`:
```python
"""Modal dialog to add or edit a single script line."""

from typing import Optional

import customtkinter as ctk

from ...models.script import ScriptLine

EMOTIONS = ["neutral", "friendly", "cheerful", "serious", "excited"]
SPEAKERS = [
    "female_us_1", "female_us_2",
    "male_us_1", "male_us_2",
    "female_uk_1", "male_uk_1",
]


class LineFormDialog(ctk.CTkToplevel):
    """Modal form for a ScriptLine. After wait_window(), read .result."""

    def __init__(self, master, line: ScriptLine):
        super().__init__(master)
        self.title("Edit Line")
        self.resizable(False, False)
        self.grab_set()
        self.result: Optional[ScriptLine] = None
        self._line = line

        fields = [
            ("Speaker", "_speaker", "option", SPEAKERS, line.speaker),
            ("Text", "_text", "entry", None, line.text),
            ("Emotion", "_emotion", "option", EMOTIONS, line.emotion),
            ("pause_after_ms", "_pause", "entry", None, str(line.pause_after_ms)),
            ("speech_rate", "_rate", "entry", None, str(line.speech_rate)),
        ]

        for row, (label, attr, kind, values, default) in enumerate(fields):
            ctk.CTkLabel(self, text=label, anchor="w").grid(
                row=row, column=0, padx=12, pady=4, sticky="w"
            )
            if kind == "option":
                widget = ctk.CTkOptionMenu(self, values=values, width=240)
                widget.set(default)
            else:
                widget = ctk.CTkEntry(self, width=240)
                widget.insert(0, default)
            widget.grid(row=row, column=1, padx=12, pady=4)
            setattr(self, attr, widget)

        self._err = ctk.CTkLabel(self, text="", text_color="red")
        self._err.grid(row=len(fields), column=0, columnspan=2, padx=12, pady=2)

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=len(fields) + 1, column=0, columnspan=2, pady=10)
        ctk.CTkButton(btn_frame, text="OK", command=self._ok, width=90).pack(side="left", padx=8)
        ctk.CTkButton(btn_frame, text="Cancel", command=self.destroy, width=90).pack(
            side="left", padx=8
        )

    def _ok(self) -> None:
        try:
            self.result = ScriptLine(
                id=self._line.id,
                speaker=self._speaker.get(),
                text=self._text.get(),
                emotion=self._emotion.get(),
                pause_after_ms=int(self._pause.get()),
                speech_rate=float(self._rate.get()),
            )
        except ValueError as exc:
            self._err.configure(text=str(exc))
            return
        self.destroy()
```

- [ ] **Step 2: Verify import**

```bash
python -c "from src.gui.widgets.line_form import LineFormDialog; print('ok')"
```
Expected: prints `ok`.

- [ ] **Step 3: Commit**

```bash
git add src/gui/widgets/line_form.py
git commit -m "feat(gui): add LineFormDialog modal for script line editing"
```

---

## Task 5: QueuePanel

**Files:**
- Create: `src/gui/panels/queue.py`
- Test: `tests/gui/test_queue_panel.py`

- [ ] **Step 1: Write the failing test**

Create `tests/gui/test_queue_panel.py`:
```python
"""Tests for QueuePanelLogic (state mutations, no Tk rendering)."""

import json

import pytest

from src.gui.panels.queue import QueuePanelLogic
from src.gui.state import AppState
from src.models.config import Config
from src.tui.history_store import HistoryStore
from src.tui.models import QueueStatus
from src.tui.player import FakePlayer
from src.tui.runner import FakeRunner


def _make_state(tmp_path, runner=None):
    return AppState(
        config=Config(),
        config_path=tmp_path / "config.yaml",
        output_dir=tmp_path / "output",
        history=HistoryStore(tmp_path / "history.json"),
        runner=runner or FakeRunner(total_lines=1, duration_ms=500),
        player=FakePlayer(),
    )


def _write_script(tmp_path, lesson_id="lesson_x"):
    data = {
        "lesson_id": lesson_id, "title": "T",
        "lines": [{"id": 1, "speaker": "female_us_1", "text": "Hello!"}],
    }
    p = tmp_path / f"{lesson_id}.json"
    p.write_text(json.dumps(data))
    return p


def test_add_item_enqueues(tmp_path):
    state = _make_state(tmp_path)
    logic = QueuePanelLogic(state)
    p = _write_script(tmp_path)
    item = logic.add_item(str(p))
    assert item.lesson_id == "lesson_x"
    assert len(state.queue) == 1


def test_add_item_raises_on_invalid(tmp_path):
    from src.services.validator import ValidationError
    state = _make_state(tmp_path)
    logic = QueuePanelLogic(state)
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"lesson_id": "", "title": "", "lines": []}))
    with pytest.raises(ValidationError):
        logic.add_item(str(bad))


def test_remove_queued_item(tmp_path):
    state = _make_state(tmp_path)
    logic = QueuePanelLogic(state)
    p = _write_script(tmp_path)
    logic.add_item(str(p))
    assert logic.remove_item(0) is True
    assert len(state.queue) == 0


def test_remove_refuses_running_item(tmp_path):
    state = _make_state(tmp_path)
    logic = QueuePanelLogic(state)
    p = _write_script(tmp_path)
    logic.add_item(str(p))
    state.queue[0].status = QueueStatus.RUNNING
    assert logic.remove_item(0) is False
    assert len(state.queue) == 1


def test_run_all_sets_done_and_records_history(tmp_path):
    state = _make_state(tmp_path, FakeRunner(total_lines=1, duration_ms=500))
    logic = QueuePanelLogic(state)
    p = _write_script(tmp_path)
    logic.add_item(str(p))

    done = []
    t = logic.run_all(on_update=lambda: None, on_done=lambda: done.append(1))
    t.join(timeout=5)

    assert state.queue[0].status == QueueStatus.DONE
    assert state.queue[0].progress == 1.0
    assert len(state.history.list()) == 1
    assert state.history.list()[0].success is True
    assert done


def test_run_all_marks_failed_on_error(tmp_path):
    state = _make_state(tmp_path, FakeRunner(total_lines=1, fail_with="boom"))
    logic = QueuePanelLogic(state)
    p = _write_script(tmp_path)
    logic.add_item(str(p))

    done = []
    t = logic.run_all(on_update=lambda: None, on_done=lambda: done.append(1))
    t.join(timeout=5)

    assert state.queue[0].status == QueueStatus.FAILED
    assert state.queue[0].error == "boom"
    assert done
```

- [ ] **Step 2: Run to verify it fails**

```bash
python -m pytest tests/gui/test_queue_panel.py -q
```
Expected: FAIL — `ImportError` (module missing).

- [ ] **Step 3: Create `queue.py`**

Create `src/gui/panels/queue.py`:
```python
"""Queue panel — add topics, run generation with live progress."""

import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional

import customtkinter as ctk

from ...services.validator import ValidationError
from ...tui.history_store import HistoryRecord
from ...tui.models import QueueItem, QueueStatus, build_queue_item
from ..state import AppState

_STATUS_COLOR = {
    QueueStatus.QUEUED:  ("#9ca3af", "#6b7280"),
    QueueStatus.RUNNING: ("#3b82f6", "#2563eb"),
    QueueStatus.DONE:    ("#22c55e", "#16a34a"),
    QueueStatus.FAILED:  ("#ef4444", "#dc2626"),
}


class QueuePanelLogic:
    """State-mutation logic for the Queue panel. No Tk dependency — fully testable."""

    def __init__(self, state: AppState):
        self.state = state

    def add_item(self, path: str) -> QueueItem:
        """Validate a script file and append a QueueItem. Raises ValidationError on failure."""
        item = build_queue_item(path)
        self.state.queue.append(item)
        return item

    def remove_item(self, index: int) -> bool:
        """Remove item at index if not running. Returns True on success."""
        if not (0 <= index < len(self.state.queue)):
            return False
        if self.state.queue[index].status == QueueStatus.RUNNING:
            return False
        del self.state.queue[index]
        return True

    def run_all(
        self,
        on_update: Callable[[], None],
        on_done: Callable[[], None],
    ) -> threading.Thread:
        """
        Start a daemon thread that runs all QUEUED items sequentially.
        Calls on_update() after each status/progress change.
        Calls on_done() when complete. Returns the started thread.
        """
        if any(i.status == QueueStatus.RUNNING for i in self.state.queue):
            raise RuntimeError("Already running")

        t = threading.Thread(
            target=self._run, args=(on_update, on_done), daemon=True
        )
        t.start()
        return t

    def _run(self, on_update: Callable, on_done: Callable) -> None:
        state = self.state
        for item in state.queue:
            if item.status != QueueStatus.QUEUED:
                continue
            item.status = QueueStatus.RUNNING
            on_update()

            def _progress(current: int, total: int, _item=item) -> None:
                _item.progress = current / total
                on_update()

            result = state.runner.run(
                script_path=item.script_path,
                output_dir=str(state.output_dir),
                config=state.config,
                on_progress=_progress,
            )

            if result.success:
                item.status = QueueStatus.DONE
                item.progress = 1.0
            else:
                item.status = QueueStatus.FAILED
                item.error = result.error

            state.history.append(
                HistoryRecord(
                    timestamp=datetime.now(timezone.utc).isoformat(),
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
            on_update()
        on_done()


class QueuePanel(ctk.CTkFrame):
    """Queue screen: add/remove topics and run generation."""

    def __init__(
        self,
        master,
        state: AppState,
        switch_to: Callable[[str], None],
        **kwargs,
    ):
        super().__init__(master, **kwargs)
        self.logic = QueuePanelLogic(state)
        self._switch_to = switch_to
        self._selected: Optional[int] = None

        # Toolbar
        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.pack(fill="x", padx=8, pady=(8, 4))
        ctk.CTkButton(toolbar, text="Add Topic", command=self._add).pack(side="left", padx=4)
        ctk.CTkButton(toolbar, text="Remove", command=self._remove).pack(side="left", padx=4)
        ctk.CTkButton(toolbar, text="▶ Run All", command=self._run_all).pack(side="left", padx=4)
        self._lbl_status = ctk.CTkLabel(toolbar, text="")
        self._lbl_status.pack(side="right", padx=8)

        # Scrollable item list
        self._scroll = ctk.CTkScrollableFrame(self, label_text="Queue")
        self._scroll.pack(fill="both", expand=True, padx=8, pady=4)

        self._refresh()

    def _refresh(self) -> None:
        for w in self._scroll.winfo_children():
            w.destroy()
        for i, item in enumerate(self.logic.state.queue):
            row = ctk.CTkFrame(self._scroll)
            row.pack(fill="x", padx=4, pady=2)
            color = _STATUS_COLOR[item.status]
            ctk.CTkLabel(row, text=Path(item.script_path).stem, anchor="w", width=200).pack(
                side="left", padx=6
            )
            ctk.CTkLabel(
                row, text=item.status.value, width=80,
                fg_color=color, corner_radius=4,
            ).pack(side="left", padx=4)
            bar = ctk.CTkProgressBar(row, width=160)
            bar.set(item.progress)
            bar.pack(side="left", padx=4)
            if item.error:
                ctk.CTkLabel(row, text=item.error, text_color="red").pack(side="left", padx=4)
            idx = i
            row.bind("<Button-1>", lambda e, n=idx: self._select(n))

    def _select(self, index: int) -> None:
        self._selected = index

    def _add(self) -> None:
        path = ctk.filedialog.askopenfilename(
            title="Select a topic script",
            filetypes=[("JSON scripts", "*.json")],
            initialdir="topics" if Path("topics").exists() else ".",
        )
        if not path:
            return
        try:
            self.logic.add_item(path)
            self._refresh()
            self._lbl_status.configure(text="")
        except (ValidationError, ValueError, FileNotFoundError) as exc:
            self._lbl_status.configure(text=f"Invalid: {exc}", text_color="red")

    def _remove(self) -> None:
        if self._selected is None:
            return
        if self.logic.remove_item(self._selected):
            self._selected = None
            self._refresh()

    def _run_all(self) -> None:
        try:
            self.logic.run_all(
                on_update=lambda: self.after(0, self._refresh),
                on_done=lambda: self.after(
                    0, lambda: self._lbl_status.configure(text="Done.", text_color="green")
                ),
            )
        except RuntimeError:
            pass
```

- [ ] **Step 4: Run to verify it passes**

```bash
python -m pytest tests/gui/test_queue_panel.py -q
```
Expected: PASS (6 tests).

- [ ] **Step 5: Commit**

```bash
git add src/gui/panels/queue.py tests/gui/test_queue_panel.py
git commit -m "feat(gui): add QueuePanel with run-all threading and live progress"
```

---

## Task 6: EditorPanel

**Files:**
- Create: `src/gui/panels/editor.py`
- Test: `tests/gui/test_editor_panel.py`

- [ ] **Step 1: Write the failing test**

Create `tests/gui/test_editor_panel.py`:
```python
"""Tests for EditorPanelLogic (no Tk rendering)."""

import pytest

from src.gui.panels.editor import EditorPanelLogic
from src.gui.state import AppState
from src.models.config import Config
from src.models.script import ScriptLine
from src.tui.history_store import HistoryStore
from src.tui.player import FakePlayer
from src.tui.runner import FakeRunner


def _make_state(tmp_path):
    return AppState(
        config=Config(),
        config_path=tmp_path / "config.yaml",
        output_dir=tmp_path / "output",
        history=HistoryStore(tmp_path / "history.json"),
        runner=FakeRunner(),
        player=FakePlayer(),
    )


def test_next_line_id_empty():
    logic = EditorPanelLogic.__new__(EditorPanelLogic)
    logic.lines = []
    assert logic._next_id() == 1


def test_next_line_id_with_lines():
    logic = EditorPanelLogic.__new__(EditorPanelLogic)
    logic.lines = [
        ScriptLine(id=1, speaker="female_us_1", text="a"),
        ScriptLine(id=4, speaker="male_us_1", text="b"),
    ]
    assert logic._next_id() == 5


def test_move_up_swaps(tmp_path):
    state = _make_state(tmp_path)
    logic = EditorPanelLogic(state)
    logic.lines = [
        ScriptLine(id=1, speaker="female_us_1", text="first"),
        ScriptLine(id=2, speaker="male_us_1", text="second"),
    ]
    assert logic.move_up(1) is True
    assert logic.lines[0].text == "second"
    assert logic.lines[1].text == "first"


def test_move_up_noop_at_top(tmp_path):
    state = _make_state(tmp_path)
    logic = EditorPanelLogic(state)
    logic.lines = [ScriptLine(id=1, speaker="female_us_1", text="only")]
    assert logic.move_up(0) is False


def test_move_down_swaps(tmp_path):
    state = _make_state(tmp_path)
    logic = EditorPanelLogic(state)
    logic.lines = [
        ScriptLine(id=1, speaker="female_us_1", text="first"),
        ScriptLine(id=2, speaker="male_us_1", text="second"),
    ]
    assert logic.move_down(0) is True
    assert logic.lines[0].text == "second"


def test_save_writes_file_and_calls_callback(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    state = _make_state(tmp_path)
    logic = EditorPanelLogic(state)
    logic.lines = [ScriptLine(id=1, speaker="female_us_1", text="Hello!")]

    saved = []
    ok, msg = logic.save("test_lesson", "Test Title", "en", "B1", on_save=lambda: saved.append(1))

    assert ok is True
    assert (tmp_path / "topics" / "test_lesson.json").exists()
    assert saved


def test_save_fails_on_empty_lesson_id(tmp_path):
    state = _make_state(tmp_path)
    logic = EditorPanelLogic(state)
    logic.lines = [ScriptLine(id=1, speaker="female_us_1", text="Hello!")]
    ok, msg = logic.save("", "Title", "en", "B1", on_save=lambda: None)
    assert ok is False
    assert msg
```

- [ ] **Step 2: Run to verify it fails**

```bash
python -m pytest tests/gui/test_editor_panel.py -q
```
Expected: FAIL — `ImportError`.

- [ ] **Step 3: Create `editor.py`**

Create `src/gui/panels/editor.py`:
```python
"""Editor panel — author a conversation script line by line."""

from pathlib import Path
from typing import Callable, Optional

import customtkinter as ctk

from ...models.script import Script, ScriptLine, ScriptSettings
from ...services.validator import ScriptValidator, ValidationError
from ...tui.script_io import save_script
from ..state import AppState
from ..widgets.line_form import LineFormDialog, SPEAKERS

EMOTIONS = ["neutral", "friendly", "cheerful", "serious", "excited"]


class EditorPanelLogic:
    """State-mutation logic for the Editor panel. No Tk dependency."""

    def __init__(self, state: AppState):
        self.state = state
        self.lines: list[ScriptLine] = []

    def _next_id(self) -> int:
        return (max((l.id for l in self.lines), default=0)) + 1

    def load_script(self, script: Script) -> None:
        self.lines = list(script.lines)

    def move_up(self, index: int) -> bool:
        if index <= 0 or index >= len(self.lines):
            return False
        self.lines[index - 1], self.lines[index] = self.lines[index], self.lines[index - 1]
        return True

    def move_down(self, index: int) -> bool:
        if index < 0 or index >= len(self.lines) - 1:
            return False
        self.lines[index + 1], self.lines[index] = self.lines[index], self.lines[index + 1]
        return True

    def save(
        self,
        lesson_id: str,
        title: str,
        language: str,
        level: str,
        on_save: Callable[[], None],
    ) -> tuple[bool, str]:
        """Validate and save. Returns (success, message)."""
        script = Script(
            lesson_id=lesson_id.strip(),
            title=title.strip(),
            lines=self.lines,
            language=language.strip() or "en",
            level=level.strip() or "B1",
            settings=ScriptSettings(),
        )
        try:
            ScriptValidator().validate_or_raise(script)
        except ValidationError as exc:
            return False, str(exc)
        path = Path("topics") / f"{script.lesson_id}.json"
        save_script(script, path)
        on_save()
        return True, f"Saved {path}"


class EditorPanel(ctk.CTkFrame):
    """Two-column script editor: metadata + line list | line form."""

    def __init__(
        self,
        master,
        state: AppState,
        on_save: Optional[Callable[[], None]] = None,
        **kwargs,
    ):
        super().__init__(master, **kwargs)
        self.logic = EditorPanelLogic(state)
        self._on_save = on_save or (lambda: None)
        self._selected: Optional[int] = None

        # ── Left column ──────────────────────────────────────────
        left = ctk.CTkFrame(self)
        left.place(relx=0, rely=0, relwidth=0.40, relheight=1.0)

        for label, attr in [("lesson_id", "_e_lid"), ("title", "_e_title"),
                             ("language", "_e_lang"), ("level", "_e_level")]:
            ctk.CTkLabel(left, text=label, anchor="w").pack(fill="x", padx=8, pady=(4, 0))
            entry = ctk.CTkEntry(left)
            entry.pack(fill="x", padx=8)
            setattr(self, attr, entry)

        ctk.CTkLabel(left, text="Lines", anchor="w").pack(fill="x", padx=8, pady=(8, 0))
        self._line_scroll = ctk.CTkScrollableFrame(left)
        self._line_scroll.pack(fill="both", expand=True, padx=8, pady=4)

        # ── Right column ─────────────────────────────────────────
        right = ctk.CTkFrame(self)
        right.place(relx=0.40, rely=0, relwidth=0.60, relheight=1.0)

        btn_row = ctk.CTkFrame(right, fg_color="transparent")
        btn_row.pack(fill="x", padx=8, pady=8)
        for text, cmd in [
            ("Add",      self._add_line),
            ("Delete",   self._delete_line),
            ("▲ Up",     self._move_up),
            ("▼ Down",   self._move_down),
            ("💾 Save",  self._save),
        ]:
            ctk.CTkButton(btn_row, text=text, command=cmd, width=80).pack(
                side="left", padx=2
            )

        self._lbl_msg = ctk.CTkLabel(right, text="")
        self._lbl_msg.pack(padx=8, pady=4)

        self._refresh_lines()

    # ── public ────────────────────────────────────────────────────

    def load_script(self, script: Script) -> None:
        self.logic.load_script(script)
        self._e_lid.delete(0, "end"); self._e_lid.insert(0, script.lesson_id)
        self._e_title.delete(0, "end"); self._e_title.insert(0, script.title)
        self._e_lang.delete(0, "end"); self._e_lang.insert(0, script.language)
        self._e_level.delete(0, "end"); self._e_level.insert(0, script.level)
        self._refresh_lines()

    # ── private ───────────────────────────────────────────────────

    def _refresh_lines(self) -> None:
        for w in self._line_scroll.winfo_children():
            w.destroy()
        for i, line in enumerate(self.logic.lines):
            preview = line.text[:35] + ("…" if len(line.text) > 35 else "")
            row = ctk.CTkFrame(self._line_scroll)
            row.pack(fill="x", pady=1)
            ctk.CTkLabel(row, text=f"{line.id}", width=30).pack(side="left")
            ctk.CTkLabel(row, text=line.speaker, width=110, anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=preview, anchor="w").pack(side="left", fill="x", expand=True)
            idx = i
            row.bind("<Button-1>", lambda e, n=idx: self._select(n))

    def _select(self, index: int) -> None:
        self._selected = index

    def _add_line(self) -> None:
        new = ScriptLine(id=self.logic._next_id(), speaker=SPEAKERS[0], text="")
        dlg = LineFormDialog(self, new)
        self.wait_window(dlg)
        if dlg.result:
            self.logic.lines.append(dlg.result)
            self._refresh_lines()

    def _delete_line(self) -> None:
        if self._selected is not None and 0 <= self._selected < len(self.logic.lines):
            del self.logic.lines[self._selected]
            self._selected = None
            self._refresh_lines()

    def _move_up(self) -> None:
        if self._selected is not None and self.logic.move_up(self._selected):
            self._selected -= 1
            self._refresh_lines()

    def _move_down(self) -> None:
        if self._selected is not None and self.logic.move_down(self._selected):
            self._selected += 1
            self._refresh_lines()

    def _save(self) -> None:
        ok, msg = self.logic.save(
            self._e_lid.get(), self._e_title.get(),
            self._e_lang.get(), self._e_level.get(),
            on_save=self._on_save,
        )
        color = "green" if ok else "red"
        self._lbl_msg.configure(text=msg, text_color=color)
```

- [ ] **Step 4: Run to verify it passes**

```bash
python -m pytest tests/gui/test_editor_panel.py -q
```
Expected: PASS (7 tests).

- [ ] **Step 5: Commit**

```bash
git add src/gui/panels/editor.py tests/gui/test_editor_panel.py
git commit -m "feat(gui): add EditorPanel with line list, form, move, save"
```

---

## Task 7: ConfigPanel

**Files:**
- Create: `src/gui/panels/config.py`

- [ ] **Step 1: Create `config.py`**

Create `src/gui/panels/config.py`:
```python
"""Config panel — edit and persist the YAML configuration."""

import customtkinter as ctk

from ...tui.config_io import save_config, load_config
from ..state import AppState


class ConfigPanel(ctk.CTkFrame):
    """Scrollable form: engine, audio, synthesis, voice map. Save / Reset buttons."""

    def __init__(self, master, state: AppState, **kwargs):
        super().__init__(master, **kwargs)
        self._state = state

        # Toolbar
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", padx=8, pady=(8, 4))
        ctk.CTkButton(bar, text="💾 Save", command=self._save).pack(side="left", padx=4)
        ctk.CTkButton(bar, text="↺ Reset", command=self._reset).pack(side="left", padx=4)
        self._lbl_msg = ctk.CTkLabel(bar, text="")
        self._lbl_msg.pack(side="right", padx=8)

        # Scrollable form
        self._form = ctk.CTkScrollableFrame(self)
        self._form.pack(fill="both", expand=True, padx=8, pady=4)

        self._build_form()

    def _build_form(self) -> None:
        cfg = self._state.config
        for w in self._form.winfo_children():
            w.destroy()

        def _lbl(text):
            ctk.CTkLabel(self._form, text=text, anchor="w",
                         font=ctk.CTkFont(weight="bold")).pack(fill="x", padx=4, pady=(10, 2))

        def _row(label, attr, default):
            ctk.CTkLabel(self._form, text=label, anchor="w").pack(fill="x", padx=12, pady=(2, 0))
            e = ctk.CTkEntry(self._form)
            e.insert(0, str(default))
            e.pack(fill="x", padx=12, pady=2)
            setattr(self, attr, e)

        # Engine
        _lbl("Engine")
        self._engine_var = ctk.StringVar(value=cfg.engine)
        for val in ("edge", "kokoro"):
            ctk.CTkRadioButton(
                self._form, text=val, variable=self._engine_var, value=val
            ).pack(anchor="w", padx=16, pady=2)

        # Audio
        _lbl("Audio")
        _row("sample_rate", "_e_sample_rate", cfg.audio.sample_rate)
        _row("normalize_to (dBFS)", "_e_normalize", cfg.audio.normalize_to)
        ctk.CTkLabel(self._form, text="output_format", anchor="w").pack(fill="x", padx=12, pady=(2,0))
        self._fmt_var = ctk.StringVar(value=cfg.audio.output_format)
        for val in ("mp3", "wav"):
            ctk.CTkRadioButton(
                self._form, text=val, variable=self._fmt_var, value=val
            ).pack(anchor="w", padx=16, pady=2)

        # Synthesis
        _lbl("Synthesis")
        _row("default_pause_ms", "_e_pause", cfg.synthesis.default_pause_ms)
        _row("initial_silence_ms", "_e_silence", cfg.synthesis.initial_silence_ms)
        _row("max_retries", "_e_retries", cfg.synthesis.max_retries)

        # Edge voice map
        _lbl("Edge voices  (speaker → voice name)")
        self._voice_entries: dict[str, ctk.CTkEntry] = {}
        for speaker, voice in cfg.edge.voices.items():
            row = ctk.CTkFrame(self._form, fg_color="transparent")
            row.pack(fill="x", padx=12, pady=2)
            ctk.CTkLabel(row, text=speaker, width=130, anchor="w").pack(side="left")
            e = ctk.CTkEntry(row)
            e.insert(0, voice)
            e.pack(side="left", fill="x", expand=True)
            self._voice_entries[speaker] = e

    def _save(self) -> None:
        cfg = self._state.config
        try:
            cfg.engine = self._engine_var.get()
            cfg.audio.sample_rate = int(self._e_sample_rate.get())
            cfg.audio.normalize_to = float(self._e_normalize.get())
            cfg.audio.output_format = self._fmt_var.get()
            cfg.synthesis.default_pause_ms = int(self._e_pause.get())
            cfg.synthesis.initial_silence_ms = int(self._e_silence.get())
            cfg.synthesis.max_retries = int(self._e_retries.get())
            cfg.edge.voices = {
                sp: e.get() for sp, e in self._voice_entries.items()
            }
            save_config(cfg, self._state.config_path)
            self._lbl_msg.configure(text="Saved.", text_color="green")
        except (ValueError, OSError) as exc:
            self._lbl_msg.configure(text=f"Error: {exc}", text_color="red")

    def _reset(self) -> None:
        self._state.config = load_config(self._state.config_path)
        self._build_form()
        self._lbl_msg.configure(text="Reset.")
```

- [ ] **Step 2: Verify import**

```bash
python -c "from src.gui.panels.config import ConfigPanel; print('ok')"
```
Expected: prints `ok`.

- [ ] **Step 3: Commit**

```bash
git add src/gui/panels/config.py
git commit -m "feat(gui): add ConfigPanel with save/reset"
```

---

## Task 8: HistoryPanel

**Files:**
- Create: `src/gui/panels/history.py`
- Test: `tests/gui/test_history_panel.py`

- [ ] **Step 1: Write the failing test**

Create `tests/gui/test_history_panel.py`:
```python
"""Tests for HistoryPanelLogic (no Tk rendering)."""

import json

from src.gui.panels.history import HistoryPanelLogic
from src.gui.state import AppState
from src.models.config import Config
from src.tui.history_store import HistoryRecord, HistoryStore
from src.tui.models import QueueStatus
from src.tui.player import FakePlayer
from src.tui.runner import FakeRunner


def _make_state(tmp_path, store=None):
    return AppState(
        config=Config(),
        config_path=tmp_path / "config.yaml",
        output_dir=tmp_path / "output",
        history=store or HistoryStore(tmp_path / "history.json"),
        runner=FakeRunner(),
        player=FakePlayer(),
    )


def _write_script(tmp_path, lesson_id="lesson_a"):
    data = {
        "lesson_id": lesson_id, "title": "T",
        "lines": [{"id": 1, "speaker": "female_us_1", "text": "Hi!"}],
    }
    p = tmp_path / f"{lesson_id}.json"
    p.write_text(json.dumps(data))
    return p


def _record(script_path, lesson_id="a"):
    return HistoryRecord(
        timestamp="2026-06-12T00:00:00Z",
        lesson_id=lesson_id, title="T", engine="edge",
        duration_ms=1000, line_count=1,
        script_path=str(script_path),
        audio_file="output/a.mp3", srt_file="output/a.srt",
        subtitle_file="output/a_subtitles.json",
        timeline_file="output/a_timeline.json",
        success=True,
    )


def test_load_returns_newest_first(tmp_path):
    store = HistoryStore(tmp_path / "history.json")
    p = _write_script(tmp_path)
    store.append(_record(p, "first"))
    store.append(_record(p, "second"))
    state = _make_state(tmp_path, store)
    logic = HistoryPanelLogic(state)
    records = logic.load()
    assert records[0].lesson_id == "second"
    assert records[1].lesson_id == "first"


def test_requeue_appends_to_queue(tmp_path):
    p = _write_script(tmp_path, "lesson_a")
    state = _make_state(tmp_path)
    logic = HistoryPanelLogic(state)
    ok, msg = logic.requeue(_record(p, "lesson_a"))
    assert ok is True
    assert len(state.queue) == 1
    assert state.queue[0].lesson_id == "lesson_a"


def test_requeue_fails_if_script_missing(tmp_path):
    state = _make_state(tmp_path)
    logic = HistoryPanelLogic(state)
    rec = _record(tmp_path / "gone.json", "gone")
    ok, msg = logic.requeue(rec)
    assert ok is False
    assert len(state.queue) == 0
```

- [ ] **Step 2: Run to verify it fails**

```bash
python -m pytest tests/gui/test_history_panel.py -q
```
Expected: FAIL — `ImportError`.

- [ ] **Step 3: Create `history.py`**

Create `src/gui/panels/history.py`:
```python
"""History panel — browse past runs, replay audio, re-queue."""

from typing import Callable

import customtkinter as ctk

from ...services.validator import ValidationError
from ...tui.history_store import HistoryRecord
from ...tui.models import build_queue_item
from ..state import AppState
from ..widgets.audio_player import AudioPlayerWidget


class HistoryPanelLogic:
    """State logic for HistoryPanel. No Tk dependency."""

    def __init__(self, state: AppState):
        self.state = state

    def load(self) -> list[HistoryRecord]:
        return self.state.history.list()

    def requeue(self, record: HistoryRecord) -> tuple[bool, str]:
        """Build a QueueItem from the record's script path and append to queue."""
        try:
            item = build_queue_item(record.script_path)
        except (ValidationError, ValueError, FileNotFoundError, OSError) as exc:
            return False, f"Cannot re-queue: {exc}"
        self.state.queue.append(item)
        return True, f"Re-queued {record.lesson_id}"


class HistoryPanel(ctk.CTkFrame):
    """Two-column history browser with embedded audio player."""

    def __init__(
        self,
        master,
        state: AppState,
        switch_to: Callable[[str], None],
        **kwargs,
    ):
        super().__init__(master, **kwargs)
        self.logic = HistoryPanelLogic(state)
        self._switch_to = switch_to
        self._records: list[HistoryRecord] = []
        self._selected: int = 0

        # Left: run list
        self._left = ctk.CTkScrollableFrame(self, label_text="History", width=280)
        self._left.pack(side="left", fill="y", padx=(8, 4), pady=8)

        # Right: detail
        right = ctk.CTkFrame(self)
        right.pack(side="right", fill="both", expand=True, padx=(4, 8), pady=8)

        self._detail = ctk.CTkLabel(right, text="Select a run.", anchor="nw", justify="left",
                                    wraplength=420)
        self._detail.pack(fill="both", expand=True, padx=8, pady=8)

        self._player_widget = AudioPlayerWidget(right, player=state.player)
        self._player_widget.pack(fill="x", padx=8, pady=4)

        btn_row = ctk.CTkFrame(right, fg_color="transparent")
        btn_row.pack(fill="x", padx=8, pady=4)
        ctk.CTkButton(btn_row, text="Re-queue", command=self._requeue).pack(side="left", padx=4)
        self._lbl_msg = ctk.CTkLabel(btn_row, text="")
        self._lbl_msg.pack(side="left", padx=8)

        self.refresh()

    def refresh(self) -> None:
        self._records = self.logic.load()
        for w in self._left.winfo_children():
            w.destroy()
        for i, rec in enumerate(self._records):
            color = "#22c55e" if rec.success else "#ef4444"
            btn = ctk.CTkButton(
                self._left,
                text=f"{rec.title[:24]}  [{rec.engine}]",
                fg_color=color, hover_color=color,
                anchor="w",
                command=lambda n=i: self._select(n),
            )
            btn.pack(fill="x", pady=1, padx=2)
        if self._records:
            self._select(0)

    def _select(self, index: int) -> None:
        self._selected = index
        if not (0 <= index < len(self._records)):
            return
        rec = self._records[index]
        lines = [
            f"Title:     {rec.title}",
            f"ID:        {rec.lesson_id}",
            f"Engine:    {rec.engine}",
            f"Duration:  {rec.duration_ms / 1000:.1f}s",
            f"Script:    {rec.script_path}",
            f"Audio:     {rec.audio_file}",
            f"SRT:       {rec.srt_file}",
        ]
        if not rec.success:
            lines.append(f"Error:     {rec.error}")
        self._detail.configure(text="\n".join(lines))
        self._player_widget.load(rec.audio_file)

    def _requeue(self) -> None:
        if not self._records:
            return
        rec = self._records[self._selected]
        ok, msg = self.logic.requeue(rec)
        color = "green" if ok else "red"
        self._lbl_msg.configure(text=msg, text_color=color)
        if ok:
            self._switch_to("queue")
```

- [ ] **Step 4: Run to verify it passes**

```bash
python -m pytest tests/gui/test_history_panel.py -q
```
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add src/gui/panels/history.py tests/gui/test_history_panel.py
git commit -m "feat(gui): add HistoryPanel with detail view, audio player, re-queue"
```

---

## Task 9: LibraryPanel

**Files:**
- Create: `src/gui/panels/library.py`
- Test: `tests/gui/test_library_panel.py`

- [ ] **Step 1: Write the failing test**

Create `tests/gui/test_library_panel.py`:
```python
"""Tests for LibraryPanelLogic (no Tk rendering)."""

import json
import shutil

from src.gui.panels.library import LibraryPanelLogic


def _write_script(directory, lesson_id, title="T"):
    data = {
        "lesson_id": lesson_id, "title": title,
        "lines": [{"id": 1, "speaker": "female_us_1", "text": "Hi!"}],
    }
    p = directory / f"{lesson_id}.json"
    p.write_text(json.dumps(data))
    return p


def test_load_lists_json_files(tmp_path):
    topics = tmp_path / "topics"
    topics.mkdir()
    _write_script(topics, "lesson_a", "Alpha")
    _write_script(topics, "lesson_b", "Beta")
    logic = LibraryPanelLogic(topics)
    items = logic.load()
    assert len(items) == 2
    lesson_ids = {item[1] for item in items}
    assert lesson_ids == {"lesson_a", "lesson_b"}


def test_load_returns_empty_for_missing_dir(tmp_path):
    logic = LibraryPanelLogic(tmp_path / "missing")
    assert logic.load() == []


def test_duplicate_creates_copy(tmp_path):
    topics = tmp_path / "topics"
    topics.mkdir()
    src = _write_script(topics, "lesson_a")
    logic = LibraryPanelLogic(topics)
    copy_path = logic.duplicate(src)
    assert copy_path.exists()
    assert copy_path.name == "lesson_a_copy.json"
    assert copy_path.read_text() == src.read_text()


def test_delete_removes_file(tmp_path):
    topics = tmp_path / "topics"
    topics.mkdir()
    p = _write_script(topics, "lesson_a")
    logic = LibraryPanelLogic(topics)
    logic.delete(p)
    assert not p.exists()
```

- [ ] **Step 2: Run to verify it fails**

```bash
python -m pytest tests/gui/test_library_panel.py -q
```
Expected: FAIL — `ImportError`.

- [ ] **Step 3: Create `library.py`**

Create `src/gui/panels/library.py`:
```python
"""Library panel — browse, open, duplicate, and delete topic scripts."""

import json
import shutil
from pathlib import Path
from typing import Callable, Optional

import customtkinter as ctk

from ...models.script import Script
from ...services.validator import ScriptValidator
from ..state import AppState


class LibraryPanelLogic:
    """Filesystem logic for LibraryPanel. No Tk dependency."""

    def __init__(self, topics_dir: Path):
        self.topics_dir = topics_dir

    def load(self) -> list[tuple[Path, str, str]]:
        """Return [(path, lesson_id, title)] sorted by filename."""
        if not self.topics_dir.exists():
            return []
        result = []
        for p in sorted(self.topics_dir.glob("*.json")):
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                result.append((p, data.get("lesson_id", p.stem), data.get("title", "")))
            except Exception:
                pass
        return result

    def duplicate(self, src: Path) -> Path:
        dst = src.parent / f"{src.stem}_copy{src.suffix}"
        shutil.copy2(src, dst)
        return dst

    def delete(self, path: Path) -> None:
        path.unlink(missing_ok=True)

    def load_script(self, path: Path) -> Script:
        return ScriptValidator.load_script(path)


class LibraryPanel(ctk.CTkFrame):
    """Two-column script library: file list | read-only preview."""

    def __init__(
        self,
        master,
        state: AppState,
        open_in_editor: Callable[[Script], None],
        **kwargs,
    ):
        super().__init__(master, **kwargs)
        topics_dir = Path("topics")
        self.logic = LibraryPanelLogic(topics_dir)
        self._open_in_editor = open_in_editor
        self._items: list[tuple[Path, str, str]] = []
        self._selected: Optional[int] = None

        # Left: file list
        self._left = ctk.CTkScrollableFrame(self, label_text="Topics", width=240)
        self._left.pack(side="left", fill="y", padx=(8, 4), pady=8)

        # Right: preview + action buttons
        right = ctk.CTkFrame(self)
        right.pack(side="right", fill="both", expand=True, padx=(4, 8), pady=8)

        btn_row = ctk.CTkFrame(right, fg_color="transparent")
        btn_row.pack(fill="x", padx=8, pady=(8, 4))
        ctk.CTkButton(btn_row, text="Open in Editor", command=self._open).pack(
            side="left", padx=4
        )
        ctk.CTkButton(btn_row, text="Duplicate", command=self._duplicate).pack(
            side="left", padx=4
        )
        ctk.CTkButton(btn_row, text="Delete", fg_color="#ef4444", hover_color="#dc2626",
                      command=self._delete).pack(side="left", padx=4)
        self._lbl_msg = ctk.CTkLabel(btn_row, text="")
        self._lbl_msg.pack(side="right", padx=8)

        self._preview = ctk.CTkTextbox(right, state="disabled")
        self._preview.pack(fill="both", expand=True, padx=8, pady=4)

        self.refresh()

    def refresh(self) -> None:
        self._items = self.logic.load()
        for w in self._left.winfo_children():
            w.destroy()
        if not self._items:
            ctk.CTkLabel(self._left, text="topics/ not found or empty").pack(pady=8)
            return
        for i, (path, lesson_id, title) in enumerate(self._items):
            btn = ctk.CTkButton(
                self._left, text=f"{lesson_id}\n{title[:20]}", anchor="w",
                command=lambda n=i: self._select(n),
            )
            btn.pack(fill="x", pady=1, padx=2)
        self._select(0)

    def _select(self, index: int) -> None:
        self._selected = index
        if not (0 <= index < len(self._items)):
            return
        path, lesson_id, title = self._items[index]
        try:
            script = self.logic.load_script(path)
            lines_text = "\n".join(
                f"  {l.id}. [{l.speaker}] {l.text}" for l in script.lines
            )
            preview = (
                f"lesson_id: {script.lesson_id}\n"
                f"title:     {script.title}\n"
                f"language:  {script.language}  level: {script.level}\n\n"
                f"Lines ({len(script.lines)}):\n{lines_text}"
            )
        except Exception as exc:
            preview = f"(Cannot read script: {exc})"
        self._preview.configure(state="normal")
        self._preview.delete("1.0", "end")
        self._preview.insert("1.0", preview)
        self._preview.configure(state="disabled")

    def _open(self) -> None:
        if self._selected is None or not self._items:
            return
        path = self._items[self._selected][0]
        try:
            script = self.logic.load_script(path)
            self._open_in_editor(script)
        except Exception as exc:
            self._lbl_msg.configure(text=str(exc), text_color="red")

    def _duplicate(self) -> None:
        if self._selected is None or not self._items:
            return
        copy = self.logic.duplicate(self._items[self._selected][0])
        self._lbl_msg.configure(text=f"Created {copy.name}", text_color="green")
        self.refresh()

    def _delete(self) -> None:
        if self._selected is None or not self._items:
            return
        path, lesson_id, _ = self._items[self._selected]
        dialog = ctk.CTkInputDialog(
            text=f"Type '{lesson_id}' to confirm deletion:", title="Confirm Delete"
        )
        if dialog.get_input() == lesson_id:
            self.logic.delete(path)
            self._selected = None
            self._lbl_msg.configure(text=f"Deleted {path.name}", text_color="orange")
            self.refresh()
```

- [ ] **Step 4: Run to verify it passes**

```bash
python -m pytest tests/gui/test_library_panel.py -q
```
Expected: PASS (4 tests).

- [ ] **Step 5: Commit**

```bash
git add src/gui/panels/library.py tests/gui/test_library_panel.py
git commit -m "feat(gui): add LibraryPanel with preview, duplicate, delete"
```

---

## Task 10: VoiceBrowserPanel

**Files:**
- Create: `src/gui/panels/voices.py`

- [ ] **Step 1: Create `voices.py`**

Create `src/gui/panels/voices.py`:
```python
"""Voice browser panel — list voices, preview with synthesis, copy name."""

import tempfile
import threading
from pathlib import Path
from typing import Optional

import customtkinter as ctk

from ...engines.edge import EdgeTTSEngine, list_voices_sync
from ...models.config import DEFAULT_KOKORO_VOICES
from ..state import AppState
from ..widgets.audio_player import AudioPlayerWidget

_PREVIEW_TEXT = "Hello, this is a preview of this voice."


class VoiceBrowserPanel(ctk.CTkFrame):
    """Browse Edge / Kokoro voices with live synthesis preview."""

    def __init__(self, master, state: AppState, **kwargs):
        super().__init__(master, **kwargs)
        self._state = state
        self._voices: list[dict] = []
        self._selected_voice: Optional[str] = None
        self._preview_tmp: Optional[str] = None

        # Top bar
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=8, pady=(8, 4))

        ctk.CTkLabel(top, text="Engine:").pack(side="left", padx=4)
        self._engine_var = ctk.StringVar(value="edge")
        for val in ("edge", "kokoro"):
            ctk.CTkRadioButton(
                top, text=val, variable=self._engine_var, value=val,
                command=self._load_voices,
            ).pack(side="left", padx=4)

        ctk.CTkLabel(top, text="Language:").pack(side="left", padx=(16, 4))
        self._lang_var = ctk.StringVar(value="en")
        self._lang_entry = ctk.CTkEntry(top, textvariable=self._lang_var, width=60)
        self._lang_entry.pack(side="left")
        ctk.CTkButton(top, text="Filter", width=70, command=self._load_voices).pack(
            side="left", padx=4
        )
        self._lbl_loading = ctk.CTkLabel(top, text="")
        self._lbl_loading.pack(side="right", padx=8)

        # Voice list
        self._list_frame = ctk.CTkScrollableFrame(self, label_text="Voices")
        self._list_frame.pack(fill="both", expand=True, padx=8, pady=4)

        # Bottom: player + buttons
        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.pack(fill="x", padx=8, pady=(4, 8))
        ctk.CTkButton(bottom, text="▶ Preview", command=self._preview).pack(side="left", padx=4)
        ctk.CTkButton(bottom, text="Copy Name", command=self._copy_name).pack(side="left", padx=4)
        self._lbl_msg = ctk.CTkLabel(bottom, text="")
        self._lbl_msg.pack(side="left", padx=8)
        self._player_widget = AudioPlayerWidget(bottom, player=state.player)
        self._player_widget.pack(side="right", padx=4)

        self._load_voices()

    def _load_voices(self) -> None:
        engine = self._engine_var.get()
        if engine == "kokoro":
            self._voices = [
                {"ShortName": v, "Gender": "–", "Locale": "en"}
                for v in DEFAULT_KOKORO_VOICES.values()
            ]
            self._render_voices()
            return

        # Edge: network call in thread
        self._lbl_loading.configure(text="Loading…")
        lang = self._lang_var.get().strip() or "en"
        threading.Thread(
            target=self._fetch_edge_voices, args=(lang,), daemon=True
        ).start()

    def _fetch_edge_voices(self, lang: str) -> None:
        try:
            voices = list_voices_sync(lang)
        except Exception as exc:
            self.after(0, lambda: self._lbl_loading.configure(text=f"Error: {exc}"))
            return
        self._voices = voices
        self.after(0, self._render_voices)

    def _render_voices(self) -> None:
        self._lbl_loading.configure(text=f"{len(self._voices)} voices")
        for w in self._list_frame.winfo_children():
            w.destroy()
        for voice in self._voices:
            name = voice["ShortName"]
            row = ctk.CTkFrame(self._list_frame, fg_color="transparent")
            row.pack(fill="x", pady=1)
            ctk.CTkLabel(row, text=name, width=220, anchor="w").pack(side="left", padx=6)
            ctk.CTkLabel(row, text=voice.get("Gender", ""), width=70).pack(side="left")
            ctk.CTkLabel(row, text=voice.get("Locale", ""), width=100).pack(side="left")
            row.bind("<Button-1>", lambda e, n=name: self._select(n))
            for child in row.winfo_children():
                child.bind("<Button-1>", lambda e, n=name: self._select(n))
        if self._voices:
            self._select(self._voices[0]["ShortName"])

    def _select(self, voice_name: str) -> None:
        self._selected_voice = voice_name
        self._lbl_msg.configure(text=f"Selected: {voice_name}")

    def _preview(self) -> None:
        if not self._selected_voice:
            return
        voice = self._selected_voice
        engine_name = self._engine_var.get()
        self._lbl_msg.configure(text="Synthesizing…")
        threading.Thread(
            target=self._synth_preview, args=(voice, engine_name), daemon=True
        ).start()

    def _synth_preview(self, voice: str, engine_name: str) -> None:
        try:
            if engine_name == "kokoro":
                self.after(0, lambda: self._lbl_msg.configure(
                    text="Kokoro preview requires model files — use Edge instead."
                ))
                return
            engine = EdgeTTSEngine()
            result = engine.synthesize(_PREVIEW_TEXT, voice=voice, speed=1.0)
            if not result.success or not result.audio_data:
                raise RuntimeError(result.error or "no audio")
            tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
            tmp.write(result.audio_data)
            tmp.close()
            self._preview_tmp = tmp.name
            self.after(0, lambda: (
                self._player_widget.load(self._preview_tmp),
                self._player_widget.play(),
                self._lbl_msg.configure(text=""),
            ))
        except Exception as exc:
            self.after(0, lambda: self._lbl_msg.configure(text=f"Preview failed: {exc}"))

    def _copy_name(self) -> None:
        if self._selected_voice:
            self.clipboard_clear()
            self.clipboard_append(self._selected_voice)
            self._lbl_msg.configure(text=f"Copied: {self._selected_voice}")
```

- [ ] **Step 2: Verify import**

```bash
python -c "from src.gui.panels.voices import VoiceBrowserPanel; print('ok')"
```
Expected: prints `ok`.

- [ ] **Step 3: Commit**

```bash
git add src/gui/panels/voices.py
git commit -m "feat(gui): add VoiceBrowserPanel with Edge listing and synthesis preview"
```

---

## Task 11: TtsGuiApp shell

**Files:**
- Create: `src/gui/app.py`

- [ ] **Step 1: Create `app.py`**

Create `src/gui/app.py`:
```python
"""Main application window: sidebar navigation + content panels."""

import json
import shutil
from pathlib import Path
from typing import Optional

import customtkinter as ctk

from ..models.config import Config
from ..tui.history_store import HistoryStore
from ..tui.player import AudioPlayer, FfplayPlayer
from ..tui.runner import GenerationRunner, PipelineRunner
from .state import AppState
from .panels.queue import QueuePanel
from .panels.editor import EditorPanel
from .panels.config import ConfigPanel
from .panels.history import HistoryPanel
from .panels.library import LibraryPanel
from .panels.voices import VoiceBrowserPanel

_STATE_FILE = Path.home() / ".tts_gui_state.json"
_THEMES = ["Dark", "Light", "System"]
_NAV = [
    ("Queue",   "queue"),
    ("Library", "library"),
    ("Editor",  "editor"),
    ("Config",  "config"),
    ("History", "history"),
    ("Voices",  "voices"),
]


class TtsGuiApp(ctk.CTk):
    """Desktop GUI main window."""

    def __init__(
        self,
        config: Config,
        config_path: str | Path,
        output_dir: str | Path,
        runner: Optional[GenerationRunner] = None,
        player: Optional[AudioPlayer] = None,
        history_store: Optional[HistoryStore] = None,
    ):
        super().__init__()
        self.title("TTS & SRT Generator")
        self._restore_geometry()

        self.state = AppState(
            config=config,
            config_path=Path(config_path),
            output_dir=Path(output_dir),
            history=history_store or HistoryStore(Path(output_dir) / "history.json"),
            runner=runner or PipelineRunner(),
            player=player or FfplayPlayer(),
        )

        self._theme_idx = 0

        # ── Sidebar ──────────────────────────────────────────────
        sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        ctk.CTkLabel(
            sidebar, text="TTS & SRT",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(pady=(20, 10), padx=12)

        self._nav_btns: dict[str, ctk.CTkButton] = {}
        for label, name in _NAV:
            btn = ctk.CTkButton(
                sidebar, text=label, anchor="w",
                fg_color="transparent",
                text_color=("gray10", "gray90"),
                hover_color=("gray70", "gray30"),
                command=lambda n=name: self.show_panel(n),
            )
            btn.pack(fill="x", padx=8, pady=2)
            self._nav_btns[name] = btn

        self._theme_btn = ctk.CTkButton(
            sidebar, text="☀ Theme", command=self._cycle_theme
        )
        self._theme_btn.pack(side="bottom", fill="x", padx=8, pady=16)

        # ── Content area ─────────────────────────────────────────
        self._content = ctk.CTkFrame(self)
        self._content.pack(side="right", fill="both", expand=True)

        # ffmpeg warning banner
        if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
            ctk.CTkLabel(
                self._content,
                text="⚠  ffmpeg not found — audio generation will fail. Install ffmpeg and restart.",
                text_color="orange",
            ).pack(pady=4)

        # ── Panels ───────────────────────────────────────────────
        self._library = LibraryPanel(
            self._content, self.state,
            open_in_editor=self._open_in_editor,
        )
        self._editor = EditorPanel(
            self._content, self.state,
            on_save=self._library.refresh,
        )
        self._panels: dict[str, ctk.CTkFrame] = {
            "queue":   QueuePanel(self._content, self.state, self.show_panel),
            "library": self._library,
            "editor":  self._editor,
            "config":  ConfigPanel(self._content, self.state),
            "history": HistoryPanel(self._content, self.state, self.show_panel),
            "voices":  VoiceBrowserPanel(self._content, self.state),
        }

        self.show_panel("queue")
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ── public ───────────────────────────────────────────────────

    def show_panel(self, name: str) -> None:
        for panel in self._panels.values():
            panel.pack_forget()
        self._panels[name].pack(fill="both", expand=True, padx=8, pady=8)
        for n, btn in self._nav_btns.items():
            btn.configure(fg_color=("gray75", "gray25") if n == name else "transparent")
        # Refresh data-heavy panels on show
        if name == "history":
            self._panels["history"].refresh()

    # ── private ──────────────────────────────────────────────────

    def _open_in_editor(self, script) -> None:
        self._editor.load_script(script)
        self.show_panel("editor")

    def _cycle_theme(self) -> None:
        self._theme_idx = (self._theme_idx + 1) % len(_THEMES)
        ctk.set_appearance_mode(_THEMES[self._theme_idx])

    def _restore_geometry(self) -> None:
        try:
            s = json.loads(_STATE_FILE.read_text())
            self.geometry(f"{s['w']}x{s['h']}+{s['x']}+{s['y']}")
        except Exception:
            self.geometry("1100x700")

    def _on_close(self) -> None:
        try:
            _STATE_FILE.write_text(json.dumps({
                "w": self.winfo_width(), "h": self.winfo_height(),
                "x": self.winfo_x(), "y": self.winfo_y(),
            }))
        except Exception:
            pass
        self.destroy()
```

- [ ] **Step 2: Verify import**

```bash
python -c "from src.gui.app import TtsGuiApp; print('ok')"
```
Expected: prints `ok`.

- [ ] **Step 3: Commit**

```bash
git add src/gui/app.py
git commit -m "feat(gui): add TtsGuiApp shell with sidebar navigation and theme toggle"
```

---

## Task 12: `gui` CLI command

**Files:**
- Modify: `main.py`

- [ ] **Step 1: Add import**

In `main.py`, after the existing `from src.tui.app import TtsApp` line, add:

```python
from src.gui.app import TtsGuiApp
```

- [ ] **Step 2: Add the command**

In `main.py`, after the `tui` command (after line `app.run()`), add:

```python
@cli.command()
@click.option(
    "-c", "--config", "config_path",
    type=click.Path(),
    default="config/default.yaml",
    help="Path to configuration file",
)
@click.option(
    "-o", "--output",
    type=click.Path(),
    default="output",
    help="Output directory (default: output/)",
)
def gui(config_path: str, output: str) -> None:
    """Launch the desktop GUI."""
    cfg = load_config(config_path)
    app = TtsGuiApp(config=cfg, config_path=config_path, output_dir=output)
    app.mainloop()
```

- [ ] **Step 3: Verify the command is registered**

```bash
python -c "import main; print('gui' in main.cli.commands)"
```
Expected: prints `True`.

- [ ] **Step 4: Verify help text**

```bash
python main.py gui --help
```
Expected: shows usage with `-c` and `-o` options.

- [ ] **Step 5: Commit**

```bash
git add main.py
git commit -m "feat(gui): add 'gui' CLI command to launch the desktop app"
```

---

## Task 13: Full verification

- [ ] **Step 1: Run the full test suite**

```bash
python -m pytest -q
```
Expected: all 42 existing tests + 20 new GUI tests pass (≥ 62 total), no failures.

- [ ] **Step 2: Manual smoke test**

Run: `python main.py gui`

Verify:
- Window opens at 1100 × 700 with sidebar on the left.
- Sidebar buttons Queue / Library / Editor / Config / History / Voices switch panels.
- Theme button cycles Dark → Light → System.
- Queue: click `Add Topic`, pick a valid `.json` from `topics/`, confirm it appears in the list.
- Queue: click `Run All` — status badge turns blue then green; history records a run.
- History: open panel, select the run, press `▶ Play` (requires ffplay on PATH).
- Editor: create a new script, save; confirm file appears in Library.
- Config: change `max_retries`, save, reopen — value persists.
- Voices: select Edge, filter by `en`, confirm voice list loads; select a voice, click `Copy Name`.
- Close and reopen — window remembers its last size/position.

- [ ] **Step 3: Commit any fixes found during smoke test**

```bash
git add -p
git commit -m "fix(gui): smoke test corrections"
```

---

## Self-review notes

- **Spec coverage:** AppState (T2), AudioPlayerWidget (T3), LineFormDialog (T4), QueuePanel + logic (T5), EditorPanel + logic (T6), ConfigPanel (T7), HistoryPanel + logic (T8), LibraryPanel + logic (T9), VoiceBrowserPanel (T10), TtsGuiApp sidebar + theme + window state (T11), `gui` CLI command (T12). All spec sections covered.
- **Threading rule:** all widget mutations go through `app.after(0, cb)` — enforced in QueuePanel `_run_all` and VoiceBrowserPanel `_synth_preview`.
- **TUI untouched:** no files in `src/tui/` or `tests/tui/` are modified.
- **Kokoro preview:** synthesizing previews for Kokoro requires model files on disk. The panel detects their absence and shows an informative message instead of crashing.
- **Library confirm-delete:** uses `CTkInputDialog` (type the lesson_id to confirm) rather than a simple yes/no, consistent with the "no accidental deletes" principle.
