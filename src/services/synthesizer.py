"""TTS synthesis orchestration service."""

import logging
from dataclasses import dataclass
from typing import Optional

from ..engines.base import TTSEngine, SynthesisResult
from ..models.script import Script, ScriptLine


logger = logging.getLogger(__name__)


@dataclass
class LineSynthesisResult:
    """Result from synthesizing a script line."""

    line: ScriptLine
    result: SynthesisResult
    attempts: int


class SynthesisError(Exception):
    """Raised when synthesis fails."""

    def __init__(self, line_id: int, message: str):
        self.line_id = line_id
        super().__init__(f"Line {line_id}: {message}")


class Synthesizer:
    """Orchestrates TTS synthesis for script lines."""

    def __init__(
        self,
        engine: TTSEngine,
        max_retries: int = 3,
        default_speech_rate: float = 1.0,
    ):
        """
        Initialize the synthesizer.

        Args:
            engine: TTS engine to use
            max_retries: Maximum retry attempts for failed synthesis
            default_speech_rate: Default speech rate multiplier
        """
        self.engine = engine
        self.max_retries = max_retries
        self.default_speech_rate = default_speech_rate

    def synthesize_line(
        self,
        line: ScriptLine,
        speech_rate_override: Optional[float] = None,
    ) -> LineSynthesisResult:
        """
        Synthesize a single script line.

        Args:
            line: Script line to synthesize
            speech_rate_override: Optional override for speech rate

        Returns:
            LineSynthesisResult with synthesis result

        Raises:
            SynthesisError: If synthesis fails after all retries
        """
        # Determine voice to use (prefer explicit voice, fall back to speaker)
        voice = line.voice if line.voice else line.speaker

        # Determine speech rate
        speed = speech_rate_override or line.speech_rate or self.default_speech_rate

        attempts = 0
        last_error = None

        while attempts < self.max_retries:
            attempts += 1

            result = self.engine.synthesize(
                text=line.text,
                voice=voice,
                emotion=line.emotion,
                speed=speed,
            )

            # Update line_id in result
            result.line_id = line.id

            if result.success:
                logger.debug(
                    f"Synthesized line {line.id}: {result.duration_ms}ms "
                    f"(attempt {attempts})"
                )
                return LineSynthesisResult(
                    line=line,
                    result=result,
                    attempts=attempts,
                )

            last_error = result.error
            logger.warning(
                f"Synthesis failed for line {line.id} (attempt {attempts}): {result.error}"
            )

        # All retries exhausted
        raise SynthesisError(
            line.id,
            f"Failed after {attempts} attempts: {last_error}"
        )

    def synthesize_script(
        self,
        script: Script,
        on_progress: Optional[callable] = None,
    ) -> list[LineSynthesisResult]:
        """
        Synthesize all lines in a script.

        Args:
            script: Script to synthesize
            on_progress: Optional callback for progress updates
                        (called with current_line, total_lines, result)

        Returns:
            List of LineSynthesisResult objects

        Raises:
            SynthesisError: If any line fails after all retries
        """
        results = []
        total_lines = len(script.lines)

        # Get default speech rate from script settings
        default_rate = self.default_speech_rate
        if script.settings and script.settings.speech_rate:
            default_rate = script.settings.speech_rate

        for i, line in enumerate(script.lines):
            logger.info(f"Synthesizing line {i + 1}/{total_lines}: {line.text[:50]}...")

            result = self.synthesize_line(line, speech_rate_override=default_rate if line.speech_rate == 1.0 else None)
            results.append(result)

            if on_progress:
                on_progress(i + 1, total_lines, result)

        return results

    def get_audio_data_for_stitching(
        self,
        results: list[LineSynthesisResult],
    ) -> list[tuple[int, str, str, bytes, int]]:
        """
        Extract audio data from synthesis results for stitching.

        Args:
            results: List of synthesis results

        Returns:
            List of tuples (line_id, speaker, text, audio_bytes, pause_after_ms)
        """
        audio_data = []

        for result in results:
            if result.result.success and result.result.audio_bytes:
                audio_data.append((
                    result.line.id,
                    result.line.speaker,
                    result.line.text,
                    result.result.audio_bytes,
                    result.line.pause_after_ms,
                ))

        return audio_data
