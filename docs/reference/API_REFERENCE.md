# API Reference

Python API documentation for programmatic usage.

## Quick Start

```python
from src.pipeline import Pipeline

# Create pipeline with default settings
pipeline = Pipeline()

# Generate audio and subtitles
result = pipeline.generate(
    script_path="script.json",
    output_dir="output/"
)

print(f"Audio: {result.audio_file}")
print(f"Duration: {result.duration_ms}ms")
```

---

## Pipeline

The main entry point for generating audio and subtitles.

### `Pipeline`

```python
from src.pipeline import Pipeline
from src.models.config import Config
from src.engines.base import TTSEngine

class Pipeline:
    def __init__(
        self,
        engine: Optional[TTSEngine] = None,
        config: Optional[Config] = None,
    ) -> None:
        """
        Initialize the pipeline.

        Args:
            engine: TTS engine to use. If not provided, created from config.
            config: Configuration. If not provided, uses defaults.
        """
```

### `Pipeline.generate()`

```python
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
                    Signature: (current: int, total: int, result: LineSynthesisResult)

    Returns:
        PipelineResult with output file paths and metadata
    """
```

### `Pipeline.generate_from_script()`

```python
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
```

### `PipelineResult`

```python
@dataclass
class PipelineResult:
    success: bool               # Whether generation succeeded
    lesson_id: str              # Lesson identifier
    title: str                  # Lesson title
    audio_file: Optional[str]   # Path to audio file
    srt_file: Optional[str]     # Path to SRT file
    timeline_file: Optional[str]  # Path to timeline JSON
    duration_ms: int            # Total duration in milliseconds
    error: Optional[str]        # Error message if failed
```

---

## Configuration

### `Config`

```python
from src.models.config import Config

@dataclass
class Config:
    engine: str = "edge"                    # "edge" or "kokoro"
    edge: EdgeConfig                        # Edge TTS settings
    kokoro: KokoroConfig                    # Kokoro TTS settings
    audio: AudioConfig                      # Audio output settings
    synthesis: SynthesisConfig              # Synthesis settings

    @classmethod
    def from_dict(cls, data: dict) -> Config:
        """Create Config from dictionary (e.g., loaded from YAML)."""
```

### `EdgeConfig`

```python
@dataclass
class EdgeConfig:
    default_voice: str = "en-US-AriaNeural"
    voices: dict[str, str]  # Speaker ID -> Edge voice mapping
```

### `KokoroConfig`

```python
@dataclass
class KokoroConfig:
    model_path: str = "./models/kokoro-v1.0.onnx"
    voices_path: str = "./models/voices-v1.0.bin"
    default_voice: str = "af_heart"
    voices: dict[str, str]  # Speaker ID -> Kokoro voice mapping
```

### `AudioConfig`

```python
@dataclass
class AudioConfig:
    sample_rate: int = 24000
    normalize_to: int = -16       # dBFS
    output_format: str = "mp3"    # "mp3" or "wav"
```

### `SynthesisConfig`

```python
@dataclass
class SynthesisConfig:
    default_pause_ms: int = 400
    initial_silence_ms: int = 300
    max_retries: int = 3
```

---

## TTS Engines

### `TTSEngine` (Abstract Base)

```python
from src.engines.base import TTSEngine, SynthesisResult

class TTSEngine(ABC):
    @abstractmethod
    def initialize(self) -> None:
        """Load model/connect to service."""

    @abstractmethod
    def synthesize(
        self,
        text: str,
        voice: str,
        emotion: str = "neutral",
        speed: float = 1.0,
    ) -> SynthesisResult:
        """Synthesize text to audio."""

    @abstractmethod
    def get_available_voices(self) -> list[str]:
        """List available voice IDs."""

    @abstractmethod
    def cleanup(self) -> None:
        """Release resources."""
```

### `EdgeTTSEngine`

```python
from src.engines.edge import EdgeTTSEngine

class EdgeTTSEngine(TTSEngine):
    def __init__(
        self,
        custom_voices: Optional[dict[str, str]] = None
    ) -> None:
        """
        Initialize Edge TTS engine.

        Args:
            custom_voices: Custom speaker->voice mapping
        """
```

### `KokoroTTSEngine`

```python
from src.engines.kokoro import KokoroTTSEngine

class KokoroTTSEngine(TTSEngine):
    def __init__(
        self,
        model_path: str = "kokoro-v1.0.onnx",
        voices_path: str = "voices-v1.0.bin",
        custom_voices: Optional[dict[str, str]] = None,
    ) -> None:
        """
        Initialize Kokoro-ONNX engine.

        Args:
            model_path: Path to ONNX model file
            voices_path: Path to voices binary file
            custom_voices: Custom speaker->voice mapping
        """
```

### `SynthesisResult`

```python
@dataclass
class SynthesisResult:
    line_id: int                    # Line identifier
    success: bool                   # Whether synthesis succeeded
    audio_bytes: Optional[bytes]    # WAV or MP3 bytes
    duration_ms: int                # Audio duration in milliseconds
    sample_rate: int                # Sample rate
    error: Optional[str]            # Error message if failed
```

### Engine Factory

```python
from src.engines.factory import create_engine, get_engine_from_config

def create_engine(
    engine_type: str,
    config: Optional[Config] = None,
) -> TTSEngine:
    """
    Create a TTS engine instance.

    Args:
        engine_type: "edge" or "kokoro"
        config: Optional configuration

    Returns:
        TTSEngine instance
    """

def get_engine_from_config(config: Config) -> TTSEngine:
    """Create engine from configuration."""
```

---

## Data Models

### `Script`

```python
from src.models.script import Script, ScriptLine, ScriptSettings

@dataclass
class Script:
    lesson_id: str                          # Unique identifier
    title: str                              # Human-readable title
    lines: list[ScriptLine]                 # Conversation lines
    language: str = "en"                    # Language code
    level: str = "B1"                       # CEFR level
    settings: Optional[ScriptSettings]      # Script settings
```

### `ScriptLine`

```python
@dataclass
class ScriptLine:
    id: int                         # Unique line ID
    speaker: str                    # Speaker identifier
    text: str                       # Text to synthesize
    voice: Optional[str] = None     # Direct voice override
    emotion: str = "neutral"        # Emotion hint
    pause_after_ms: int = 400       # Pause after this line
    speech_rate: float = 1.0        # Speed multiplier
```

### `ScriptSettings`

```python
@dataclass
class ScriptSettings:
    speech_rate: float = 1.0
    initial_silence_ms: int = 300
    default_pause_ms: int = 400
```

### `Segment`

```python
@dataclass
class Segment:
    id: int                 # Line ID
    speaker: str            # Speaker identifier
    text: str               # Spoken text
    start_ms: int           # Start time in milliseconds
    end_ms: int             # End time in milliseconds
    audio_duration_ms: int  # Audio duration
```

### `TimelineOutput`

```python
@dataclass
class TimelineOutput:
    lesson_id: str
    title: str
    audio_file: str
    srt_file: str
    duration_ms: int
    segments: list[Segment]
    metadata: Metadata
```

---

## Services

### `ScriptValidator`

```python
from src.services.validator import ScriptValidator, ValidationError

class ScriptValidator:
    def __init__(self, engine: Optional[TTSEngine] = None):
        """Initialize validator with optional engine for voice validation."""

    def validate(self, script: Script) -> list[str]:
        """Return list of validation errors (empty if valid)."""

    def validate_or_raise(self, script: Script) -> None:
        """Raise ValidationError if invalid."""

    @staticmethod
    def load_script(path: str | Path) -> Script:
        """Load and parse script from JSON file."""

    @staticmethod
    def parse_script(data: dict) -> Script:
        """Parse script from dictionary."""
```

### `Synthesizer`

```python
from src.services.synthesizer import Synthesizer, LineSynthesisResult

class Synthesizer:
    def __init__(
        self,
        engine: TTSEngine,
        max_retries: int = 3,
        default_speech_rate: float = 1.0,
    ):
        """Initialize synthesizer with TTS engine."""

    def synthesize_line(
        self,
        line: ScriptLine,
        speech_rate_override: Optional[float] = None,
    ) -> LineSynthesisResult:
        """Synthesize a single script line."""

    def synthesize_script(
        self,
        script: Script,
        on_progress: Optional[callable] = None,
    ) -> list[LineSynthesisResult]:
        """Synthesize all lines in a script."""
```

### `AudioStitcher`

```python
from src.services.stitcher import AudioStitcher, StitchResult

class AudioStitcher:
    def __init__(
        self,
        initial_silence_ms: int = 300,
        default_pause_ms: int = 400,
        normalize_dbfs: Optional[float] = -16.0,
        sample_rate: int = 24000,
    ):
        """Initialize audio stitcher."""

    def stitch_from_bytes(
        self,
        audio_data: list[tuple[int, str, str, bytes, int]],
    ) -> StitchResult:
        """
        Stitch audio from raw bytes.

        Args:
            audio_data: List of (line_id, speaker, text, audio_bytes, pause_after_ms)

        Returns:
            StitchResult with combined audio and segments
        """

    def export_mp3(self, audio: AudioSegment, path: str, bitrate: str = "128k"):
        """Export audio to MP3 file."""

    def export_wav(self, audio: AudioSegment, path: str):
        """Export audio to WAV file."""
```

---

## Utilities

### SRT Generation

```python
from src.utils.srt import generate_srt, ms_to_srt_time

def ms_to_srt_time(ms: int) -> str:
    """Convert milliseconds to SRT timestamp (HH:MM:SS,mmm)."""

def generate_srt(segments: list[Segment]) -> str:
    """Generate SRT content from segments."""

def save_srt(content: str, path: str) -> None:
    """Save SRT content to file."""
```

### Audio Utilities

```python
from src.utils.audio import normalize_audio, get_audio_duration

def get_audio_duration(audio_bytes: bytes, format: str = "mp3") -> int:
    """Get audio duration in milliseconds."""

def normalize_audio(audio: AudioSegment, target_dbfs: float = -16.0) -> AudioSegment:
    """Normalize audio to target dBFS level."""

def detect_format(audio_bytes: bytes) -> str:
    """Detect audio format from bytes ('mp3' or 'wav')."""
```

---

## Usage Examples

### Basic Generation

```python
from src.pipeline import Pipeline

pipeline = Pipeline()
result = pipeline.generate("script.json", "output/")

if result.success:
    print(f"Generated: {result.audio_file}")
else:
    print(f"Failed: {result.error}")
```

### Custom Configuration

```python
from src.pipeline import Pipeline
from src.models.config import Config

config = Config()
config.engine = "kokoro"
config.audio.output_format = "wav"
config.synthesis.default_pause_ms = 600

pipeline = Pipeline(config=config)
result = pipeline.generate("script.json", "output/")
```

### Progress Callback

```python
def on_progress(current: int, total: int, result):
    print(f"Progress: {current}/{total} - {result.line.text[:30]}...")

pipeline = Pipeline()
result = pipeline.generate("script.json", "output/", on_progress=on_progress)
```

### Direct Engine Usage

```python
from src.engines.edge import EdgeTTSEngine

engine = EdgeTTSEngine()
result = engine.synthesize(
    text="Hello, world!",
    voice="female_us_1",
    emotion="cheerful",
    speed=1.0
)

if result.success:
    with open("hello.mp3", "wb") as f:
        f.write(result.audio_bytes)
```

### Batch Processing

```python
from pathlib import Path
from src.pipeline import Pipeline

pipeline = Pipeline()

for script in Path("scripts").glob("*.json"):
    result = pipeline.generate(script, "output/")
    print(f"{script.name}: {'OK' if result.success else result.error}")

pipeline.cleanup()
```
