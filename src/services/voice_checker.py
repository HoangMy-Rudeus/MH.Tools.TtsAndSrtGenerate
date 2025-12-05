"""Voice consistency checking service."""

import logging
from pathlib import Path
from typing import Optional

import numpy as np
from pydantic import BaseModel, Field

from src.models.config import VoiceCheckConfig

logger = logging.getLogger(__name__)


class ConsistencyResult(BaseModel):
    """Result of voice consistency check."""
    voice_id: str
    similarity_score: float = Field(ge=0.0, le=1.0)
    passed: bool
    error: Optional[str] = None


class VoiceConsistencyChecker:
    """Ensures synthesized audio matches reference voice characteristics."""

    REFERENCE_PHRASE = "The quick brown fox jumps over the lazy dog."

    def __init__(self, config: VoiceCheckConfig):
        """
        Initialize voice checker.

        Args:
            config: Voice check configuration
        """
        self.config = config
        self._encoder = None

    def _load_encoder(self):
        """Load speaker encoder lazily."""
        if self._encoder is None:
            try:
                from resemblyzer import VoiceEncoder
                logger.info("Loading voice encoder...")
                self._encoder = VoiceEncoder()
                logger.info("Voice encoder loaded")
            except ImportError:
                logger.warning("resemblyzer not installed, voice checking disabled")

    def check_consistency(
        self,
        generated_audio: np.ndarray | bytes,
        reference_path: str | Path,
        sample_rate: int = 24000,
    ) -> ConsistencyResult:
        """
        Compare generated audio to reference voice.

        Args:
            generated_audio: Generated audio as numpy array or WAV bytes
            reference_path: Path to reference voice audio
            sample_rate: Sample rate of generated audio

        Returns:
            ConsistencyResult with similarity score
        """
        if not self.config.enabled:
            return ConsistencyResult(
                voice_id=Path(reference_path).stem,
                similarity_score=1.0,
                passed=True,
            )

        self._load_encoder()

        if self._encoder is None:
            return ConsistencyResult(
                voice_id=Path(reference_path).stem,
                similarity_score=1.0,
                passed=True,
                error="Voice encoder not available",
            )

        try:
            from resemblyzer import preprocess_wav

            # Load reference audio
            reference_wav = preprocess_wav(Path(reference_path))
            reference_embed = self._encoder.embed_utterance(reference_wav)

            # Process generated audio
            if isinstance(generated_audio, bytes):
                generated_wav = self._bytes_to_numpy(generated_audio)
            else:
                generated_wav = generated_audio

            # Preprocess if needed
            if sample_rate != 16000:
                import librosa
                generated_wav = librosa.resample(
                    generated_wav,
                    orig_sr=sample_rate,
                    target_sr=16000,
                )

            generated_embed = self._encoder.embed_utterance(generated_wav)

            # Calculate cosine similarity
            similarity = np.dot(reference_embed, generated_embed)
            similarity = float(np.clip(similarity, 0.0, 1.0))

            passed = similarity >= self.config.similarity_threshold

            return ConsistencyResult(
                voice_id=Path(reference_path).stem,
                similarity_score=similarity,
                passed=passed,
            )

        except Exception as e:
            logger.error(f"Voice consistency check failed: {e}")
            return ConsistencyResult(
                voice_id=Path(reference_path).stem,
                similarity_score=0.0,
                passed=False,
                error=str(e),
            )

    def _bytes_to_numpy(self, wav_bytes: bytes) -> np.ndarray:
        """Convert WAV bytes to numpy array."""
        import io
        import wave

        with wave.open(io.BytesIO(wav_bytes), "rb") as wav_file:
            frames = wav_file.readframes(wav_file.getnframes())
            audio = np.frombuffer(frames, dtype=np.int16)
            audio = audio.astype(np.float32) / 32768.0

        return audio

    def validate_voice_samples(
        self,
        voice_registry: dict,
        tts_worker,
    ) -> dict[str, ConsistencyResult]:
        """
        Validate all voice samples before batch processing.

        Synthesizes a reference phrase with each voice and compares
        to stored baseline to detect model drift.

        Args:
            voice_registry: Dict of voice_id -> VoiceReference
            tts_worker: TTS worker for synthesis

        Returns:
            Dict of voice_id -> ConsistencyResult
        """
        from src.models.script import ScriptLine, Emotion

        results = {}

        for voice_id, voice_ref in voice_registry.items():
            logger.info(f"Validating voice: {voice_id}")

            # Synthesize reference phrase
            line = ScriptLine(
                id=0,
                speaker=voice_id,
                text=self.REFERENCE_PHRASE,
                emotion=Emotion.NEUTRAL,
            )

            synthesis_result = tts_worker.synthesize_line(line)

            if not synthesis_result.success:
                results[voice_id] = ConsistencyResult(
                    voice_id=voice_id,
                    similarity_score=0.0,
                    passed=False,
                    error=f"Synthesis failed: {synthesis_result.error}",
                )
                continue

            # Check consistency
            result = self.check_consistency(
                generated_audio=synthesis_result.audio_bytes,
                reference_path=voice_ref.reference_path,
                sample_rate=synthesis_result.sample_rate,
            )

            results[voice_id] = result

            if not result.passed:
                logger.warning(
                    f"Voice {voice_id} failed consistency check: "
                    f"similarity={result.similarity_score:.2f}"
                )

        return results
