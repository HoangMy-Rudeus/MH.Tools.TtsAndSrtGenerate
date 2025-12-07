"""Edge TTS worker for fast cloud-based synthesis."""

import asyncio
import io
import logging
from typing import Optional

import edge_tts
import numpy as np
from pydantic import BaseModel

from src.models.script import ScriptLine, Emotion
from src.models.config import TTSConfig, SynthesisConfig

logger = logging.getLogger(__name__)


class SynthesisResult(BaseModel):
    """Result of TTS synthesis for a single line."""
    line_id: int
    success: bool
    audio_bytes: Optional[bytes] = None
    duration_ms: int = 0
    sample_rate: int = 24000
    error: Optional[str] = None

    class Config:
        arbitrary_types_allowed = True


# Edge TTS voice mapping for different speaker types
EDGE_VOICES = {
    # US English voices
    "male_us_1": "en-US-GuyNeural",
    "male_us_2": "en-US-ChristopherNeural",
    "female_us_1": "en-US-AriaNeural",
    "female_us_2": "en-US-JennyNeural",
    # UK English voices
    "male_uk_1": "en-GB-RyanNeural",
    "female_uk_1": "en-GB-SoniaNeural",
    # Default
    "default": "en-US-AriaNeural",
}

# Emotion to Edge TTS style mapping
EMOTION_STYLES = {
    Emotion.NEUTRAL: {},
    Emotion.FRIENDLY: {"style": "friendly"},
    Emotion.CHEERFUL: {"style": "cheerful"},
    Emotion.SERIOUS: {"style": "serious"},
    Emotion.EXCITED: {"style": "excited"},
}


class EdgeTTSWorker:
    """Synthesizes audio using Microsoft Edge TTS (free, fast, cloud-based)."""

    def __init__(
        self,
        tts_config: TTSConfig,
        synthesis_config: SynthesisConfig,
        voice_registry: dict = None,
    ):
        """
        Initialize Edge TTS worker.

        Args:
            tts_config: TTS engine configuration
            synthesis_config: Synthesis parameters
            voice_registry: Optional voice registry (used for voice ID mapping)
        """
        self.tts_config = tts_config
        self.synthesis_config = synthesis_config
        self.voice_registry = voice_registry or {}
        self._loaded = False

    def load_model(self) -> None:
        """No model loading needed for Edge TTS."""
        self._loaded = True
        logger.info("Edge TTS ready (cloud-based, no local model)")

    def _get_voice(self, speaker: str) -> str:
        """Get Edge TTS voice name for speaker."""
        # Check config voice mapping first
        if speaker in self.tts_config.edge_voices:
            return self.tts_config.edge_voices[speaker]
        # Check built-in voice mapping
        if speaker in EDGE_VOICES:
            return EDGE_VOICES[speaker]
        # Use config default
        return self.tts_config.edge_voice

    async def _synthesize_async(self, text: str, voice: str, rate: str = "+0%") -> bytes:
        """Async synthesis using Edge TTS."""
        communicate = edge_tts.Communicate(text, voice, rate=rate)

        audio_data = io.BytesIO()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data.write(chunk["data"])

        return audio_data.getvalue()

    def synthesize_line(self, line: ScriptLine) -> SynthesisResult:
        """
        Synthesize a single script line.

        Args:
            line: Script line to synthesize

        Returns:
            SynthesisResult with audio bytes and duration
        """
        if not self._loaded:
            self.load_model()

        try:
            # Get voice for speaker
            voice = self._get_voice(line.speaker)

            # Calculate rate adjustment
            speed = line.speech_rate or 1.0
            rate_percent = int((speed - 1.0) * 100)
            rate = f"+{rate_percent}%" if rate_percent >= 0 else f"{rate_percent}%"

            # Run async synthesis
            audio_bytes = asyncio.run(self._synthesize_async(line.text, voice, rate))

            # Estimate duration from MP3 size (rough estimate: ~16KB/sec at 128kbps)
            duration_ms = int(len(audio_bytes) / 16 * 1000 / 1024)

            logger.debug(f"Synthesized line {line.id}: ~{duration_ms}ms (Edge TTS)")

            return SynthesisResult(
                line_id=line.id,
                success=True,
                audio_bytes=audio_bytes,
                duration_ms=duration_ms,
                sample_rate=24000,  # Edge TTS outputs 24kHz
            )

        except Exception as e:
            logger.error(f"Edge TTS synthesis failed for line {line.id}: {e}")
            return SynthesisResult(
                line_id=line.id,
                success=False,
                error=str(e)
            )

    def synthesize_batch(self, lines: list[ScriptLine]) -> list[SynthesisResult]:
        """
        Synthesize multiple lines.

        Args:
            lines: List of script lines

        Returns:
            List of SynthesisResult in same order
        """
        results = []
        for line in lines:
            result = self.synthesize_line(line)
            results.append(result)
        return results

    def unload_model(self) -> None:
        """No cleanup needed for Edge TTS."""
        self._loaded = False
        logger.info("Edge TTS worker stopped")


async def list_voices(language: str = "en") -> list[dict]:
    """List available Edge TTS voices for a language."""
    voices = await edge_tts.list_voices()
    return [v for v in voices if v["Locale"].startswith(language)]
