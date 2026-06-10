"""Script, segment, and timeline data models."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ScriptLine:
    """A single line of dialogue in a conversation script."""

    id: int
    speaker: str
    text: str
    voice: Optional[str] = None
    emotion: str = "neutral"
    pause_after_ms: int = 400
    speech_rate: float = 1.0


@dataclass
class ScriptSettings:
    """Global generation settings for a script."""

    speech_rate: float = 1.0
    initial_silence_ms: int = 300
    default_pause_ms: int = 400


@dataclass
class Script:
    """A conversation script to be synthesized."""

    lesson_id: str
    title: str
    lines: list[ScriptLine] = field(default_factory=list)
    language: str = "en"
    level: str = "B1"
    settings: Optional[ScriptSettings] = None


@dataclass
class Segment:
    """A synthesized segment with absolute timing information."""

    id: int
    speaker: str
    text: str
    start_ms: int
    end_ms: int
    audio_duration_ms: int


@dataclass
class Metadata:
    """Metadata about a generation run."""

    engine: str
    generated_at: str


@dataclass
class TimelineOutput:
    """Full timeline output describing a generated lesson."""

    lesson_id: str
    title: str
    audio_file: str
    srt_file: str
    duration_ms: int
    segments: list[Segment]
    metadata: Metadata
