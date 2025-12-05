"""Data models for script input and lesson output."""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class Emotion(str, Enum):
    """Supported emotion types for TTS synthesis."""
    NEUTRAL = "neutral"
    FRIENDLY = "friendly"
    CHEERFUL = "cheerful"
    SERIOUS = "serious"
    EXCITED = "excited"


class ScriptLine(BaseModel):
    """Single line of dialogue in a script."""
    id: int = Field(..., description="Unique line identifier")
    speaker: str = Field(..., description="Voice ID from registry")
    text: str = Field(..., min_length=1, description="Text to synthesize")
    emotion: Emotion = Field(default=Emotion.NEUTRAL, description="Emotion for synthesis")
    pause_after_ms: int = Field(default=400, ge=0, le=5000, description="Pause after line in ms")
    speech_rate: Optional[float] = Field(default=None, ge=0.5, le=1.5, description="Override speech rate")


class ScriptSettings(BaseModel):
    """Global settings for script synthesis."""
    speech_rate: float = Field(default=1.0, ge=0.5, le=1.5, description="Default speech rate")
    initial_silence_ms: int = Field(default=300, ge=0, le=2000, description="Silence at start")
    default_pause_ms: int = Field(default=400, ge=0, le=5000, description="Default pause between lines")


class ScriptInput(BaseModel):
    """Complete script input for lesson generation."""
    lesson_id: str = Field(..., min_length=1, description="Unique lesson identifier")
    title: str = Field(..., min_length=1, description="Lesson title")
    level: str = Field(default="B2", description="Language level")
    lines: list[ScriptLine] = Field(..., min_length=1, description="Dialogue lines")
    settings: ScriptSettings = Field(default_factory=ScriptSettings)


class Segment(BaseModel):
    """Audio segment with timing information."""
    id: int = Field(..., description="Line ID from script")
    speaker: str = Field(..., description="Speaker voice ID")
    text: str = Field(..., description="Original text")
    start_ms: int = Field(..., ge=0, description="Start time in milliseconds")
    end_ms: int = Field(..., description="End time in milliseconds")
    audio_duration_ms: int = Field(..., ge=0, description="Actual audio duration")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Alignment confidence")


class LessonMetadata(BaseModel):
    """Metadata for generated lesson."""
    model_version: str = Field(..., description="TTS model version used")
    generated_at: str = Field(..., description="ISO timestamp of generation")
    quality_score: float = Field(default=1.0, ge=0.0, le=1.0, description="Overall quality score")


class LessonOutput(BaseModel):
    """Complete output from lesson generation."""
    lesson_id: str
    title: str
    audio_file: str = Field(..., description="Path to generated audio file")
    srt_file: str = Field(..., description="Path to generated SRT file")
    duration_ms: int = Field(..., ge=0, description="Total audio duration")
    segments: list[Segment] = Field(default_factory=list)
    metadata: LessonMetadata
