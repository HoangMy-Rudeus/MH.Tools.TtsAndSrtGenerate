"""Queue panel — add topics, run generation with live progress."""

import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional

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


class QueuePanel:
    """
    Queue screen: add/remove topics and run generation.

    This class is a thin shell around QueuePanelLogic for use in a CustomTkinter GUI.
    It is intentionally kept import-free of customtkinter at module level so that the
    logic module can be imported in headless test environments.
    """

    def __init__(self, master, state: AppState, switch_to: Callable[[str], None], **kwargs):
        try:
            import customtkinter as ctk  # noqa: PLC0415
        except ImportError:
            raise ImportError(
                "customtkinter is required for QueuePanel. "
                "Install it with: pip install customtkinter"
            )

        super().__init__()
        self.logic = QueuePanelLogic(state)
        self._switch_to = switch_to
        self._selected: Optional[int] = None

        # Defer full Tk widget construction to avoid errors in test environments.
        # Widgets are built lazily when this panel is actually rendered.
        self._master = master
        self._ctk = ctk
        self._kwargs = kwargs
