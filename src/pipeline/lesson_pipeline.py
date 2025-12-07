"""Main pipeline for lesson generation."""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from src.models.script import ScriptInput, Segment, LessonOutput, LessonMetadata
from src.models.config import AppConfig
from src.services.validator import ScriptValidator, ValidationResult
from src.services.tts_worker import TTSWorker, load_voice_registry, SynthesisResult
from src.services.edge_tts_worker import EdgeTTSWorker
from src.services.stitcher import AudioStitcher, StitchResult
from src.services.aligner import AlignmentService, AlignmentResult
from src.utils.srt import save_srt

logger = logging.getLogger(__name__)


class PipelineError(Exception):
    """Error during pipeline execution."""
    pass


class LessonPipeline:
    """Orchestrates the full lesson generation pipeline."""

    def __init__(self, config: AppConfig):
        """
        Initialize pipeline with configuration.

        Args:
            config: Application configuration
        """
        self.config = config

        # Load voice registry (only needed for XTTS)
        self.voice_registry = load_voice_registry(config.voices.directory)

        # Initialize services
        # For Edge TTS, skip voice registry validation (uses cloud voices)
        if config.tts.engine == "edge":
            self.validator = ScriptValidator(voice_registry=None)
        else:
            self.validator = ScriptValidator(
                voice_registry={v: r.reference_path for v, r in self.voice_registry.items()}
            )

        # Select TTS engine based on config
        if config.tts.engine == "edge":
            logger.info("Using Edge TTS engine (fast cloud-based)")
            self.tts_worker = EdgeTTSWorker(
                tts_config=config.tts,
                synthesis_config=config.synthesis,
                voice_registry=self.voice_registry,
            )
        else:
            logger.info("Using XTTS engine (local voice cloning)")
            self.tts_worker = TTSWorker(
                tts_config=config.tts,
                synthesis_config=config.synthesis,
                voice_registry=self.voice_registry,
            )
        self.stitcher = AudioStitcher(
            audio_config=config.audio,
            synthesis_config=config.synthesis,
        )
        self.aligner = AlignmentService(config=config.alignment)

    @classmethod
    def from_config_file(cls, config_path: str | Path) -> "LessonPipeline":
        """Create pipeline from config file."""
        config = AppConfig.from_yaml(config_path)
        return cls(config)

    @classmethod
    def from_default_config(cls) -> "LessonPipeline":
        """Create pipeline with default configuration."""
        return cls(AppConfig.default())

    def generate(
        self,
        script: dict,
        output_dir: str | Path,
    ) -> LessonOutput:
        """
        Generate lesson from script.

        Pipeline steps:
        1. Validate script
        2. Synthesize all lines
        3. Stitch audio
        4. Run forced alignment
        5. Generate outputs (audio, SRT, JSON)

        Args:
            script: Script dictionary
            output_dir: Output directory

        Returns:
            LessonOutput with paths and metadata

        Raises:
            PipelineError: If pipeline fails
        """
        output_dir = Path(output_dir)

        # Step 1: Validate
        logger.info("Step 1: Validating script...")
        validation = self.validator.validate(script)
        if not validation.success:
            errors = "; ".join(f"{e.field}: {e.message}" for e in validation.errors)
            raise PipelineError(f"Validation failed: {errors}")

        parsed = ScriptInput(**script)
        logger.info(f"Validated script: {parsed.lesson_id} with {len(parsed.lines)} lines")

        # Step 2: Synthesize
        logger.info("Step 2: Synthesizing audio...")
        synthesis_results = self._synthesize_with_retry(parsed)

        failed = [r for r in synthesis_results if not r.success]
        if failed:
            failed_ids = [r.line_id for r in failed]
            raise PipelineError(f"Synthesis failed for lines: {failed_ids}")

        # Step 3: Stitch
        logger.info("Step 3: Stitching audio...")
        stitch_result = self.stitcher.stitch(
            synthesis_results=synthesis_results,
            lines=parsed.lines,
            output_dir=output_dir,
            filename_base=parsed.lesson_id,
        )

        if not stitch_result.success:
            raise PipelineError(f"Stitching failed: {stitch_result.error}")

        # Step 4: Alignment
        logger.info("Step 4: Running forced alignment...")
        texts = {line.id: line.text for line in parsed.lines}
        speakers = {line.id: line.speaker for line in parsed.lines}

        alignment_result = self.aligner.align(
            audio_path=stitch_result.wav_path,
            segments=stitch_result.segments,
            texts=texts,
        )

        # Step 5: Generate outputs
        logger.info("Step 5: Generating outputs...")

        # Build segments with final timing
        segments = []
        for aligned in alignment_result.segments:
            segments.append(Segment(
                id=aligned.line_id,
                speaker=speakers.get(aligned.line_id, "unknown"),
                text=aligned.text,
                start_ms=aligned.aligned_start_ms,
                end_ms=aligned.aligned_end_ms,
                audio_duration_ms=aligned.aligned_end_ms - aligned.aligned_start_ms,
                confidence=aligned.confidence,
            ))

        # Save SRT
        srt_path = output_dir / f"{parsed.lesson_id}.srt"
        save_srt(segments, srt_path)

        # Build output
        output = LessonOutput(
            lesson_id=parsed.lesson_id,
            title=parsed.title,
            audio_file=str(stitch_result.mp3_path),
            srt_file=str(srt_path),
            duration_ms=stitch_result.total_duration_ms,
            segments=segments,
            metadata=LessonMetadata(
                model_version=f"{self.config.tts.engine}:{self.config.tts.model if self.config.tts.engine == 'xtts' else self.config.tts.edge_voice}",
                generated_at=datetime.now(timezone.utc).isoformat(),
                quality_score=self._calculate_quality_score(alignment_result),
            ),
        )

        # Save timeline JSON
        timeline_path = output_dir / f"{parsed.lesson_id}.json"
        with open(timeline_path, "w", encoding="utf-8") as f:
            f.write(output.model_dump_json(indent=2))

        logger.info(f"Generation complete: {output.audio_file}")
        logger.info(f"Duration: {output.duration_ms}ms, Quality: {output.metadata.quality_score:.2f}")

        return output

    def _synthesize_with_retry(self, script: ScriptInput) -> list[SynthesisResult]:
        """Synthesize with retry on failure."""
        results = []

        for line in script.lines:
            result = self.tts_worker.synthesize_line(line)

            # Retry on failure
            if not result.success:
                for attempt in range(1, self.config.retry.max_attempts):
                    logger.warning(f"Retry {attempt} for line {line.id}")
                    result = self.tts_worker.synthesize_line(line)
                    if result.success:
                        break

            results.append(result)

        return results

    def _calculate_quality_score(self, alignment: AlignmentResult) -> float:
        """Calculate overall quality score from alignment."""
        if not alignment.segments:
            return 1.0

        # Average confidence weighted by inverse drift
        total_score = 0.0
        for seg in alignment.segments:
            drift_penalty = min(abs(seg.drift_ms) / 500.0, 0.5)  # Max 0.5 penalty
            segment_score = seg.confidence * (1.0 - drift_penalty)
            total_score += segment_score

        return total_score / len(alignment.segments)

    def generate_from_file(
        self,
        script_path: str | Path,
        output_dir: str | Path,
    ) -> LessonOutput:
        """Generate lesson from script file."""
        with open(script_path) as f:
            script = json.load(f)
        return self.generate(script, output_dir)
