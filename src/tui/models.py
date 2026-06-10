"""UI-side queue state models."""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional

from ..services.validator import ScriptValidator


class QueueStatus(str, Enum):
    """Lifecycle status of a queued topic."""

    QUEUED = "queued"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


@dataclass
class QueueItem:
    """A topic waiting to be (or being) generated."""

    script_path: str
    title: str
    lesson_id: str
    status: QueueStatus = QueueStatus.QUEUED
    progress: float = 0.0
    duration_ms: int = 0
    error: Optional[str] = None


def build_queue_item(script_path: str | Path) -> QueueItem:
    """
    Load + validate a script file and build a QueueItem.

    Raises ValidationError if the script is invalid (engine-independent checks:
    structure, duplicate IDs, emotion, speech_rate, etc.).
    """
    validator = ScriptValidator()  # no engine -> voice-name checks are skipped
    script = validator.load_script(script_path)
    validator.validate_or_raise(script)
    return QueueItem(
        script_path=str(script_path),
        title=script.title,
        lesson_id=script.lesson_id,
    )
