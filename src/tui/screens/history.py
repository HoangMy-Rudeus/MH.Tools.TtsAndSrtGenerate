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
            f"Re-queued {rec.lesson_id}. Go to Queue (esc) and press 'r' to run."
        )
