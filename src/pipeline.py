"""Main pipeline for TTS & SRT generation."""

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from .engines.base import TTSEngine
from .engines.factory import create_engine, get_engine_from_config
from .models.config import Config
from .models.script import Script, TimelineOutput, Metadata
from .services.validator import ScriptValidator
from .services.synthesizer import Synthesizer
from .services.stitcher import AudioStitcher
from .utils.srt import generate_srt, save_srt


logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    """Result from running the pipeline."""

    success: bool
    lesson_id: str
    title: str
    audio_file: Optional[str]
    srt_file: Optional[str]
    timeline_file: Optional[str]
    duration_ms: int
    error: Optional[str] = None


class Pipeline:
    """Main pipeline for generating TTS audio and subtitles."""

    def __init__(
        self,
        engine: Optional[TTSEngine] = None,
        config: Optional[Config] = None,
    ):
        """
        Initialize the pipeline.

        Args:
            engine: TTS engine to use (if not provided, created from config)
            config: Configuration (if not provided, uses defaults)
        """
        self.config = config or Config()

        if engine:
            self.engine = engine
        else:
            self.engine = get_engine_from_config(self.config)

        self.validator = ScriptValidator(self.engine)
        self.synthesizer = Synthesizer(
            engine=self.engine,
            max_retries=self.config.synthesis.max_retries,
        )
        self.stitcher = AudioStitcher(
            initial_silence_ms=self.config.synthesis.initial_silence_ms,
            default_pause_ms=self.config.synthesis.default_pause_ms,
            normalize_dbfs=self.config.audio.normalize_to,
            sample_rate=self.config.audio.sample_rate,
        )

    def generate(
        self,
        script_path: str | Path,
        output_dir: str | Path,
        on_progress: Optional[callable] = None,
    ) -> PipelineResult:
        """
        Generate audio and subtitles from a script file.

        Args:
            script_path: Path to the JSON script file
            output_dir: Directory for output files
            on_progress: Optional callback for progress updates

        Returns:
            PipelineResult with output file paths and metadata
        """
        script_path = Path(script_path)
        output_dir = Path(output_dir)

        # Ensure output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Load and validate script
            logger.info(f"Loading script: {script_path}")
            script = self.validator.load_script(script_path)

            # Apply script settings to stitcher if present
            if script.settings:
                self.stitcher.initial_silence_ms = script.settings.initial_silence_ms
                self.stitcher.default_pause_ms = script.settings.default_pause_ms

            logger.info(f"Validating script: {script.title}")
            self.validator.validate_or_raise(script)

            # Generate using the script object
            return self.generate_from_script(script, output_dir, on_progress)

        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            return PipelineResult(
                success=False,
                lesson_id=script_path.stem,
                title="",
                audio_file=None,
                srt_file=None,
                timeline_file=None,
                duration_ms=0,
                error=str(e),
            )

    def generate_from_script(
        self,
        script: Script,
        output_dir: str | Path,
        on_progress: Optional[callable] = None,
    ) -> PipelineResult:
        """
        Generate audio and subtitles from a Script object.

        Args:
            script: Script object
            output_dir: Directory for output files
            on_progress: Optional callback for progress updates

        Returns:
            PipelineResult with output file paths and metadata
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Validate script
            logger.info(f"Validating script: {script.title}")
            self.validator.validate_or_raise(script)

            # Synthesize all lines
            logger.info(f"Synthesizing {len(script.lines)} lines...")
            synthesis_results = self.synthesizer.synthesize_script(
                script,
                on_progress=on_progress,
            )

            # Extract audio data for stitching
            audio_data = self.synthesizer.get_audio_data_for_stitching(synthesis_results)

            # Stitch audio
            logger.info("Stitching audio segments...")
            stitch_result = self.stitcher.stitch_from_bytes(audio_data)

            # Determine output format
            output_format = self.config.audio.output_format
            audio_ext = "mp3" if output_format == "mp3" else "wav"

            # Generate output file paths
            audio_file = output_dir / f"{script.lesson_id}.{audio_ext}"
            srt_file = output_dir / f"{script.lesson_id}.srt"
            timeline_file = output_dir / f"{script.lesson_id}_timeline.json"

            # Export audio
            logger.info(f"Exporting audio: {audio_file}")
            if output_format == "mp3":
                self.stitcher.export_mp3(stitch_result.audio, str(audio_file))
            else:
                self.stitcher.export_wav(stitch_result.audio, str(audio_file))

            # Generate and save SRT
            logger.info(f"Generating SRT: {srt_file}")
            srt_content = generate_srt(stitch_result.segments)
            save_srt(srt_content, str(srt_file))

            # Generate timeline JSON
            logger.info(f"Generating timeline: {timeline_file}")
            timeline = TimelineOutput(
                lesson_id=script.lesson_id,
                title=script.title,
                audio_file=audio_file.name,
                srt_file=srt_file.name,
                duration_ms=stitch_result.total_duration_ms,
                segments=stitch_result.segments,
                metadata=Metadata(
                    engine=self.config.engine,
                    generated_at=datetime.utcnow().isoformat() + "Z",
                ),
            )

            self._save_timeline(timeline, timeline_file)

            logger.info(
                f"Generation complete! Duration: {stitch_result.total_duration_ms}ms"
            )

            return PipelineResult(
                success=True,
                lesson_id=script.lesson_id,
                title=script.title,
                audio_file=str(audio_file),
                srt_file=str(srt_file),
                timeline_file=str(timeline_file),
                duration_ms=stitch_result.total_duration_ms,
            )

        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            return PipelineResult(
                success=False,
                lesson_id=script.lesson_id,
                title=script.title,
                audio_file=None,
                srt_file=None,
                timeline_file=None,
                duration_ms=0,
                error=str(e),
            )

    def _save_timeline(self, timeline: TimelineOutput, path: Path) -> None:
        """Save timeline to JSON file."""
        data = {
            "lesson_id": timeline.lesson_id,
            "title": timeline.title,
            "audio_file": timeline.audio_file,
            "srt_file": timeline.srt_file,
            "duration_ms": timeline.duration_ms,
            "segments": [
                {
                    "id": seg.id,
                    "speaker": seg.speaker,
                    "text": seg.text,
                    "start_ms": seg.start_ms,
                    "end_ms": seg.end_ms,
                    "audio_duration_ms": seg.audio_duration_ms,
                }
                for seg in timeline.segments
            ],
            "metadata": {
                "engine": timeline.metadata.engine,
                "generated_at": timeline.metadata.generated_at,
            },
        }

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def cleanup(self) -> None:
        """Release engine resources."""
        if self.engine:
            self.engine.cleanup()
