"""Shared application state held by TtsApp and read/written by screens."""

from dataclasses import dataclass, field
from pathlib import Path

from ..models.config import Config
from .history_store import HistoryStore
from .models import QueueItem
from .runner import GenerationRunner, PipelineRunner


@dataclass
class AppState:
    """Live state shared across screens."""

    config: Config
    config_path: Path
    output_dir: Path
    history: HistoryStore
    runner: GenerationRunner = field(default_factory=PipelineRunner)
    queue: list[QueueItem] = field(default_factory=list)
