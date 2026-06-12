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
