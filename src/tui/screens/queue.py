"""Queue screen (home): add topics, run them, show live progress."""

from datetime import datetime
from pathlib import Path

from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.message import Message
from textual.screen import ModalScreen, Screen
from textual.widgets import (
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
        Binding("r", "run_all", "Run all"),
        # enter also runs, but the focused DataTable claims plain Enter, so use priority
        Binding("enter", "run_all", "Run", show=False, priority=True),
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
