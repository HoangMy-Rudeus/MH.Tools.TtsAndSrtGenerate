# Console UI (TUI) v2 Implementation Plan — Editor + Audio Replay

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:executing-plans (or subagent-driven-development). Steps use `- [ ]` checkboxes.

**Goal:** Add an in-TUI script Editor (per-line modal form) and audio replay (ffplay) to the existing console UI.

**Architecture:** New `script_io` (serialize/save Script) and `player` (ffplay wrapper, injectable) modules; a new `EditorScreen` + `LineFormScreen` modal; audio replay wired into the existing History screen. Reuses `Script`/`ScriptLine`/`ScriptValidator` and the v1 `AppState`.

**Tech Stack:** Python, Textual, pytest + pytest-asyncio, ffplay (from ffmpeg).

**Spec:** `docs/superpowers/specs/2026-06-11-tts-console-ui-v2-design.md`

---

## Task 1: `script_io` — serialize + save Script

**Files:** Create `src/tui/script_io.py`; Test `tests/tui/test_script_io.py`

- [ ] **Step 1: Failing test**

```python
"""Tests for script serialization."""

from src.models.script import Script, ScriptLine, ScriptSettings
from src.services.validator import ScriptValidator
from src.tui.script_io import save_script, script_to_dict


def _script():
    return Script(
        lesson_id="lesson_x", title="Title",
        lines=[
            ScriptLine(id=1, speaker="female_us_1", text="Hello!", emotion="cheerful", pause_after_ms=500),
            ScriptLine(id=2, speaker="male_us_1", text="Hi there!"),
        ],
        language="en", level="A2",
        settings=ScriptSettings(speech_rate=1.0, initial_silence_ms=500, default_pause_ms=400),
    )


def test_script_to_dict_round_trips_through_parser():
    parsed = ScriptValidator.parse_script(script_to_dict(_script()))
    assert parsed.lesson_id == "lesson_x"
    assert parsed.title == "Title"
    assert [l.id for l in parsed.lines] == [1, 2]
    assert parsed.lines[0].emotion == "cheerful"
    assert parsed.lines[0].pause_after_ms == 500
    assert parsed.settings.initial_silence_ms == 500


def test_save_script_writes_valid_loadable_file(tmp_path):
    path = tmp_path / "lesson_x.json"
    save_script(_script(), path)
    loaded = ScriptValidator.load_script(path)
    assert loaded.lesson_id == "lesson_x"
    assert len(loaded.lines) == 2
```

- [ ] **Step 2: Run, expect fail** — `python -m pytest tests/tui/test_script_io.py -q` → ImportError.

- [ ] **Step 3: Implement**

```python
"""Serialize and save conversation scripts to JSON."""

import json
from pathlib import Path

from ..models.script import Script


def script_to_dict(script: Script) -> dict:
    """Inverse of ScriptValidator.parse_script."""
    data = {
        "lesson_id": script.lesson_id,
        "title": script.title,
        "language": script.language,
        "level": script.level,
        "lines": [],
    }
    for line in script.lines:
        line_dict = {"id": line.id, "speaker": line.speaker, "text": line.text}
        if line.voice:
            line_dict["voice"] = line.voice
        line_dict["emotion"] = line.emotion
        line_dict["pause_after_ms"] = line.pause_after_ms
        line_dict["speech_rate"] = line.speech_rate
        data["lines"].append(line_dict)
    if script.settings:
        data["settings"] = {
            "speech_rate": script.settings.speech_rate,
            "initial_silence_ms": script.settings.initial_silence_ms,
            "default_pause_ms": script.settings.default_pause_ms,
        }
    return data


def save_script(script: Script, path: str | Path) -> None:
    """Write a Script to a pretty JSON file (creating parent dirs)."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(script_to_dict(script), f, indent=2, ensure_ascii=False)
```

- [ ] **Step 4: Run, expect pass.**
- [ ] **Step 5: Commit** — `feat(tui): add script_io (serialize + save Script)`

---

## Task 2: `player` — ffplay audio replay wrapper

**Files:** Create `src/tui/player.py`; Test `tests/tui/test_player.py`

- [ ] **Step 1: Failing test**

```python
"""Tests for the audio player seam."""

from src.tui.player import FakePlayer


def test_fake_player_records_play_and_stop():
    p = FakePlayer()
    p.play("output/a.mp3")
    p.play("output/b.mp3")
    p.stop()
    assert p.played == ["output/a.mp3", "output/b.mp3"]
    assert p.stop_count == 1
```

- [ ] **Step 2: Run, expect fail.**

- [ ] **Step 3: Implement**

```python
"""Audio replay seam — wraps ffplay so the TUI stays decoupled/testable."""

import shutil
import subprocess
from pathlib import Path
from typing import Optional, Protocol


class AudioPlayer(Protocol):
    def play(self, path: str) -> None: ...
    def stop(self) -> None: ...


class FfplayPlayer:
    """Plays audio via ffplay (bundled with ffmpeg). No-op if ffplay is absent."""

    def __init__(self) -> None:
        self._proc: Optional[subprocess.Popen] = None

    def available(self) -> bool:
        return shutil.which("ffplay") is not None

    def play(self, path: str) -> None:
        if not self.available() or not Path(path).exists():
            return
        self.stop()
        self._proc = subprocess.Popen(
            ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", str(path)]
        )

    def stop(self) -> None:
        if self._proc is not None and self._proc.poll() is None:
            self._proc.terminate()
        self._proc = None


class FakePlayer:
    """Test player: records calls instead of spawning a process."""

    def __init__(self) -> None:
        self.played: list[str] = []
        self.stop_count = 0

    def play(self, path: str) -> None:
        self.played.append(path)

    def stop(self) -> None:
        self.stop_count += 1
```

- [ ] **Step 4: Run, expect pass.**
- [ ] **Step 5: Commit** — `feat(tui): add ffplay audio player seam`

---

## Task 3: Add `player` to AppState and TtsApp

**Files:** Modify `src/tui/state.py`, `src/tui/app.py`

- [ ] **Step 1: Edit `state.py`** — add import and field.

```python
from .player import AudioPlayer, FfplayPlayer
```
Add to `AppState` (after `runner`):
```python
    player: AudioPlayer = field(default_factory=FfplayPlayer)
```

- [ ] **Step 2: Edit `app.py`** — accept optional player.

Add import: `from .player import AudioPlayer, FfplayPlayer`
Add param to `__init__` signature: `player: Optional[AudioPlayer] = None,`
In the `AppState(...)` construction add: `player=player or FfplayPlayer(),`

- [ ] **Step 3: Verify import** — `python -c "from src.tui.app import TtsApp; print('ok')"`
- [ ] **Step 4: Run full suite** — `python -m pytest -q` (should still pass; default player unused in tests).
- [ ] **Step 5: Commit** — `feat(tui): wire AudioPlayer into AppState and TtsApp`

---

## Task 4: Audio replay in History screen

**Files:** Modify `src/tui/screens/history.py`; Test add to `tests/tui/test_history_screen.py`

- [ ] **Step 1: Failing test** (append to existing test file)

```python
@pytest.mark.asyncio
async def test_history_play_calls_player(tmp_path):
    from src.tui.player import FakePlayer
    store = HistoryStore(tmp_path / "history.json")
    store.append(_record(_write_script(tmp_path, "a"), "a"))
    player = FakePlayer()
    app = TtsApp(
        config=Config(), config_path=tmp_path / "config.yaml",
        output_dir=tmp_path / "output", runner=FakeRunner(),
        history_store=store, player=player,
    )
    async with app.run_test() as pilot:
        await pilot.press("h")
        app.screen.query_one("#history-table").move_cursor(row=0)
        await pilot.press("p")
        await pilot.pause()
        assert player.played == ["output/x.mp3"]
```

- [ ] **Step 2: Run, expect fail** (no `p` binding / action).

- [ ] **Step 3: Implement** — in `history.py`:

Add bindings (extend BINDINGS list):
```python
        ("p", "play", "Play"),
        ("s", "stop", "Stop"),
```
Add actions and stop-on-unmount:
```python
    def action_play(self) -> None:
        rec = self._selected()
        if rec is None or not rec.audio_file:
            return
        self.app.state.player.play(rec.audio_file)
        self.query_one("#history-detail", Static).update(f"Playing {rec.audio_file} …")

    def action_stop(self) -> None:
        self.app.state.player.stop()

    def on_unmount(self) -> None:
        self.app.state.player.stop()
```

- [ ] **Step 4: Run, expect pass** — `python -m pytest tests/tui/test_history_screen.py -q`.
- [ ] **Step 5: Commit** — `feat(tui): add audio replay (ffplay) to history screen`

---

## Task 5: Editor screen + line-form modal

**Files:** Create `src/tui/screens/editor.py`; Test `tests/tui/test_editor_screen.py`

- [ ] **Step 1: Failing test**

```python
"""Tests for the Editor screen."""

import pytest

from src.models.config import Config
from src.models.script import ScriptLine
from src.services.validator import ScriptValidator
from src.tui.app import TtsApp
from src.tui.history_store import HistoryStore
from src.tui.runner import FakeRunner
from src.tui.screens.editor import EditorScreen


def _make_app(tmp_path):
    return TtsApp(
        config=Config(), config_path=tmp_path / "config.yaml",
        output_dir=tmp_path / "output", runner=FakeRunner(),
        history_store=HistoryStore(tmp_path / "history.json"),
    )


@pytest.mark.asyncio
async def test_editor_saves_valid_script(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)            # so topics/ is written under tmp_path
    app = _make_app(tmp_path)
    async with app.run_test() as pilot:
        app.push_screen(EditorScreen())
        await pilot.pause()
        screen = app.screen
        assert isinstance(screen, EditorScreen)
        # populate programmatically (modal form is exercised separately)
        screen.query_one("#lesson_id").value = "made_in_tui"
        screen.query_one("#title").value = "Made in TUI"
        screen.lines = [
            ScriptLine(id=1, speaker="female_us_1", text="Hello!"),
            ScriptLine(id=2, speaker="male_us_1", text="Hi!"),
        ]
        screen.action_save()
        await pilot.pause()

    saved = ScriptValidator.load_script(tmp_path / "topics" / "made_in_tui.json")
    assert saved.lesson_id == "made_in_tui"
    assert [l.id for l in saved.lines] == [1, 2]


def test_next_line_id_helper():
    assert EditorScreen._next_id([]) == 1
    assert EditorScreen._next_id([ScriptLine(id=1, speaker="x", text="a"),
                                  ScriptLine(id=4, speaker="y", text="b")]) == 5
```

- [ ] **Step 2: Run, expect fail.**

- [ ] **Step 3: Implement** `src/tui/screens/editor.py`

```python
"""Editor screen: author a conversation script via a per-line modal form."""

from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Vertical, VerticalScroll
from textual.screen import ModalScreen, Screen
from textual.widgets import Button, DataTable, Footer, Header, Input, Label, Select, Static

from ..script_io import save_script
from ...models.script import Script, ScriptLine, ScriptSettings
from ...services.validator import ScriptValidator, ValidationError

EMOTIONS = ["neutral", "friendly", "cheerful", "serious", "excited"]
SPEAKERS = ["female_us_1", "female_us_2", "male_us_1", "male_us_2", "female_uk_1", "male_uk_1"]


class LineFormScreen(ModalScreen[ScriptLine]):
    """Modal to add/edit a single line; dismisses with a ScriptLine or None."""

    BINDINGS = [("escape", "cancel", "Cancel")]

    def __init__(self, line: ScriptLine):
        super().__init__()
        self._line = line

    def compose(self) -> ComposeResult:
        with Vertical(id="line-form"):
            yield Label("Speaker")
            yield Select([(s, s) for s in SPEAKERS], value=self._line.speaker,
                         id="lf_speaker", allow_blank=False)
            yield Label("Text")
            yield Input(self._line.text, id="lf_text")
            yield Label("Emotion")
            yield Select([(e, e) for e in EMOTIONS], value=self._line.emotion,
                         id="lf_emotion", allow_blank=False)
            yield Label("pause_after_ms")
            yield Input(str(self._line.pause_after_ms), id="lf_pause")
            yield Label("speech_rate")
            yield Input(str(self._line.speech_rate), id="lf_rate")
            yield Button("OK", id="lf_ok", variant="primary")
            yield Static("", id="lf_err")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "lf_ok":
            self.action_ok()

    def action_ok(self) -> None:
        try:
            line = ScriptLine(
                id=self._line.id,
                speaker=str(self.query_one("#lf_speaker", Select).value),
                text=self.query_one("#lf_text", Input).value,
                emotion=str(self.query_one("#lf_emotion", Select).value),
                pause_after_ms=int(self.query_one("#lf_pause", Input).value),
                speech_rate=float(self.query_one("#lf_rate", Input).value),
            )
        except ValueError as exc:
            self.query_one("#lf_err", Static).update(f"Invalid: {exc}")
            return
        self.dismiss(line)

    def action_cancel(self) -> None:
        self.dismiss(None)


class EditorScreen(Screen):
    """Author a conversation script."""

    BINDINGS = [
        ("a", "add_line", "Add"),
        ("e", "edit_line", "Edit"),
        ("d", "delete_line", "Delete"),
        ("k", "move_up", "Up"),
        ("j", "move_down", "Down"),
        ("s", "save", "Save"),
        ("escape", "app.pop_screen", "Back"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.lines: list[ScriptLine] = []

    def compose(self) -> ComposeResult:
        yield Header()
        with VerticalScroll(id="editor-form"):
            yield Label("lesson_id")
            yield Input("", id="lesson_id")
            yield Label("title")
            yield Input("", id="title")
            yield Label("language")
            yield Input("en", id="language")
            yield Label("level")
            yield Input("B1", id="level")
            table = DataTable(id="lines-table", cursor_type="row")
            table.add_columns("#", "speaker", "text")
            yield table
            yield Static("", id="editor-msg")
        yield Footer()

    @staticmethod
    def _next_id(lines: list[ScriptLine]) -> int:
        return (max((l.id for l in lines), default=0)) + 1

    def refresh_lines(self) -> None:
        table = self.query_one("#lines-table", DataTable)
        table.clear()
        for line in self.lines:
            preview = line.text[:40] + ("…" if len(line.text) > 40 else "")
            table.add_row(str(line.id), line.speaker, preview)

    def _cursor(self) -> int | None:
        row = self.query_one("#lines-table", DataTable).cursor_row
        if row is None or not (0 <= row < len(self.lines)):
            return None
        return row

    def action_add_line(self) -> None:
        new = ScriptLine(id=self._next_id(self.lines), speaker=SPEAKERS[0], text="")

        def _on_close(line: ScriptLine | None) -> None:
            if line is not None:
                self.lines.append(line)
                self.refresh_lines()

        self.app.push_screen(LineFormScreen(new), _on_close)

    def action_edit_line(self) -> None:
        row = self._cursor()
        if row is None:
            return

        def _on_close(line: ScriptLine | None) -> None:
            if line is not None:
                self.lines[row] = line
                self.refresh_lines()

        self.app.push_screen(LineFormScreen(self.lines[row]), _on_close)

    def action_delete_line(self) -> None:
        row = self._cursor()
        if row is not None:
            del self.lines[row]
            self.refresh_lines()

    def action_move_up(self) -> None:
        row = self._cursor()
        if row and row > 0:
            self.lines[row - 1], self.lines[row] = self.lines[row], self.lines[row - 1]
            self.refresh_lines()

    def action_move_down(self) -> None:
        row = self._cursor()
        if row is not None and row < len(self.lines) - 1:
            self.lines[row + 1], self.lines[row] = self.lines[row], self.lines[row + 1]
            self.refresh_lines()

    def action_save(self) -> None:
        script = Script(
            lesson_id=self.query_one("#lesson_id", Input).value.strip(),
            title=self.query_one("#title", Input).value.strip(),
            lines=self.lines,
            language=self.query_one("#language", Input).value.strip() or "en",
            level=self.query_one("#level", Input).value.strip() or "B1",
            settings=ScriptSettings(),
        )
        try:
            ScriptValidator().validate_or_raise(script)
        except ValidationError as exc:
            self.query_one("#editor-msg", Static).update(f"Invalid: {exc}")
            return
        path = Path("topics") / f"{script.lesson_id}.json"
        save_script(script, path)
        self.query_one("#editor-msg", Static).update(f"Saved {path}")
```

- [ ] **Step 4: Run, expect pass** — `python -m pytest tests/tui/test_editor_screen.py -q`.
- [ ] **Step 5: Commit** — `feat(tui): add script editor screen with per-line modal form`

---

## Task 6: Wire Editor into Queue + final verification + docs

**Files:** Modify `src/tui/screens/queue.py`, `README.md`, handover doc

- [ ] **Step 1: Add `e` binding to QueueScreen** — in `queue.py` BINDINGS add:
```python
        ("e", "new_script", "Editor"),
```
Add action and import (`from .editor import EditorScreen` at top of file):
```python
    def action_new_script(self) -> None:
        self.app.push_screen(EditorScreen())
```

- [ ] **Step 2: Headless wiring test** (append to `tests/tui/test_queue_screen.py`)
```python
@pytest.mark.asyncio
async def test_queue_opens_editor(tmp_path):
    app = _make_app(tmp_path, FakeRunner())
    async with app.run_test() as pilot:
        await pilot.press("e")
        assert app.screen.__class__.__name__ == "EditorScreen"
```

- [ ] **Step 3: Run full suite** — `python -m pytest -q` → all pass.

- [ ] **Step 4: README** — under "Console UI", add Editor (`e`) and replay (`p`/`s`) to the screen list. Commit.

- [ ] **Step 5: Update handover** — mark v2 tasks DONE with commit SHAs; note suite count.

- [ ] **Step 6: Commit** — `feat(tui): open editor from queue; document v2 in README`

---

## Self-review notes
- **Spec coverage:** script_io (T1), player (T2), AppState/app wiring (T3), replay in history (T4),
  editor + modal (T5), queue→editor + docs (T6). Overwrite-confirm modal for existing
  `topics/<id>.json` is a nice-to-have; if skipped for v1-of-v2, note it (save silently overwrites).
- **Textual API:** verify `Select` value handling and `ModalScreen[...].dismiss(value)` against
  installed Textual 8.2.7 (used successfully in v1 config screen / add-topic modal).
- **Reorder:** mutates list order only; line `id`s remain unique (playback order = list order).
