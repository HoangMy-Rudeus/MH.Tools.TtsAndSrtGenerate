"""Top-level Textual application."""

import shutil
from pathlib import Path
from typing import Optional

from textual.app import App

from ..models.config import Config
from .history_store import HistoryStore
from .player import AudioPlayer, FfplayPlayer
from .runner import GenerationRunner, PipelineRunner
from .screens.config import ConfigScreen
from .screens.history import HistoryScreen
from .screens.queue import QueueScreen
from .state import AppState


class TtsApp(App):
    """TTS & SRT generator console UI."""

    TITLE = "TTS & SRT Generator"

    BINDINGS = [
        ("c", "open_config", "Config"),
        ("h", "open_history", "History"),
        ("q", "quit", "Quit"),
    ]

    def __init__(
        self,
        config: Config,
        config_path: str | Path,
        output_dir: str | Path,
        runner: Optional[GenerationRunner] = None,
        history_store: Optional[HistoryStore] = None,
        player: Optional[AudioPlayer] = None,
    ):
        super().__init__()
        output_dir = Path(output_dir)
        self.state = AppState(
            config=config,
            config_path=Path(config_path),
            output_dir=output_dir,
            history=history_store or HistoryStore(output_dir / "history.json"),
            runner=runner or PipelineRunner(),
            player=player or FfplayPlayer(),
        )

    def on_mount(self) -> None:
        if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
            self.notify(
                "ffmpeg/ffprobe not found on PATH — audio stitching will fail. "
                "Install ffmpeg and restart.",
                title="Missing dependency",
                severity="warning",
                timeout=10,
            )
        self.push_screen(QueueScreen())

    def action_open_config(self) -> None:
        self.push_screen(ConfigScreen())

    def action_open_history(self) -> None:
        self.push_screen(HistoryScreen())
