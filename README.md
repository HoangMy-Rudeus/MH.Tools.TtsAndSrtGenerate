# TTS & SRT Generator

A batch Text-to-Speech application that converts conversation scripts into synchronized audio and subtitle files for English learning.

## Features

- **Multiple TTS Engines**: Support for Edge TTS (cloud, fast, free) and Kokoro-ONNX (local, high quality)
- **SRT Generation**: Automatic subtitle file generation with accurate timestamps
- **Timeline JSON**: Detailed timeline with segment information for integration
- **Batch Processing**: Process multiple scripts in a directory
- **Configurable**: YAML configuration for voices, audio settings, and more

## Installation

```bash
# Clone the repository
cd TtsAndSrtGenerate

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### For Kokoro-ONNX (Local TTS)

```bash
# Install kokoro-onnx
pip install kokoro-onnx

# Download model files
mkdir models
wget -P models https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx
wget -P models https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin
```

## Quick Start

### Generate from a script

```bash
# Using Edge TTS (default, cloud-based)
python main.py generate docs/conversation_1.json -o output/

# Using Kokoro TTS (local, high quality)
python main.py generate docs/conversation_1.json --engine kokoro -o output/
```

### Validate a script

```bash
python main.py validate docs/conversation_1.json
```

### List available voices

```bash
python main.py voices --engine edge
python main.py voices --engine kokoro
```

### Batch processing

```bash
python main.py batch scripts/ -o output/
```

### Generate config file

```bash
python main.py init-config -o config/my-config.yaml
```

## Script Format

Input scripts are JSON files with conversation lines:

```json
{
  "lesson_id": "conversation_001",
  "title": "Office Introduction",
  "language": "en",
  "lines": [
    {
      "id": 1,
      "speaker": "female_us_1",
      "text": "Hi everyone, this is Alex, our new front-end developer.",
      "emotion": "friendly",
      "pause_after_ms": 500
    },
    {
      "id": 2,
      "speaker": "male_us_1",
      "text": "Hello Alex, nice to meet you.",
      "emotion": "neutral"
    }
  ],
  "settings": {
    "speech_rate": 1.0,
    "initial_silence_ms": 500,
    "default_pause_ms": 400
  }
}
```

### Line Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | int | Yes | Unique line identifier |
| `speaker` | string | Yes | Speaker ID (maps to voice) |
| `text` | string | Yes | Text to synthesize |
| `voice` | string | No | Direct voice name (overrides speaker mapping) |
| `emotion` | string | No | Emotion: neutral, friendly, cheerful, serious, excited |
| `pause_after_ms` | int | No | Pause after line (default: 400ms) |
| `speech_rate` | float | No | Speed multiplier (default: 1.0) |

## Output Files

For input `conversation_001.json`, generates:

1. **Audio**: `conversation_001.mp3` - All lines concatenated with pauses
2. **Subtitles**: `conversation_001.srt` - SRT file with timestamps
3. **Timeline**: `conversation_001_timeline.json` - Detailed timing information

## Voice Mappings

### Edge TTS (Cloud)

| Speaker ID | Voice | Description |
|------------|-------|-------------|
| `female_us_1` | en-US-AriaNeural | Friendly, versatile |
| `female_us_2` | en-US-JennyNeural | Conversational |
| `male_us_1` | en-US-GuyNeural | Casual, friendly |
| `male_us_2` | en-US-ChristopherNeural | Professional |
| `female_uk_1` | en-GB-SoniaNeural | Warm, professional |
| `male_uk_1` | en-GB-RyanNeural | Friendly |

### Kokoro-ONNX (Local)

| Speaker ID | Voice | Description |
|------------|-------|-------------|
| `female_us_1` | af_heart | Warm, friendly |
| `female_us_2` | af_bella | Clear, professional |
| `male_us_1` | am_adam | Deep, authoritative |
| `male_us_2` | am_michael | Friendly, casual |
| `female_uk_1` | bf_emma | Clear, warm |
| `male_uk_1` | bm_george | Professional |

## Configuration

Create a `config.yaml` file:

```yaml
engine: "edge"  # or "kokoro"

edge:
  default_voice: "en-US-AriaNeural"
  voices:
    female_us_1: "en-US-AriaNeural"
    male_us_1: "en-US-GuyNeural"

audio:
  output_format: "mp3"  # or "wav"
  normalize_to: -16

synthesis:
  default_pause_ms: 400
  initial_silence_ms: 300
```

## Project Structure

```
tts-generator/
├── main.py                 # CLI entry point
├── config/
│   └── default.yaml        # Default configuration
├── src/
│   ├── models/
│   │   ├── script.py       # Input/output data models
│   │   └── config.py       # Configuration models
│   ├── engines/
│   │   ├── base.py         # TTSEngine abstract class
│   │   ├── edge.py         # Edge TTS implementation
│   │   ├── kokoro.py       # Kokoro TTS implementation
│   │   └── factory.py      # Engine factory
│   ├── services/
│   │   ├── validator.py    # Script validation
│   │   ├── synthesizer.py  # TTS orchestration
│   │   └── stitcher.py     # Audio concatenation
│   ├── utils/
│   │   ├── audio.py        # Audio processing
│   │   └── srt.py          # SRT generation
│   └── pipeline.py         # Main pipeline
├── requirements.txt
└── tests/
```

## Python API

```python
from src.pipeline import Pipeline
from src.engines.factory import create_engine

# Create pipeline with Edge TTS
engine = create_engine("edge")
pipeline = Pipeline(engine)

# Generate from script
result = pipeline.generate(
    script_path="conversation.json",
    output_dir="output/"
)

print(f"Audio: {result.audio_file}")
print(f"SRT: {result.srt_file}")
print(f"Duration: {result.duration_ms}ms")
```

## License

MIT
