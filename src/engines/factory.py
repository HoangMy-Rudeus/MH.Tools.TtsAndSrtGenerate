"""TTS Engine factory for creating engine instances."""

from typing import Optional

from .base import TTSEngine
from .edge import EdgeTTSEngine
from .kokoro import KokoroTTSEngine
from ..models.config import Config


def create_engine(
    engine_type: str,
    config: Optional[Config] = None,
) -> TTSEngine:
    """
    Create a TTS engine instance based on the engine type.

    Args:
        engine_type: Engine type ("edge" or "kokoro")
        config: Optional configuration object

    Returns:
        TTSEngine instance

    Raises:
        ValueError: If engine type is not supported
    """
    engine_type = engine_type.lower()

    if engine_type == "edge":
        custom_voices = None
        if config and config.edge:
            custom_voices = config.edge.voices
        engine = EdgeTTSEngine(custom_voices=custom_voices)
        engine.initialize()
        return engine

    elif engine_type == "kokoro":
        if config and config.kokoro:
            engine = KokoroTTSEngine(
                model_path=config.kokoro.model_path,
                voices_path=config.kokoro.voices_path,
                custom_voices=config.kokoro.voices,
            )
        else:
            engine = KokoroTTSEngine()
        engine.initialize()
        return engine

    else:
        raise ValueError(
            f"Unsupported engine type: {engine_type}. "
            f"Supported types: 'edge', 'kokoro'"
        )


def get_engine_from_config(config: Config) -> TTSEngine:
    """
    Create a TTS engine instance from configuration.

    Args:
        config: Configuration object

    Returns:
        TTSEngine instance
    """
    return create_engine(config.engine, config)
