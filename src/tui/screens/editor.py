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
            speaker = self._line.speaker if self._line.speaker in SPEAKERS else SPEAKERS[0]
            yield Select([(s, s) for s in SPEAKERS], value=speaker,
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
