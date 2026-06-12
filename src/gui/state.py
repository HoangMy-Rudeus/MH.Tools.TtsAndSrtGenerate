"""Shared application state for the GUI."""

from dataclasses import dataclass, field
from pathlib import Path

from ..models.config import Config
from ..tui.history_store import HistoryStore
from ..tui.models import QueueItem
from ..tui.player import AudioPlayer, FfplayPlayer
from ..tui.runner import GenerationRunner, PipelineRunner


@dataclass
class AppState:
    """Live state shared across all panels."""

    config: Config
    config_path: Path
    output_dir: Path
    history: HistoryStore
    runner: GenerationRunner = field(default_factory=PipelineRunner)
    player: AudioPlayer = field(default_factory=FfplayPlayer)
    queue: list[QueueItem] = field(default_factory=list)
