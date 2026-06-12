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
            row.bind("<Button-1>", lambda e, n=i: self._select(n))
            for child in row.winfo_children():
                child.bind("<Button-1>", lambda e, n=i: self._select(n))

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
