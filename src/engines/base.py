"""Abstract base class for TTS engines."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class SynthesisResult:
    """Result from synthesizing text to speech."""

    line_id: int
    success: bool
    audio_bytes: Optional[bytes]  # WAV or MP3 bytes
    duration_ms: int
    sample_rate: int
    error: Optional[str] = None


class TTSEngine(ABC):
    """Abstract base class for TTS engines."""

    @abstractmethod
    def initialize(self) -> None:
        """Load model/connect to service."""
        pass

    @abstractmethod
    def synthesize(
        self,
        text: str,
        voice: str,
        emotion: str = "neutral",
        speed: float = 1.0,
    ) -> SynthesisResult:
        """
        Synthesize single text to audio.

        Args:
            text: Text to synthesize
            voice: Speaker ID (e.g., "female_us_1") or engine-specific voice name
            emotion: Emotion hint (neutral, friendly, cheerful, serious, excited)
            speed: Speech rate multiplier (1.0 = normal)

        Returns:
            SynthesisResult with audio bytes and metadata
        """
        pass

    @abstractmethod
    def get_available_voices(self) -> list[str]:
        """List available voice IDs."""
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """Release resources."""
        pass

    def get_voice(self, speaker: str) -> str:
        """
        Get engine-specific voice name for speaker ID.

        Override in subclasses to provide voice mapping.

        Args:
            speaker: Abstract speaker ID (e.g., "female_us_1")

        Returns:
            Engine-specific voice name
        """
        return speaker
