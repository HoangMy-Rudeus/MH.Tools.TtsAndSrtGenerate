"""Edge TTS Engine - Microsoft's free cloud TTS service."""

import asyncio
import io
from typing import Optional

import edge_tts

from .base import TTSEngine, SynthesisResult
from ..models.config import DEFAULT_EDGE_VOICES


DEFAULT_VOICE = "en-US-AriaNeural"


class EdgeTTSEngine(TTSEngine):
    """Microsoft Edge TTS - free, fast, cloud-based."""

    def __init__(self, custom_voices: Optional[dict[str, str]] = None):
        """
        Initialize Edge TTS engine.

        Args:
            custom_voices: Optional custom speaker->voice mapping
        """
        self.voices = {**DEFAULT_EDGE_VOICES, **(custom_voices or {})}
        self.default_voice = DEFAULT_VOICE

    def initialize(self) -> None:
        """No initialization needed for Edge TTS."""
        pass

    def get_voice(self, speaker: str) -> str:
        """
        Get Edge TTS voice for speaker ID.

        Args:
            speaker: Speaker ID or direct Edge voice name

        Returns:
            Edge TTS voice name (e.g., "en-US-AriaNeural")
        """
        # If it looks like a direct Edge voice name, use it as-is
        if "-" in speaker and "Neural" in speaker:
            return speaker
        # Otherwise, look up in the mapping
        return self.voices.get(speaker, self.default_voice)

    async def _synthesize_async(
        self,
        text: str,
        voice: str,
        rate: str = "+0%",
    ) -> bytes:
        """
        Async synthesis using Edge TTS.

        Args:
            text: Text to synthesize
            voice: Edge TTS voice name
            rate: Speech rate string (e.g., "+10%" or "-10%")

        Returns:
            MP3 audio bytes
        """
        communicate = edge_tts.Communicate(text, voice, rate=rate)

        audio_data = io.BytesIO()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data.write(chunk["data"])

        return audio_data.getvalue()

    def synthesize(
        self,
        text: str,
        voice: str,
        emotion: str = "neutral",
        speed: float = 1.0,
    ) -> SynthesisResult:
        """
        Synthesize text to audio.

        Args:
            text: Text to synthesize
            voice: Speaker ID (e.g., "female_us_1") or Edge voice name
            emotion: Emotion hint (not fully supported by Edge)
            speed: Speech rate multiplier (1.0 = normal)

        Returns:
            SynthesisResult with MP3 audio bytes
        """
        try:
            # Map speaker to Edge voice
            edge_voice = self.get_voice(voice)

            # Calculate rate string (+10% or -10%)
            rate_percent = int((speed - 1.0) * 100)
            rate = f"+{rate_percent}%" if rate_percent >= 0 else f"{rate_percent}%"

            # Run async synthesis
            # Create a new event loop if we're not in an async context
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None

            if loop and loop.is_running():
                # We're in an async context, use run_coroutine_threadsafe
                import concurrent.futures
                future = asyncio.run_coroutine_threadsafe(
                    self._synthesize_async(text, edge_voice, rate),
                    loop
                )
                audio_bytes = future.result()
            else:
                # We're not in an async context, use asyncio.run
                audio_bytes = asyncio.run(
                    self._synthesize_async(text, edge_voice, rate)
                )

            # Estimate duration (rough: ~16KB/sec for MP3 at 128kbps)
            duration_ms = int(len(audio_bytes) / 16 * 1000 / 1024)

            return SynthesisResult(
                line_id=0,
                success=True,
                audio_bytes=audio_bytes,
                duration_ms=duration_ms,
                sample_rate=24000,
            )

        except Exception as e:
            return SynthesisResult(
                line_id=0,
                success=False,
                audio_bytes=None,
                duration_ms=0,
                sample_rate=24000,
                error=str(e),
            )

    def get_available_voices(self) -> list[str]:
        """List available speaker IDs."""
        return list(self.voices.keys())

    def cleanup(self) -> None:
        """No cleanup needed for Edge TTS."""
        pass


async def list_all_edge_voices(language: str = "en") -> list[dict]:
    """
    List all available Edge TTS voices for a language.

    Args:
        language: Language code prefix (e.g., "en" for English)

    Returns:
        List of voice dictionaries with metadata
    """
    voices = await edge_tts.list_voices()
    return [v for v in voices if v["Locale"].startswith(language)]


# Synchronous wrapper for listing voices
def list_voices_sync(language: str = "en") -> list[dict]:
    """Synchronous wrapper for listing Edge TTS voices."""
    return asyncio.run(list_all_edge_voices(language))


if __name__ == "__main__":
    # Quick test
    engine = EdgeTTSEngine()

    result = engine.synthesize(
        text="Hello, this is a test of Edge TTS.",
        voice="female_us_1",
        speed=1.0
    )

    if result.success:
        with open("test_edge.mp3", "wb") as f:
            f.write(result.audio_bytes)
        print(f"Generated audio: {result.duration_ms}ms")
    else:
        print(f"Error: {result.error}")
