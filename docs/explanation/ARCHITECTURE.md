# Architecture Overview

Understanding the design and structure of the TTS & SRT Generator.

## System Overview

The TTS & SRT Generator converts conversation scripts into synchronized audio and subtitle files. It follows a pipeline architecture with pluggable components.

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Input     │────▶│   Validate   │────▶│  Synthesize │
│   Script    │     │   Script     │     │  Per Line   │
└─────────────┘     └──────────────┘     └─────────────┘
                                                │
                                                ▼
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Output    │◀────│   Generate   │◀────│   Stitch    │
│   Files     │     │   SRT/JSON   │     │   Audio     │
└─────────────┘     └──────────────┘     └─────────────┘
```

## Core Components

### Pipeline

The main orchestrator that coordinates all operations.

```
Pipeline
├── Loads and validates scripts
├── Coordinates synthesis of all lines
├── Stitches audio segments
├── Generates output files
└── Handles errors and cleanup
```

**Responsibilities:**
- Script loading and validation
- TTS engine lifecycle management
- Audio generation orchestration
- Output file generation (audio, SRT, timeline)

### TTS Engines

Pluggable text-to-speech engines with a common interface.

```
TTSEngine (Abstract)
├── EdgeTTSEngine (Cloud)
│   └── Microsoft Edge neural voices
└── KokoroTTSEngine (Local)
    └── ONNX-based neural TTS
```

**Interface:**
```python
class TTSEngine(ABC):
    def initialize(self) -> None
    def synthesize(text, voice, emotion, speed) -> SynthesisResult
    def get_available_voices() -> list[str]
    def cleanup(self) -> None
```

### Services

Business logic components that handle specific tasks.

```
Services
├── ScriptValidator
│   └── Validates script structure and content
├── Synthesizer
│   └── Orchestrates TTS synthesis with retries
└── AudioStitcher
    └── Combines audio segments with timing
```

### Models

Data structures used throughout the application.

```
Models
├── Script, ScriptLine, ScriptSettings
│   └── Input script representation
├── Config, EdgeConfig, KokoroConfig
│   └── Configuration data
├── SynthesisResult
│   └── Per-line synthesis output
└── TimelineOutput, Segment
    └── Output timing data
```

## Data Flow

### 1. Input Processing

```
JSON Script File
       │
       ▼
┌─────────────────┐
│ ScriptValidator │
│  .load_script() │
└────────┬────────┘
         │
         ▼
   Script Object
         │
         ▼
┌─────────────────┐
│ ScriptValidator │
│   .validate()   │
└────────┬────────┘
         │
         ▼
  Validated Script
```

### 2. Synthesis Process

```
Script Lines
     │
     ▼ (for each line)
┌──────────────┐
│  Synthesizer │
│  .synthesize │
│    _line()   │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  TTSEngine   │
│ .synthesize()│
└──────┬───────┘
       │
       ▼
SynthesisResult
(audio_bytes, duration_ms)
```

### 3. Audio Assembly

```
List[SynthesisResult]
         │
         ▼
┌─────────────────┐
│  AudioStitcher  │
│ .stitch_from_   │
│     bytes()     │
└────────┬────────┘
         │
         ├── Add initial silence
         ├── Concatenate audio segments
         ├── Add pauses between segments
         └── Normalize audio
         │
         ▼
   StitchResult
   (audio, segments, duration)
```

### 4. Output Generation

```
StitchResult
     │
     ├────────────────┬──────────────────┐
     ▼                ▼                  ▼
┌─────────┐    ┌───────────┐    ┌──────────────┐
│  Export │    │  Generate │    │   Generate   │
│  Audio  │    │    SRT    │    │   Timeline   │
│  File   │    │   File    │    │     JSON     │
└─────────┘    └───────────┘    └──────────────┘
     │                │                  │
     ▼                ▼                  ▼
lesson.mp3    lesson.srt    lesson_timeline.json
```

## Project Structure

```
TtsAndSrtGenerate/
├── main.py                     # CLI entry point
├── config/
│   └── default.yaml            # Default configuration
├── src/
│   ├── __init__.py
│   ├── pipeline.py             # Main pipeline orchestrator
│   ├── models/
│   │   ├── __init__.py
│   │   ├── script.py           # Script data models
│   │   └── config.py           # Configuration models
│   ├── engines/
│   │   ├── __init__.py
│   │   ├── base.py             # TTSEngine abstract class
│   │   ├── edge.py             # Edge TTS implementation
│   │   ├── kokoro.py           # Kokoro TTS implementation
│   │   └── factory.py          # Engine factory
│   ├── services/
│   │   ├── __init__.py
│   │   ├── validator.py        # Script validation
│   │   ├── synthesizer.py      # TTS orchestration
│   │   └── stitcher.py         # Audio assembly
│   └── utils/
│       ├── __init__.py
│       ├── audio.py            # Audio utilities
│       └── srt.py              # SRT generation
├── tests/
│   ├── test_validator.py
│   └── test_srt.py
└── docs/
    └── ...
```

## Design Principles

### 1. Pluggable Engines

TTS engines are interchangeable through a common interface:

```python
# Same code works with any engine
result = engine.synthesize("Hello", "female_us_1")
```

Adding a new engine requires only implementing the `TTSEngine` interface.

### 2. Separation of Concerns

Each component has a single responsibility:
- **Validator**: Script validation only
- **Synthesizer**: TTS orchestration only
- **Stitcher**: Audio assembly only
- **Pipeline**: Coordination only

### 3. Configuration over Code

Behavior is customized through configuration:

```yaml
engine: "edge"
synthesis:
  default_pause_ms: 400
```

No code changes needed for common customizations.

### 4. Error Handling

- Validation errors are collected, not thrown immediately
- Synthesis retries on failure (configurable)
- Graceful degradation where possible

### 5. Type Safety

Dataclasses and type hints throughout:

```python
@dataclass
class SynthesisResult:
    line_id: int
    success: bool
    audio_bytes: Optional[bytes]
    duration_ms: int
```

## Extension Points

### Adding a New TTS Engine

1. Implement `TTSEngine` interface:

```python
class MyTTSEngine(TTSEngine):
    def initialize(self) -> None: ...
    def synthesize(self, text, voice, emotion, speed) -> SynthesisResult: ...
    def get_available_voices(self) -> list[str]: ...
    def cleanup(self) -> None: ...
```

2. Register in factory:

```python
# In factory.py
def create_engine(engine_type: str, config: Config) -> TTSEngine:
    if engine_type == "my_engine":
        return MyTTSEngine(...)
```

### Adding Output Formats

1. Add export method to `AudioStitcher`:

```python
def export_ogg(self, audio: AudioSegment, path: str) -> None:
    audio.export(path, format="ogg")
```

2. Update pipeline to use new format.

### Custom Validation Rules

Extend `ScriptValidator`:

```python
class CustomValidator(ScriptValidator):
    def validate(self, script: Script) -> list[str]:
        errors = super().validate(script)
        # Add custom rules
        if len(script.lines) > 100:
            errors.append("Script too long (max 100 lines)")
        return errors
```

## Performance Considerations

### Edge TTS (Cloud)

- Network latency per line (~200-500ms)
- Parallel synthesis possible but rate-limited
- Best for: Quick previews, development

### Kokoro-ONNX (Local)

- Model loading time (~1-2s first run)
- Per-line synthesis (~0.5-2s depending on length)
- Best for: Production quality, offline use

### Optimization Tips

1. **Batch processing**: Reuse pipeline instance
2. **Parallel synthesis**: Use thread pool for independent scripts
3. **Caching**: Cache synthesized common phrases
4. **Format**: Use MP3 for smaller files, WAV for editing

## Dependencies

```
pydub           ─── Audio processing (requires FFmpeg)
edge-tts        ─── Microsoft Edge TTS
kokoro-onnx     ─── Local neural TTS
click           ─── CLI framework
pyyaml          ─── YAML configuration
soundfile       ─── Audio I/O
numpy           ─── Numerical operations
```

## Future Considerations

- **Streaming synthesis**: Real-time audio generation
- **Caching layer**: Avoid re-synthesizing identical text
- **Additional engines**: Google, Amazon, OpenAI TTS
- **Language support**: Multi-language conversation scripts
- **Audio effects**: Background music, sound effects
