"""Kokoro-ONNX Engine - High quality local TTS using ONNX runtime."""

import io
from typing import Optional

from .base import TTSEngine, SynthesisResult
from ..models.config import DEFAULT_KOKORO_VOICES


DEFAULT_VOICE = "af_heart"


class KokoroTTSEngine(TTSEngine):
    """Kokoro-ONNX TTS - high quality, fast local inference."""

    def __init__(
        self,
        model_path: str = "./models/kokoro-v1.0.fp16.onnx",
        voices_path: str = "./models/voices-v1.0.bin",
        custom_voices: Optional[dict[str, str]] = None,
    ):
        """
        Initialize Kokoro-ONNX engine.

        Args:
            model_path: Path to kokoro-v1.0.onnx model file
            voices_path: Path to voices-v1.0.bin file
            custom_voices: Optional custom speaker->voice mapping
        """
        self.model_path = model_path
        self.voices_path = voices_path
        self.voices = {**DEFAULT_KOKORO_VOICES, **(custom_voices or {})}
        self.default_voice = DEFAULT_VOICE
        self.kokoro = None

    def initialize(self) -> None:
        """Load Kokoro ONNX model."""
        try:
            from kokoro_onnx import Kokoro
            self.kokoro = Kokoro(self.model_path, self.voices_path)
        except ImportError:
            raise ImportError(
                "kokoro-onnx is not installed. Install it with: pip install kokoro-onnx"
            )
        except Exception as e:
            raise RuntimeError(f"Failed to load Kokoro model: {e}")

    def get_voice(self, speaker: str) -> str:
        """
        Get Kokoro voice for speaker ID.

        Args:
            speaker: Speaker ID (e.g., "female_us_1")

        Returns:
            Kokoro voice name (e.g., "af_heart")
        """
        # If it looks like a direct Kokoro voice name, use it as-is
        if speaker.startswith(("af_", "am_", "bf_", "bm_")):
            return speaker
        # Otherwise, look up in the mapping
        return self.voices.get(speaker, self.default_voice)

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
            voice: Speaker ID (e.g., "female_us_1") or Kokoro voice name
            emotion: Emotion hint (not used by Kokoro)
            speed: Speech rate multiplier (1.0 = normal)

        Returns:
            SynthesisResult with WAV audio bytes
        """
        if self.kokoro is None:
            self.initialize()

        try:
            import soundfile as sf

            # Map speaker to Kokoro voice
            kokoro_voice = self.get_voice(voice)

            # Generate audio
            samples, sample_rate = self.kokoro.create(
                text,
                voice=kokoro_voice,
                speed=speed,
                lang="en-us"
            )

            # Convert to WAV bytes
            buffer = io.BytesIO()
            sf.write(buffer, samples, sample_rate, format="WAV")
            audio_bytes = buffer.getvalue()

            # Calculate duration
            duration_ms = int(len(samples) / sample_rate * 1000)

            return SynthesisResult(
                line_id=0,
                success=True,
                audio_bytes=audio_bytes,
                duration_ms=duration_ms,
                sample_rate=sample_rate,
            )

        except ImportError:
            return SynthesisResult(
                line_id=0,
                success=False,
                audio_bytes=None,
                duration_ms=0,
                sample_rate=24000,
                error="soundfile is not installed. Install it with: pip install soundfile",
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
        """Release model resources."""
        self.kokoro = None


if __name__ == "__main__":
    # Quick test
    engine = KokoroTTSEngine(
        model_path="models/kokoro-v1.0.onnx",
        voices_path="models/voices-v1.0.bin"
    )
    engine.initialize()

    result = engine.synthesize(
        text="Hello, this is a test of Kokoro ONNX TTS.",
        voice="female_us_1",
        speed=1.0
    )

    if result.success:
        with open("test_kokoro.wav", "wb") as f:
            f.write(result.audio_bytes)
        print(f"Generated audio: {result.duration_ms}ms")
    else:
        print(f"Error: {result.error}")
