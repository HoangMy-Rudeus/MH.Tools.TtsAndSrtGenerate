"""Generation runner seam — wraps Pipeline so the TUI can stay decoupled/testable."""

from pathlib import Path
from typing import Callable, Optional, Protocol

from ..models.config import Config
from ..pipeline import Pipeline, PipelineResult

ProgressCallback = Callable[[int, int], None]


class GenerationRunner(Protocol):
    """Runs one script to completion, reporting (current, total) line progress."""

    def run(
        self,
        script_path: str,
        output_dir: str,
        config: Config,
        on_progress: ProgressCallback,
    ) -> PipelineResult:
        ...


class PipelineRunner:
    """Real runner backed by the existing Pipeline."""

    def run(
        self,
        script_path: str,
        output_dir: str,
        config: Config,
        on_progress: ProgressCallback,
    ) -> PipelineResult:
        pipeline = Pipeline(config=config)

        def cb(current: int, total: int, result) -> None:
            on_progress(current, total)

        try:
            return pipeline.generate(script_path, output_dir, on_progress=cb)
        finally:
            pipeline.cleanup()


class FakeRunner:
    """Test runner: emits synthetic progress and returns a canned PipelineResult."""

    def __init__(self, total_lines: int = 1, duration_ms: int = 1000,
                 fail_with: Optional[str] = None):
        self.total_lines = total_lines
        self.duration_ms = duration_ms
        self.fail_with = fail_with

    def run(self, script_path, output_dir, config, on_progress) -> PipelineResult:
        lesson_id = Path(script_path).stem
        for i in range(1, self.total_lines + 1):
            on_progress(i, self.total_lines)
        if self.fail_with:
            return PipelineResult(
                success=False, lesson_id=lesson_id, title=lesson_id,
                audio_file=None, srt_file=None, timeline_file=None,
                subtitle_file=None, duration_ms=0, error=self.fail_with,
            )
        return PipelineResult(
            success=True, lesson_id=lesson_id, title=lesson_id,
            audio_file=f"{output_dir}/{lesson_id}.mp3",
            srt_file=f"{output_dir}/{lesson_id}.srt",
            timeline_file=f"{output_dir}/{lesson_id}_timeline.json",
            subtitle_file=f"{output_dir}/{lesson_id}_subtitles.json",
            duration_ms=self.duration_ms,
        )
