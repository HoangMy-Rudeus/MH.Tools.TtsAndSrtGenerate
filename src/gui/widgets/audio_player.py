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
