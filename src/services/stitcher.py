"""Audio stitching service."""

import logging
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field

from src.models.script import ScriptLine
from src.models.config import AudioConfig, SynthesisConfig
from src.services.tts_worker import SynthesisResult
from src.utils.audio import (
    wav_bytes_to_segment,
    normalize_audio,
    add_silence,
    trim_silence,
    export_audio,
    get_audio_duration_ms,
)

logger = logging.getLogger(__name__)


class SegmentTiming(BaseModel):
    """Timing information for a single segment."""
    line_id: int
    start_ms: int
    end_ms: int
    audio_duration_ms: int


class StitchResult(BaseModel):
    """Result of audio stitching."""
    success: bool
    wav_path: Optional[Path] = None
    mp3_path: Optional[Path] = None
    total_duration_ms: int = 0
    segments: list[SegmentTiming] = Field(default_factory=list)
    error: Optional[str] = None

    class Config:
        arbitrary_types_allowed = True


class AudioStitcher:
    """Concatenates per-line audio with gaps and normalization."""

    def __init__(
        self,
        audio_config: AudioConfig,
        synthesis_config: SynthesisConfig,
    ):
        """
        Initialize stitcher.

        Args:
            audio_config: Audio output configuration
            synthesis_config: Synthesis parameters
        """
        self.audio_config = audio_config
        self.synthesis_config = synthesis_config

    def stitch(
        self,
        synthesis_results: list[SynthesisResult],
        lines: list[ScriptLine],
        output_dir: str | Path,
        filename_base: str,
    ) -> StitchResult:
        """
        Stitch synthesized audio segments together.

        Pipeline:
        1. Add initial silence
        2. For each segment: trim silence, add to combined, add pause
        3. Normalize final audio
        4. Export as WAV and MP3

        Args:
            synthesis_results: List of synthesis results
            lines: Original script lines (for pause metadata)
            output_dir: Output directory
            filename_base: Base filename (without extension)

        Returns:
            StitchResult with paths and timing info
        """
        from pydub import AudioSegment

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Map line_id to pause_after_ms
        pause_map = {line.id: line.pause_after_ms for line in lines}

        # Start with initial silence
        combined = add_silence(
            self.synthesis_config.initial_silence_ms,
            self.audio_config.sample_rate
        )
        current_position_ms = self.synthesis_config.initial_silence_ms

        segments: list[SegmentTiming] = []

        for result in synthesis_results:
            if not result.success or not result.audio_bytes:
                logger.warning(f"Skipping failed synthesis for line {result.line_id}")
                continue

            # Convert to AudioSegment
            segment = wav_bytes_to_segment(result.audio_bytes)

            # Trim silence from edges
            segment = trim_silence(segment)

            # Record timing
            segment_duration = get_audio_duration_ms(segment)
            segments.append(SegmentTiming(
                line_id=result.line_id,
                start_ms=current_position_ms,
                end_ms=current_position_ms + segment_duration,
                audio_duration_ms=segment_duration,
            ))

            # Add segment to combined
            combined += segment

            # Update position
            current_position_ms += segment_duration

            # Add pause after
            pause_ms = pause_map.get(result.line_id, self.synthesis_config.default_pause_ms)
            if pause_ms > 0:
                combined += add_silence(pause_ms, self.audio_config.sample_rate)
                current_position_ms += pause_ms

        # Normalize final audio
        combined = normalize_audio(combined, self.audio_config.normalization_target)

        # Export
        wav_path = output_dir / f"{filename_base}.wav"
        mp3_path = output_dir / f"{filename_base}.mp3"

        export_audio(combined, wav_path, format="wav")
        export_audio(
            combined,
            mp3_path,
            format="mp3",
            bitrate=f"{self.audio_config.mp3_bitrate}k"
        )

        total_duration = get_audio_duration_ms(combined)

        logger.info(f"Stitched {len(segments)} segments, total duration: {total_duration}ms")

        return StitchResult(
            success=True,
            wav_path=wav_path,
            mp3_path=mp3_path,
            total_duration_ms=total_duration,
            segments=segments,
        )
