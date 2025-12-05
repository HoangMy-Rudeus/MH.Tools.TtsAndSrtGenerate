"""CLI entry point for TTS and SRT Generator."""

import logging
import sys
from pathlib import Path

import click

from src.pipeline.lesson_pipeline import LessonPipeline, PipelineError
from src.models.config import AppConfig


def setup_logging(verbose: bool = False):
    """Configure logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """TTS and SRT Generator - Convert scripts to audio lessons."""
    pass


@cli.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.option(
    "-o", "--output",
    type=click.Path(),
    default="./output",
    help="Output directory (default: ./output)",
)
@click.option(
    "-c", "--config",
    type=click.Path(exists=True),
    default=None,
    help="Config file path (default: config/default.yaml)",
)
@click.option(
    "-v", "--verbose",
    is_flag=True,
    help="Enable verbose logging",
)
def generate(input_file: str, output: str, config: str | None, verbose: bool):
    """
    Generate audio lesson from script.

    INPUT_FILE: Path to JSON script file

    Example:
        python main.py generate examples/sample_script.json -o ./output
    """
    setup_logging(verbose)
    logger = logging.getLogger(__name__)

    try:
        # Load config
        if config:
            app_config = AppConfig.from_yaml(config)
        else:
            config_path = Path("config/default.yaml")
            if config_path.exists():
                app_config = AppConfig.from_yaml(config_path)
            else:
                app_config = AppConfig.default()

        # Create pipeline
        pipeline = LessonPipeline(app_config)

        # Generate
        click.echo(f"Generating lesson from: {input_file}")
        result = pipeline.generate_from_file(input_file, output)

        click.echo("")
        click.echo("Generation complete!")
        click.echo(f"  Audio: {result.audio_file}")
        click.echo(f"  SRT:   {result.srt_file}")
        click.echo(f"  JSON:  {Path(output) / f'{result.lesson_id}.json'}")
        click.echo(f"  Duration: {result.duration_ms / 1000:.1f}s")
        click.echo(f"  Quality:  {result.metadata.quality_score:.2f}")

    except PipelineError as e:
        logger.error(f"Pipeline error: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        click.echo(f"Unexpected error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.option(
    "-c", "--config",
    type=click.Path(exists=True),
    default=None,
    help="Config file path",
)
def validate(input_file: str, config: str | None):
    """
    Validate script file without generating.

    INPUT_FILE: Path to JSON script file
    """
    import json
    from src.services.validator import ScriptValidator
    from src.services.tts_worker import load_voice_registry

    # Load config for voice registry
    if config:
        app_config = AppConfig.from_yaml(config)
    else:
        app_config = AppConfig.default()

    voices = load_voice_registry(app_config.voices.directory)
    validator = ScriptValidator(
        voice_registry={v: r.reference_path for v, r in voices.items()}
    )

    with open(input_file) as f:
        script = json.load(f)

    result = validator.validate(script)

    if result.success:
        click.echo("Validation passed!")
        if result.warnings:
            click.echo("\nWarnings:")
            for w in result.warnings:
                line_info = f" (line {w.line_id})" if w.line_id else ""
                click.echo(f"  - {w.field}{line_info}: {w.message}")
    else:
        click.echo("Validation failed!", err=True)
        click.echo("\nErrors:")
        for e in result.errors:
            line_info = f" (line {e.line_id})" if e.line_id else ""
            click.echo(f"  - {e.field}{line_info}: {e.message}", err=True)
        sys.exit(1)


@cli.command()
def list_voices():
    """List available voices in registry."""
    from src.services.tts_worker import load_voice_registry

    config_path = Path("config/default.yaml")
    if config_path.exists():
        app_config = AppConfig.from_yaml(config_path)
    else:
        app_config = AppConfig.default()

    voices = load_voice_registry(app_config.voices.directory)

    if not voices:
        click.echo(f"No voices found in: {app_config.voices.directory}")
        click.echo("\nAdd .wav files to the voices directory to register them.")
        return

    click.echo("Available voices:")
    for voice_id, ref in voices.items():
        click.echo(f"  - {voice_id}: {ref.reference_path}")


if __name__ == "__main__":
    cli()
