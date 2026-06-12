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
