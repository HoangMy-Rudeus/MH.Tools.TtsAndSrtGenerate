"""TTS synthesis worker using Coqui XTTS v2."""

import io
import logging
from pathlib import Path
from typing import Optional

import numpy as np
import torch
from pydantic import BaseModel, Field

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


class VoiceReference(BaseModel):
    """Voice reference configuration."""
    voice_id: str
    reference_path: Path
    description: str = ""

    class Config:
        arbitrary_types_allowed = True


class TTSWorker:
    """Synthesizes audio using Coqui XTTS v2."""

    # Emotion to speech style mapping
    EMOTION_STYLES = {
        Emotion.NEUTRAL: {"speed": 1.0},
        Emotion.FRIENDLY: {"speed": 1.0},
        Emotion.CHEERFUL: {"speed": 1.05},
        Emotion.SERIOUS: {"speed": 0.95},
        Emotion.EXCITED: {"speed": 1.1},
    }

    def __init__(
        self,
        tts_config: TTSConfig,
        synthesis_config: SynthesisConfig,
        voice_registry: dict[str, VoiceReference],
    ):
        """
        Initialize TTS worker.

        Args:
            tts_config: TTS engine configuration
            synthesis_config: Synthesis parameters
            voice_registry: Dict mapping voice IDs to VoiceReference
        """
        self.tts_config = tts_config
        self.synthesis_config = synthesis_config
        self.voice_registry = voice_registry
        self.model = None
        self._loaded = False

    def load_model(self) -> None:
        """Load XTTS model into memory."""
        if self._loaded:
            return

        try:
            from TTS.api import TTS

            logger.info(f"Loading TTS model: {self.tts_config.model}")

            # Use XTTS v2 multilingual model
            self.model = TTS("tts_models/multilingual/multi-dataset/xtts_v2")

            # Move to specified device
            if self.tts_config.device == "cuda" and torch.cuda.is_available():
                self.model = self.model.to("cuda")
                logger.info("Model loaded on CUDA")
            else:
                logger.info("Model loaded on CPU")

            self._loaded = True

        except Exception as e:
            logger.error(f"Failed to load TTS model: {e}")
            raise RuntimeError(f"Failed to load TTS model: {e}")

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

        # Get voice reference
        voice = self.voice_registry.get(line.speaker)
        if not voice:
            return SynthesisResult(
                line_id=line.id,
                success=False,
                error=f"Voice not found: {line.speaker}"
            )

        # Check reference file exists
        if not voice.reference_path.exists():
            return SynthesisResult(
                line_id=line.id,
                success=False,
                error=f"Voice reference not found: {voice.reference_path}"
            )

        try:
            # Get emotion style adjustments
            style = self.EMOTION_STYLES.get(line.emotion, {})
            speed = line.speech_rate or style.get("speed", 1.0)

            # Synthesize with XTTS
            wav = self.model.tts(
                text=line.text,
                speaker_wav=str(voice.reference_path),
                language="en",
                speed=speed,
            )

            # Convert to numpy array if needed
            if isinstance(wav, list):
                wav = np.array(wav)

            # Convert to bytes (16-bit PCM WAV)
            audio_bytes = self._numpy_to_wav_bytes(wav, self.model.synthesizer.output_sample_rate)

            # Calculate duration
            duration_ms = int(len(wav) / self.model.synthesizer.output_sample_rate * 1000)

            logger.debug(f"Synthesized line {line.id}: {duration_ms}ms")

            return SynthesisResult(
                line_id=line.id,
                success=True,
                audio_bytes=audio_bytes,
                duration_ms=duration_ms,
                sample_rate=self.model.synthesizer.output_sample_rate,
            )

        except Exception as e:
            logger.error(f"Synthesis failed for line {line.id}: {e}")
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

    def _numpy_to_wav_bytes(self, audio: np.ndarray, sample_rate: int) -> bytes:
        """Convert numpy audio array to WAV bytes."""
        import wave
        import struct

        # Normalize to 16-bit range
        audio = np.clip(audio, -1.0, 1.0)
        audio_int16 = (audio * 32767).astype(np.int16)

        # Write to bytes buffer
        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_int16.tobytes())

        return buffer.getvalue()

    def unload_model(self) -> None:
        """Unload model from memory."""
        if self.model is not None:
            del self.model
            self.model = None
            self._loaded = False
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            logger.info("Model unloaded")


def load_voice_registry(voices_dir: str | Path) -> dict[str, VoiceReference]:
    """
    Load voice registry from directory.

    Expects directory structure:
    voices/
      male_us_1.wav
      female_us_1.wav

    Args:
        voices_dir: Path to voices directory

    Returns:
        Dict mapping voice_id to VoiceReference
    """
    voices_path = Path(voices_dir)
    registry = {}

    if not voices_path.exists():
        logger.warning(f"Voices directory not found: {voices_path}")
        return registry

    for wav_file in voices_path.glob("*.wav"):
        voice_id = wav_file.stem
        registry[voice_id] = VoiceReference(
            voice_id=voice_id,
            reference_path=wav_file,
            description=f"Voice from {wav_file.name}"
        )
        logger.info(f"Registered voice: {voice_id}")

    return registry
