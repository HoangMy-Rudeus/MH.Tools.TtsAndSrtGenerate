"""Forced alignment service using Whisper."""

import logging
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field

from src.models.config import AlignmentConfig
from src.services.stitcher import SegmentTiming

logger = logging.getLogger(__name__)


class AlignedSegment(BaseModel):
    """Segment with aligned timestamps."""
    line_id: int
    original_start_ms: int
    original_end_ms: int
    aligned_start_ms: int
    aligned_end_ms: int
    drift_ms: int
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    text: str = ""


class AlignmentResult(BaseModel):
    """Result of alignment process."""
    success: bool
    segments: list[AlignedSegment] = Field(default_factory=list)
    total_drift_ms: int = 0
    needs_review: bool = False
    error: Optional[str] = None


class AlignmentService:
    """Adjusts timestamps using Whisper forced alignment."""

    def __init__(self, config: AlignmentConfig):
        """
        Initialize alignment service.

        Args:
            config: Alignment configuration
        """
        self.config = config
        self._model = None

    def _load_model(self):
        """Load Whisper model lazily."""
        if self._model is None:
            import whisper
            logger.info("Loading Whisper model for alignment...")
            self._model = whisper.load_model("base")
            logger.info("Whisper model loaded")

    def align(
        self,
        audio_path: str | Path,
        segments: list[SegmentTiming],
        texts: dict[int, str],
    ) -> AlignmentResult:
        """
        Perform forced alignment on audio.

        Uses Whisper to transcribe and align timestamps.
        Compares with estimated timestamps and adjusts if drift exceeds threshold.

        Args:
            audio_path: Path to combined audio file
            segments: List of estimated segment timings
            texts: Dict mapping line_id to text

        Returns:
            AlignmentResult with adjusted segments
        """
        if not self.config.enabled:
            # Return original timings as aligned
            return AlignmentResult(
                success=True,
                segments=[
                    AlignedSegment(
                        line_id=seg.line_id,
                        original_start_ms=seg.start_ms,
                        original_end_ms=seg.end_ms,
                        aligned_start_ms=seg.start_ms,
                        aligned_end_ms=seg.end_ms,
                        drift_ms=0,
                        text=texts.get(seg.line_id, ""),
                    )
                    for seg in segments
                ]
            )

        try:
            self._load_model()

            # Transcribe with word-level timestamps
            result = self._model.transcribe(
                str(audio_path),
                word_timestamps=True,
                language="en",
            )

            # Extract word timings
            word_timings = self._extract_word_timings(result)

            # Match segments to word timings
            aligned_segments = self._match_segments(segments, texts, word_timings)

            # Calculate total drift
            total_drift = sum(abs(seg.drift_ms) for seg in aligned_segments)
            needs_review = any(
                abs(seg.drift_ms) > self.config.drift_threshold_ms
                for seg in aligned_segments
            )

            return AlignmentResult(
                success=True,
                segments=aligned_segments,
                total_drift_ms=total_drift,
                needs_review=needs_review,
            )

        except Exception as e:
            logger.error(f"Alignment failed: {e}")
            # Fall back to original timings
            return AlignmentResult(
                success=False,
                segments=[
                    AlignedSegment(
                        line_id=seg.line_id,
                        original_start_ms=seg.start_ms,
                        original_end_ms=seg.end_ms,
                        aligned_start_ms=seg.start_ms,
                        aligned_end_ms=seg.end_ms,
                        drift_ms=0,
                        text=texts.get(seg.line_id, ""),
                    )
                    for seg in segments
                ],
                error=str(e),
            )

    def _extract_word_timings(self, whisper_result: dict) -> list[dict]:
        """Extract word-level timings from Whisper result."""
        words = []

        for segment in whisper_result.get("segments", []):
            for word_info in segment.get("words", []):
                words.append({
                    "word": word_info["word"].strip(),
                    "start_ms": int(word_info["start"] * 1000),
                    "end_ms": int(word_info["end"] * 1000),
                })

        return words

    def _match_segments(
        self,
        segments: list[SegmentTiming],
        texts: dict[int, str],
        word_timings: list[dict],
    ) -> list[AlignedSegment]:
        """Match original segments to transcribed word timings."""
        aligned = []
        word_idx = 0

        for seg in segments:
            text = texts.get(seg.line_id, "")
            words_in_text = text.lower().split()
            num_words = len(words_in_text)

            if num_words == 0:
                aligned.append(AlignedSegment(
                    line_id=seg.line_id,
                    original_start_ms=seg.start_ms,
                    original_end_ms=seg.end_ms,
                    aligned_start_ms=seg.start_ms,
                    aligned_end_ms=seg.end_ms,
                    drift_ms=0,
                    text=text,
                ))
                continue

            # Find best matching window in word_timings
            best_start_ms = seg.start_ms
            best_end_ms = seg.end_ms

            if word_idx < len(word_timings):
                # Use word timings if available
                start_word_idx = word_idx
                end_word_idx = min(word_idx + num_words, len(word_timings)) - 1

                if start_word_idx < len(word_timings):
                    best_start_ms = word_timings[start_word_idx]["start_ms"]
                if end_word_idx < len(word_timings):
                    best_end_ms = word_timings[end_word_idx]["end_ms"]

                word_idx = end_word_idx + 1

            # Calculate drift
            start_drift = best_start_ms - seg.start_ms
            end_drift = best_end_ms - seg.end_ms
            avg_drift = (start_drift + end_drift) // 2

            # Use aligned timestamps if drift exceeds threshold
            use_aligned = abs(avg_drift) > self.config.drift_threshold_ms

            aligned.append(AlignedSegment(
                line_id=seg.line_id,
                original_start_ms=seg.start_ms,
                original_end_ms=seg.end_ms,
                aligned_start_ms=best_start_ms if use_aligned else seg.start_ms,
                aligned_end_ms=best_end_ms if use_aligned else seg.end_ms,
                drift_ms=avg_drift,
                text=text,
                confidence=0.9 if use_aligned else 1.0,
            ))

        return aligned
