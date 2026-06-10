"""Configuration data models."""

from dataclasses import dataclass, field


# Default speaker ID -> engine voice mappings (mirrors config/default.yaml)
DEFAULT_EDGE_VOICES: dict[str, str] = {
    "female_us_1": "en-US-AriaNeural",
    "female_us_2": "en-US-JennyNeural",
    "male_us_1": "en-US-GuyNeural",
    "male_us_2": "en-US-ChristopherNeural",
    "male_uk_1": "en-GB-RyanNeural",
    "female_uk_1": "en-GB-SoniaNeural",
}

DEFAULT_KOKORO_VOICES: dict[str, str] = {
    "female_us_1": "af_heart",
    "female_us_2": "af_bella",
    "female_us_3": "af_nicole",
    "female_us_4": "af_sarah",
    "male_us_1": "am_adam",
    "male_us_2": "am_michael",
    "female_uk_1": "bf_emma",
    "male_uk_1": "bm_george",
}


@dataclass
class EdgeConfig:
    """Edge TTS engine configuration."""

    default_voice: str = "en-US-AriaNeural"
    voices: dict[str, str] = field(default_factory=lambda: dict(DEFAULT_EDGE_VOICES))


@dataclass
class KokoroConfig:
    """Kokoro-ONNX engine configuration."""

    model_path: str = "./models/kokoro-v1.0.fp16.onnx"
    voices_path: str = "./models/voices-v1.0.bin"
    default_voice: str = "af_heart"
    voices: dict[str, str] = field(default_factory=lambda: dict(DEFAULT_KOKORO_VOICES))


@dataclass
class AudioConfig:
    """Audio output configuration."""

    sample_rate: int = 24000
    normalize_to: float = -16.0
    output_format: str = "mp3"


@dataclass
class SynthesisConfig:
    """Synthesis timing/retry configuration."""

    default_pause_ms: int = 400
    initial_silence_ms: int = 300
    max_retries: int = 3


@dataclass
class Config:
    """Top-level configuration."""

    engine: str = "edge"
    edge: EdgeConfig = field(default_factory=EdgeConfig)
    kokoro: KokoroConfig = field(default_factory=KokoroConfig)
    audio: AudioConfig = field(default_factory=AudioConfig)
    synthesis: SynthesisConfig = field(default_factory=SynthesisConfig)

    @classmethod
    def from_dict(cls, data: dict) -> "Config":
        """
        Build a Config from a parsed YAML/JSON dict.

        Missing keys fall back to defaults, so partial config files are valid.

        Args:
            data: Parsed configuration dictionary

        Returns:
            Config instance
        """
        data = data or {}

        edge_data = data.get("edge", {}) or {}
        edge = EdgeConfig(
            default_voice=edge_data.get("default_voice", EdgeConfig().default_voice),
            voices={**DEFAULT_EDGE_VOICES, **(edge_data.get("voices") or {})},
        )

        kokoro_data = data.get("kokoro", {}) or {}
        kokoro_defaults = KokoroConfig()
        kokoro = KokoroConfig(
            model_path=kokoro_data.get("model_path", kokoro_defaults.model_path),
            voices_path=kokoro_data.get("voices_path", kokoro_defaults.voices_path),
            default_voice=kokoro_data.get("default_voice", kokoro_defaults.default_voice),
            voices={**DEFAULT_KOKORO_VOICES, **(kokoro_data.get("voices") or {})},
        )

        audio_data = data.get("audio", {}) or {}
        audio_defaults = AudioConfig()
        audio = AudioConfig(
            sample_rate=audio_data.get("sample_rate", audio_defaults.sample_rate),
            normalize_to=audio_data.get("normalize_to", audio_defaults.normalize_to),
            output_format=audio_data.get("output_format", audio_defaults.output_format),
        )

        synthesis_data = data.get("synthesis", {}) or {}
        synthesis_defaults = SynthesisConfig()
        synthesis = SynthesisConfig(
            default_pause_ms=synthesis_data.get("default_pause_ms", synthesis_defaults.default_pause_ms),
            initial_silence_ms=synthesis_data.get("initial_silence_ms", synthesis_defaults.initial_silence_ms),
            max_retries=synthesis_data.get("max_retries", synthesis_defaults.max_retries),
        )

        return cls(
            engine=data.get("engine", "edge"),
            edge=edge,
            kokoro=kokoro,
            audio=audio,
            synthesis=synthesis,
        )

    def to_dict(self) -> dict:
        """Serialize to a plain dict matching the from_dict / YAML structure."""
        return {
            "engine": self.engine,
            "edge": {
                "default_voice": self.edge.default_voice,
                "voices": dict(self.edge.voices),
            },
            "kokoro": {
                "model_path": self.kokoro.model_path,
                "voices_path": self.kokoro.voices_path,
                "default_voice": self.kokoro.default_voice,
                "voices": dict(self.kokoro.voices),
            },
            "audio": {
                "sample_rate": self.audio.sample_rate,
                "normalize_to": self.audio.normalize_to,
                "output_format": self.audio.output_format,
            },
            "synthesis": {
                "default_pause_ms": self.synthesis.default_pause_ms,
                "initial_silence_ms": self.synthesis.initial_silence_ms,
                "max_retries": self.synthesis.max_retries,
            },
        }
