"""CLI entry point for TTS & SRT Generator."""

import logging
import sys
from pathlib import Path
from typing import Optional

import click
import yaml

from src.engines.factory import create_engine
from src.engines.edge import list_voices_sync
from src.models.config import Config
from src.pipeline import Pipeline
from src.services.validator import ScriptValidator, ValidationError


# Configure logging
def setup_logging(verbose: bool = False) -> None:
    """Configure logging based on verbosity."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%H:%M:%S",
    )


@click.group()
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose output")
def cli(verbose: bool) -> None:
    """TTS & SRT Generator - Convert conversation scripts to audio and subtitles."""
    setup_logging(verbose)


@cli.command()
@click.argument("script", type=click.Path(exists=True))
@click.option(
    "-o", "--output",
    type=click.Path(),
    default="output",
    help="Output directory (default: output/)",
)
@click.option(
    "-e", "--engine",
    type=click.Choice(["edge", "kokoro"]),
    default=None,
    help="TTS engine to use (default: from config or edge)",
)
@click.option(
    "-c", "--config",
    type=click.Path(exists=True),
    default=None,
    help="Path to configuration file",
)
@click.option(
    "-f", "--format",
    type=click.Choice(["mp3", "wav"]),
    default=None,
    help="Output audio format (default: mp3)",
)
def generate(
    script: str,
    output: str,
    engine: Optional[str],
    config: Optional[str],
    format: Optional[str],
) -> None:
    """Generate audio and subtitles from a conversation script.

    SCRIPT is the path to the JSON script file.
    """
    # Load configuration
    cfg = Config()
    if config:
        with open(config, "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f)
            cfg = Config.from_dict(config_data)

    # Override engine if specified
    if engine:
        cfg.engine = engine

    # Override format if specified
    if format:
        cfg.audio.output_format = format

    click.echo(f"Using engine: {cfg.engine}")
    click.echo(f"Output format: {cfg.audio.output_format}")
    click.echo(f"Output directory: {output}")
    click.echo()

    # Create and run pipeline
    try:
        pipeline = Pipeline(config=cfg)

        def on_progress(current: int, total: int, result) -> None:
            click.echo(f"  [{current}/{total}] Line {result.line.id}: {result.result.duration_ms}ms")

        result = pipeline.generate(
            script_path=script,
            output_dir=output,
            on_progress=on_progress,
        )

        if result.success:
            click.echo()
            click.echo(click.style("Generation successful!", fg="green"))
            click.echo(f"  Audio: {result.audio_file}")
            click.echo(f"  SRT: {result.srt_file}")
            click.echo(f"  Timeline: {result.timeline_file}")
            click.echo(f"  Duration: {result.duration_ms}ms ({result.duration_ms / 1000:.1f}s)")
        else:
            click.echo()
            click.echo(click.style(f"Generation failed: {result.error}", fg="red"))
            sys.exit(1)

    except Exception as e:
        click.echo(click.style(f"Error: {e}", fg="red"))
        sys.exit(1)


@cli.command()
@click.argument("script", type=click.Path(exists=True))
def validate(script: str) -> None:
    """Validate a conversation script without generating audio.

    SCRIPT is the path to the JSON script file.
    """
    try:
        validator = ScriptValidator()
        script_obj = validator.load_script(script)

        errors = validator.validate(script_obj)

        if errors:
            click.echo(click.style("Validation failed:", fg="red"))
            for error in errors:
                click.echo(f"  - {error}")
            sys.exit(1)
        else:
            click.echo(click.style("Script is valid!", fg="green"))
            click.echo(f"  Lesson ID: {script_obj.lesson_id}")
            click.echo(f"  Title: {script_obj.title}")
            click.echo(f"  Lines: {len(script_obj.lines)}")
            click.echo(f"  Language: {script_obj.language}")

    except Exception as e:
        click.echo(click.style(f"Error: {e}", fg="red"))
        sys.exit(1)


@cli.command()
@click.option(
    "-e", "--engine",
    type=click.Choice(["edge", "kokoro"]),
    default="edge",
    help="TTS engine to list voices for",
)
@click.option(
    "-l", "--language",
    default="en",
    help="Language filter for voices (default: en)",
)
def voices(engine: str, language: str) -> None:
    """List available voices for a TTS engine."""
    if engine == "edge":
        click.echo("Edge TTS voices:")
        click.echo()

        # Show mapped speaker IDs
        click.echo("Speaker ID mappings:")
        from src.models.config import DEFAULT_EDGE_VOICES
        for speaker_id, voice_name in DEFAULT_EDGE_VOICES.items():
            click.echo(f"  {speaker_id}: {voice_name}")

        click.echo()
        click.echo("All available Edge TTS voices (filtered by language):")

        try:
            all_voices = list_voices_sync(language)
            for voice in all_voices[:20]:  # Limit to first 20
                click.echo(f"  {voice['ShortName']}: {voice['Gender']}, {voice['Locale']}")

            if len(all_voices) > 20:
                click.echo(f"  ... and {len(all_voices) - 20} more")

            click.echo()
            click.echo(f"Total: {len(all_voices)} voices")

        except Exception as e:
            click.echo(f"  (Could not fetch voice list: {e})")

    elif engine == "kokoro":
        click.echo("Kokoro-ONNX voices:")
        click.echo()

        from src.models.config import DEFAULT_KOKORO_VOICES
        for speaker_id, voice_name in DEFAULT_KOKORO_VOICES.items():
            click.echo(f"  {speaker_id}: {voice_name}")


@cli.command()
@click.option(
    "-o", "--output",
    type=click.Path(),
    default="config/default.yaml",
    help="Output path for config file",
)
def init_config(output: str) -> None:
    """Generate a default configuration file."""
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    config_content = """# TTS & SRT Generator Configuration

# TTS Engine: "edge" (cloud, fast) or "kokoro" (local, high quality)
engine: "edge"

# Edge TTS settings (cloud-based)
edge:
  default_voice: "en-US-AriaNeural"
  voices:
    female_us_1: "en-US-AriaNeural"
    female_us_2: "en-US-JennyNeural"
    male_us_1: "en-US-GuyNeural"
    male_us_2: "en-US-ChristopherNeural"
    male_uk_1: "en-GB-RyanNeural"
    female_uk_1: "en-GB-SoniaNeural"

# Kokoro-ONNX settings (local)
kokoro:
  model_path: "./models/kokoro-v1.0.onnx"
  voices_path: "./models/voices-v1.0.bin"
  default_voice: "af_heart"
  voices:
    female_us_1: "af_heart"
    female_us_2: "af_bella"
    female_us_3: "af_nicole"
    female_us_4: "af_sarah"
    male_us_1: "am_adam"
    male_us_2: "am_michael"
    female_uk_1: "bf_emma"
    male_uk_1: "bm_george"

# Audio output settings
audio:
  sample_rate: 24000
  normalize_to: -16  # dBFS
  output_format: "mp3"  # "mp3" or "wav"

# Synthesis settings
synthesis:
  default_pause_ms: 400
  initial_silence_ms: 300
  max_retries: 3
"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(config_content)

    click.echo(f"Configuration file created: {output_path}")


@cli.command()
@click.argument("directory", type=click.Path(exists=True))
@click.option(
    "-o", "--output",
    type=click.Path(),
    default="output",
    help="Output directory (default: output/)",
)
@click.option(
    "-e", "--engine",
    type=click.Choice(["edge", "kokoro"]),
    default="edge",
    help="TTS engine to use",
)
@click.option(
    "-c", "--config",
    type=click.Path(exists=True),
    default=None,
    help="Path to configuration file",
)
def batch(
    directory: str,
    output: str,
    engine: str,
    config: Optional[str],
) -> None:
    """Process all JSON scripts in a directory.

    DIRECTORY is the path to the directory containing JSON script files.
    """
    # Load configuration
    cfg = Config()
    if config:
        with open(config, "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f)
            cfg = Config.from_dict(config_data)

    cfg.engine = engine

    # Find all JSON files
    scripts = list(Path(directory).glob("*.json"))

    if not scripts:
        click.echo("No JSON scripts found in directory")
        return

    click.echo(f"Found {len(scripts)} scripts to process")
    click.echo()

    # Create pipeline
    pipeline = Pipeline(config=cfg)

    success_count = 0
    fail_count = 0

    for script_path in scripts:
        click.echo(f"Processing: {script_path.name}")

        result = pipeline.generate(
            script_path=script_path,
            output_dir=output,
        )

        if result.success:
            click.echo(click.style(f"  OK - {result.duration_ms}ms", fg="green"))
            success_count += 1
        else:
            click.echo(click.style(f"  FAILED - {result.error}", fg="red"))
            fail_count += 1

    click.echo()
    click.echo(f"Completed: {success_count} success, {fail_count} failed")


if __name__ == "__main__":
    cli()
