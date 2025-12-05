# API Reference

Complete reference for all modules, classes, and functions in TTS & SRT Generator.

---

## Table of Contents

- [Models](#models)
  - [Script Models](#script-models)
  - [Configuration Models](#configuration-models)
- [Services](#services)
  - [ScriptValidator](#scriptvalidator)
  - [TTSWorker](#ttsworker)
  - [AudioStitcher](#audiostitcher)
  - [AlignmentService](#alignmentservice)
  - [VoiceConsistencyChecker](#voiceconsistencychecker)
- [Pipeline](#pipeline)
  - [LessonPipeline](#lessonpipeline)
- [Utilities](#utilities)
  - [Audio Utils](#audio-utils)
  - [SRT Utils](#srt-utils)

---

## Models

### Script Models

Located in `src/models/script.py`

#### `Emotion`

Enum defining supported emotion types for TTS synthesis.

```python
class Emotion(str, Enum):
    NEUTRAL = "neutral"
    FRIENDLY = "friendly"
    CHEERFUL = "cheerful"
    SERIOUS = "serious"
    EXCITED = "excited"
```

#### `ScriptLine`

Single line of dialogue in a script.

```python
class ScriptLine(BaseModel):
    id: int                           # Unique line identifier
    speaker: str                      # Voice ID from registry
    text: str                         # Text to synthesize (min 1 char)
    emotion: Emotion = "neutral"      # Emotion for synthesis
    pause_after_ms: int = 400         # Pause after line (0-5000ms)
    speech_rate: float | None = None  # Override speech rate (0.5-1.5)
```

**Example:**
```python
line = ScriptLine(
    id=1,
    speaker="male_us_1",
    text="Hello, how are you today?",
    emotion=Emotion.FRIENDLY,
    pause_after_ms=600
)
```

#### `ScriptSettings`

Global settings for script synthesis.

```python
class ScriptSettings(BaseModel):
    speech_rate: float = 1.0          # Default speech rate (0.5-1.5)
    initial_silence_ms: int = 300     # Silence at start (0-2000ms)
    default_pause_ms: int = 400       # Default pause between lines (0-5000ms)
```

#### `ScriptInput`

Complete script input for lesson generation.

```python
class ScriptInput(BaseModel):
    lesson_id: str                    # Unique lesson identifier
    title: str                        # Lesson title
    level: str = "B2"                 # Language level
    lines: list[ScriptLine]           # Dialogue lines (min 1)
    settings: ScriptSettings = ScriptSettings()
```

**Example:**
```python
script = ScriptInput(
    lesson_id="lesson_001",
    title="At the Coffee Shop",
    lines=[
        ScriptLine(id=1, speaker="male_us_1", text="Hello!"),
        ScriptLine(id=2, speaker="female_us_1", text="Hi there!"),
    ]
)
```

#### `Segment`

Audio segment with timing information.

```python
class Segment(BaseModel):
    id: int                           # Line ID from script
    speaker: str                      # Speaker voice ID
    text: str                         # Original text
    start_ms: int                     # Start time in milliseconds
    end_ms: int                       # End time in milliseconds
    audio_duration_ms: int            # Actual audio duration
    confidence: float = 1.0           # Alignment confidence (0.0-1.0)
```

#### `LessonMetadata`

Metadata for generated lesson.

```python
class LessonMetadata(BaseModel):
    model_version: str                # TTS model version used
    generated_at: str                 # ISO timestamp of generation
    quality_score: float = 1.0        # Overall quality score (0.0-1.0)
```

#### `LessonOutput`

Complete output from lesson generation.

```python
class LessonOutput(BaseModel):
    lesson_id: str
    title: str
    audio_file: str                   # Path to generated audio file
    srt_file: str                     # Path to generated SRT file
    duration_ms: int                  # Total audio duration
    segments: list[Segment]           # Timed segments
    metadata: LessonMetadata
```

---

### Configuration Models

Located in `src/models/config.py`

#### `TTSConfig`

TTS engine configuration.

```python
class TTSConfig(BaseModel):
    model: str = "xtts_v2"            # Model name
    model_path: str = "./models/xtts_v2"  # Path to model
    device: Literal["cuda", "cpu"] = "cuda"  # Compute device
```

#### `AudioConfig`

Audio output configuration.

```python
class AudioConfig(BaseModel):
    sample_rate: int = 24000          # Sample rate in Hz
    output_format: Literal["mp3", "wav"] = "mp3"
    mp3_bitrate: int = 192            # MP3 bitrate in kbps
    normalization_target: int = -16   # Target LUFS
```

#### `SynthesisConfig`

Synthesis parameters.

```python
class SynthesisConfig(BaseModel):
    temperature: float = 0.7          # Randomness (0.1-1.0)
    repetition_penalty: float = 2.0   # Repetition penalty (1.0-5.0)
    default_pause_ms: int = 400       # Default pause (0-5000ms)
    initial_silence_ms: int = 300     # Initial silence (0-2000ms)
```

#### `AlignmentConfig`

Forced alignment configuration.

```python
class AlignmentConfig(BaseModel):
    enabled: bool = True
    drift_threshold_ms: int = 200     # Max drift before correction (50-500ms)
    wer_threshold: float = 0.10       # Word error rate threshold (0.0-1.0)
```

#### `VoiceCheckConfig`

Voice consistency check configuration.

```python
class VoiceCheckConfig(BaseModel):
    enabled: bool = True
    similarity_threshold: float = 0.85  # Min similarity score (0.0-1.0)
```

#### `RetryConfig`

Retry strategy configuration.

```python
class RetryConfig(BaseModel):
    max_attempts: int = 3             # Max retry attempts (1-10)
    fallback_model: str = "vits"      # Fallback model name
```

#### `AppConfig`

Complete application configuration.

```python
class AppConfig(BaseModel):
    tts: TTSConfig
    audio: AudioConfig
    synthesis: SynthesisConfig
    alignment: AlignmentConfig
    voice_check: VoiceCheckConfig
    retry: RetryConfig
    voices: VoicesConfig
```

**Methods:**

```python
@classmethod
def from_yaml(cls, path: str | Path) -> "AppConfig":
    """Load configuration from YAML file."""

@classmethod
def default(cls) -> "AppConfig":
    """Create default configuration."""
```

**Example:**
```python
# Load from file
config = AppConfig.from_yaml("config/default.yaml")

# Use defaults
config = AppConfig.default()
```

---

## Services

### ScriptValidator

Located in `src/services/validator.py`

Validates input scripts against schema and content rules.

#### Constructor

```python
def __init__(self, voice_registry: dict[str, Path] | None = None):
    """
    Initialize validator.

    Args:
        voice_registry: Dict mapping voice IDs to reference audio paths
    """
```

#### Methods

##### `validate(script: dict) -> ValidationResult`

Validate script against schema and content rules.

**Checks performed:**
- Required fields present (via Pydantic)
- Speaker IDs exist in voice registry
- Text contains only allowed characters
- Emotion values in allowed set
- Pause values within range
- No duplicate line IDs

**Args:**
- `script`: Raw script dictionary

**Returns:**
- `ValidationResult` with `success`, `errors`, and `warnings`

**Example:**
```python
validator = ScriptValidator(voice_registry={"male_us_1": Path("voices/male_us_1.wav")})

result = validator.validate({
    "lesson_id": "test",
    "title": "Test",
    "lines": [{"id": 1, "speaker": "male_us_1", "text": "Hello"}]
})

if result.success:
    print("Valid!")
else:
    for error in result.errors:
        print(f"Error: {error.field} - {error.message}")
```

##### `validate_file(path: str | Path) -> ValidationResult`

Validate script from JSON file.

---

### TTSWorker

Located in `src/services/tts_worker.py`

Synthesizes audio using Coqui XTTS v2.

#### Constructor

```python
def __init__(
    self,
    tts_config: TTSConfig,
    synthesis_config: SynthesisConfig,
    voice_registry: dict[str, VoiceReference],
):
    """
    Initialize TTS worker.

    Args:
        tts_config: TTS engine configuration
        synthesis_config: Synthesis parameters
        voice_registry: Dict mapping voice IDs to VoiceReference
    """
```

#### Methods

##### `load_model() -> None`

Load XTTS model into memory. Called automatically on first synthesis.

##### `synthesize_line(line: ScriptLine) -> SynthesisResult`

Synthesize a single script line.

**Args:**
- `line`: Script line to synthesize

**Returns:**
- `SynthesisResult` with `audio_bytes`, `duration_ms`, `success`, `error`

**Example:**
```python
from src.models.script import ScriptLine, Emotion

worker = TTSWorker(tts_config, synthesis_config, voice_registry)

result = worker.synthesize_line(ScriptLine(
    id=1,
    speaker="male_us_1",
    text="Hello, world!",
    emotion=Emotion.FRIENDLY
))

if result.success:
    print(f"Duration: {result.duration_ms}ms")
    # result.audio_bytes contains WAV data
```

##### `synthesize_batch(lines: list[ScriptLine]) -> list[SynthesisResult]`

Synthesize multiple lines sequentially.

##### `unload_model() -> None`

Unload model from memory and free GPU resources.

#### Helper Function

##### `load_voice_registry(voices_dir: str | Path) -> dict[str, VoiceReference]`

Load voice registry from directory. Each `.wav` file becomes a voice ID.

```python
# Directory structure:
# voices/
#   male_us_1.wav    -> voice_id: "male_us_1"
#   female_us_1.wav  -> voice_id: "female_us_1"

registry = load_voice_registry("./voices")
```

---

### AudioStitcher

Located in `src/services/stitcher.py`

Concatenates per-line audio with gaps and normalization.

#### Constructor

```python
def __init__(
    self,
    audio_config: AudioConfig,
    synthesis_config: SynthesisConfig,
):
```

#### Methods

##### `stitch(synthesis_results, lines, output_dir, filename_base) -> StitchResult`

Stitch synthesized audio segments together.

**Pipeline:**
1. Add initial silence
2. For each segment: trim silence, add to combined, add pause
3. Normalize final audio to target LUFS
4. Export as WAV and MP3

**Args:**
- `synthesis_results`: List of `SynthesisResult` from TTS worker
- `lines`: Original `ScriptLine` list (for pause metadata)
- `output_dir`: Output directory path
- `filename_base`: Base filename (without extension)

**Returns:**
- `StitchResult` with `wav_path`, `mp3_path`, `total_duration_ms`, `segments`

**Example:**
```python
stitcher = AudioStitcher(audio_config, synthesis_config)

result = stitcher.stitch(
    synthesis_results=tts_results,
    lines=script.lines,
    output_dir="./output",
    filename_base="lesson_001"
)

print(f"Audio: {result.mp3_path}")
print(f"Duration: {result.total_duration_ms}ms")
```

---

### AlignmentService

Located in `src/services/aligner.py`

Adjusts timestamps using Whisper forced alignment.

#### Constructor

```python
def __init__(self, config: AlignmentConfig):
```

#### Methods

##### `align(audio_path, segments, texts) -> AlignmentResult`

Perform forced alignment on audio.

**Args:**
- `audio_path`: Path to combined audio file
- `segments`: List of estimated `SegmentTiming`
- `texts`: Dict mapping `line_id` to text

**Returns:**
- `AlignmentResult` with adjusted segments and drift information

**Example:**
```python
aligner = AlignmentService(alignment_config)

result = aligner.align(
    audio_path="./output/lesson.wav",
    segments=stitch_result.segments,
    texts={1: "Hello", 2: "World"}
)

for seg in result.segments:
    print(f"Line {seg.line_id}: {seg.aligned_start_ms}-{seg.aligned_end_ms}ms")
    print(f"  Drift: {seg.drift_ms}ms, Confidence: {seg.confidence}")
```

---

### VoiceConsistencyChecker

Located in `src/services/voice_checker.py`

Ensures synthesized audio matches reference voice characteristics.

#### Methods

##### `check_consistency(generated_audio, reference_path, sample_rate) -> ConsistencyResult`

Compare generated audio to reference voice using speaker embeddings.

**Args:**
- `generated_audio`: Generated audio as numpy array or WAV bytes
- `reference_path`: Path to reference voice audio
- `sample_rate`: Sample rate of generated audio

**Returns:**
- `ConsistencyResult` with `similarity_score` and `passed` flag

##### `validate_voice_samples(voice_registry, tts_worker) -> dict[str, ConsistencyResult]`

Validate all voice samples before batch processing. Synthesizes a reference phrase with each voice and compares to baseline.

---

## Pipeline

### LessonPipeline

Located in `src/pipeline/lesson_pipeline.py`

Orchestrates the full lesson generation pipeline.

#### Constructor

```python
def __init__(self, config: AppConfig):
    """
    Initialize pipeline with configuration.

    Args:
        config: Application configuration
    """
```

#### Class Methods

##### `from_config_file(config_path: str | Path) -> LessonPipeline`

Create pipeline from config file.

```python
pipeline = LessonPipeline.from_config_file("config/default.yaml")
```

##### `from_default_config() -> LessonPipeline`

Create pipeline with default configuration.

```python
pipeline = LessonPipeline.from_default_config()
```

#### Methods

##### `generate(script: dict, output_dir: str | Path) -> LessonOutput`

Generate lesson from script.

**Pipeline steps:**
1. Validate script
2. Synthesize all lines (with retry on failure)
3. Stitch audio
4. Run forced alignment
5. Generate outputs (audio, SRT, JSON)

**Args:**
- `script`: Script dictionary
- `output_dir`: Output directory

**Returns:**
- `LessonOutput` with paths and metadata

**Raises:**
- `PipelineError`: If pipeline fails

**Example:**
```python
pipeline = LessonPipeline.from_config_file("config/default.yaml")

result = pipeline.generate(
    script={
        "lesson_id": "test",
        "title": "Test Lesson",
        "lines": [
            {"id": 1, "speaker": "male_us_1", "text": "Hello!"}
        ]
    },
    output_dir="./output"
)

print(f"Generated: {result.audio_file}")
print(f"Duration: {result.duration_ms}ms")
print(f"Quality: {result.metadata.quality_score}")
```

##### `generate_from_file(script_path: str | Path, output_dir: str | Path) -> LessonOutput`

Generate lesson from script file.

```python
result = pipeline.generate_from_file("examples/sample_script.json", "./output")
```

---

## Utilities

### Audio Utils

Located in `src/utils/audio.py`

#### Functions

##### `normalize_audio(segment: AudioSegment, target_dbfs: float = -16.0) -> AudioSegment`

Normalize audio to target dBFS level.

##### `add_silence(duration_ms: int, sample_rate: int = 24000) -> AudioSegment`

Create silent audio segment.

##### `trim_silence(segment, silence_thresh=-50.0, min_silence_len=100, keep_silence=50) -> AudioSegment`

Trim silence from start and end of audio.

##### `export_audio(segment, output_path, format="mp3", bitrate="192k") -> Path`

Export audio segment to file.

##### `wav_bytes_to_segment(wav_bytes: bytes) -> AudioSegment`

Convert WAV bytes to pydub AudioSegment.

---

### SRT Utils

Located in `src/utils/srt.py`

#### Functions

##### `format_timestamp(ms: int) -> str`

Format milliseconds as SRT timestamp (`HH:MM:SS,mmm`).

```python
format_timestamp(3661500)  # "01:01:01,500"
```

##### `generate_srt(segments: list[Segment]) -> str`

Generate SRT content from segments.

```python
srt_content = generate_srt(segments)
# Returns:
# 1
# 00:00:00,500 --> 00:00:02,850
# Hello, how are you?
#
# 2
# ...
```

##### `save_srt(segments: list[Segment], output_path: str | Path) -> Path`

Save segments as SRT file.

##### `parse_srt(content: str) -> list[dict]`

Parse SRT content into segment dictionaries.

---

## Exceptions

### `PipelineError`

Raised when pipeline execution fails.

```python
from src.pipeline.lesson_pipeline import PipelineError

try:
    result = pipeline.generate(script, output_dir)
except PipelineError as e:
    print(f"Pipeline failed: {e}")
```
