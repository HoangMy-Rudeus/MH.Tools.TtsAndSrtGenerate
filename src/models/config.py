"""Configuration models for the application."""

from pathlib import Path
from typing import Literal, Optional
from pydantic import BaseModel, Field
import yaml


class TTSConfig(BaseModel):
    """TTS engine configuration."""
    model: str = Field(default="xtts_v2", description="Model name")
    model_path: str = Field(default="./models/xtts_v2", description="Path to model")
    device: Literal["cuda", "cpu"] = Field(default="cuda", description="Compute device")


class AudioConfig(BaseModel):
    """Audio output configuration."""
    sample_rate: int = Field(default=24000, description="Sample rate in Hz")
    output_format: Literal["mp3", "wav"] = Field(default="mp3", description="Output format")
    mp3_bitrate: int = Field(default=192, description="MP3 bitrate in kbps")
    normalization_target: int = Field(default=-16, description="Target LUFS")


class SynthesisConfig(BaseModel):
    """Synthesis parameters."""
    temperature: float = Field(default=0.7, ge=0.1, le=1.0)
    repetition_penalty: float = Field(default=2.0, ge=1.0, le=5.0)
    default_pause_ms: int = Field(default=400, ge=0, le=5000)
    initial_silence_ms: int = Field(default=300, ge=0, le=2000)


class AlignmentConfig(BaseModel):
    """Forced alignment configuration."""
    enabled: bool = Field(default=True)
    drift_threshold_ms: int = Field(default=200, ge=50, le=500)
    wer_threshold: float = Field(default=0.10, ge=0.0, le=1.0)


class VoiceCheckConfig(BaseModel):
    """Voice consistency check configuration."""
    enabled: bool = Field(default=True)
    similarity_threshold: float = Field(default=0.85, ge=0.0, le=1.0)


class RetryConfig(BaseModel):
    """Retry strategy configuration."""
    max_attempts: int = Field(default=3, ge=1, le=10)
    fallback_model: str = Field(default="vits")


class VoicesConfig(BaseModel):
    """Voice registry configuration."""
    directory: str = Field(default="./voices")


class AppConfig(BaseModel):
    """Complete application configuration."""
    tts: TTSConfig = Field(default_factory=TTSConfig)
    audio: AudioConfig = Field(default_factory=AudioConfig)
    synthesis: SynthesisConfig = Field(default_factory=SynthesisConfig)
    alignment: AlignmentConfig = Field(default_factory=AlignmentConfig)
    voice_check: VoiceCheckConfig = Field(default_factory=VoiceCheckConfig)
    retry: RetryConfig = Field(default_factory=RetryConfig)
    voices: VoicesConfig = Field(default_factory=VoicesConfig)

    @classmethod
    def from_yaml(cls, path: str | Path) -> "AppConfig":
        """Load configuration from YAML file."""
        with open(path) as f:
            data = yaml.safe_load(f)
        return cls(**data)

    @classmethod
    def default(cls) -> "AppConfig":
        """Create default configuration."""
        return cls()
