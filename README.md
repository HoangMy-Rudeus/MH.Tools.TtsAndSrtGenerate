# TTS & SRT Generator

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Batch lesson generator that converts scripted English conversations into synchronized audio and SRT transcripts using Coqui XTTS v2. Optimized for B2-level listening practice with natural US accent voices.

## Features

- **High-Quality TTS**: Uses Coqui XTTS v2 for natural, human-like speech synthesis
- **Voice Cloning**: Clone any voice from a 6-12 second reference audio sample
- **Multi-Speaker Support**: Create conversations with multiple distinct voices
- **Emotion Control**: Adjust speech style (neutral, friendly, cheerful, serious, excited)
- **Synchronized Output**: Generates audio + SRT subtitles + JSON timeline
- **Forced Alignment**: Uses Whisper for accurate timestamp synchronization
- **Quality Assurance**: Built-in voice consistency checking and validation

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/your-org/TtsAndSrtGenerate.git
cd TtsAndSrtGenerate

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Add Voice Samples

Place 6-12 second `.wav` files in the `voices/` directory:

```
voices/
  male_us_1.wav      # Male US accent reference
  female_us_1.wav    # Female US accent reference
```

**Voice sample requirements:**
- Duration: 6-12 seconds
- Format: WAV, mono, 24kHz recommended
- Quality: Clean audio, no background noise

### Generate Your First Lesson

```bash
# Generate from sample script
python main.py generate examples/sample_script.json -o ./output

# Output files:
# ./output/coffee_shop_001.mp3   - Final audio
# ./output/coffee_shop_001.srt   - Subtitles
# ./output/coffee_shop_001.json  - Timeline data
```

## Usage

### CLI Commands

```bash
# Generate audio lesson from script
python main.py generate <script.json> -o <output_dir>

# Validate script without generating
python main.py validate <script.json>

# List available voices
python main.py list-voices

# Show help
python main.py --help
```

### Command Options

| Option | Description | Default |
|--------|-------------|---------|
| `-o, --output` | Output directory | `./output` |
| `-c, --config` | Config file path | `config/default.yaml` |
| `-v, --verbose` | Enable debug logging | `false` |

### Programmatic Usage

```python
from src.pipeline import LessonPipeline
import json

# Initialize pipeline
pipeline = LessonPipeline.from_config_file("config/default.yaml")

# Load script
with open("script.json") as f:
    script = json.load(f)

# Generate lesson
result = pipeline.generate(script, output_dir="./output")

print(f"Audio: {result.audio_file}")
print(f"Duration: {result.duration_ms / 1000:.1f}s")
print(f"Quality: {result.metadata.quality_score:.2f}")
```

## Script Format

Scripts are JSON files defining the conversation:

```json
{
  "lesson_id": "coffee_shop_001",
  "title": "At the Coffee Shop",
  "level": "B2",
  "lines": [
    {
      "id": 1,
      "speaker": "male_us_1",
      "text": "Hi, can I get a large latte please?",
      "emotion": "friendly",
      "pause_after_ms": 600
    },
    {
      "id": 2,
      "speaker": "female_us_1",
      "text": "Sure! Would you like any flavor shots?",
      "emotion": "cheerful",
      "pause_after_ms": 800
    }
  ],
  "settings": {
    "speech_rate": 1.0,
    "initial_silence_ms": 500,
    "default_pause_ms": 400
  }
}
```

### Script Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `lesson_id` | string | Yes | Unique identifier for output files |
| `title` | string | Yes | Lesson title |
| `level` | string | No | Language level (default: "B2") |
| `lines` | array | Yes | Array of dialogue lines |
| `settings` | object | No | Global synthesis settings |

### Line Fields

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `id` | integer | Yes | - | Unique line identifier |
| `speaker` | string | Yes | - | Voice ID from registry |
| `text` | string | Yes | - | Text to synthesize |
| `emotion` | string | No | "neutral" | Speech emotion style |
| `pause_after_ms` | integer | No | 400 | Pause after line (0-5000ms) |
| `speech_rate` | float | No | 1.0 | Speech speed (0.5-1.5) |

### Supported Emotions

| Emotion | Speed Modifier | Use Case |
|---------|---------------|----------|
| `neutral` | 1.0x | Default, statements |
| `friendly` | 1.0x | Casual conversation |
| `cheerful` | 1.05x | Happy, excited |
| `serious` | 0.95x | Important information |
| `excited` | 1.1x | High energy |

## Output Files

### Audio (MP3)

- Format: MP3, 192kbps
- Sample rate: 24kHz
- Normalized to -16 LUFS

### Subtitles (SRT)

Standard SRT format with millisecond precision:

```srt
1
00:00:00,500 --> 00:00:02,850
Hi, can I get a large latte please?

2
00:00:03,450 --> 00:00:06,200
Sure! Would you like any flavor shots?
```

### Timeline (JSON)

Detailed timing and metadata for playback synchronization:

```json
{
  "lesson_id": "coffee_shop_001",
  "audio_file": "output/coffee_shop_001.mp3",
  "srt_file": "output/coffee_shop_001.srt",
  "duration_ms": 25000,
  "segments": [
    {
      "id": 1,
      "speaker": "male_us_1",
      "text": "Hi, can I get a large latte please?",
      "start_ms": 500,
      "end_ms": 2850,
      "confidence": 0.95
    }
  ],
  "metadata": {
    "model_version": "xtts_v2",
    "generated_at": "2025-01-15T10:30:00Z",
    "quality_score": 0.93
  }
}
```

## Configuration

Configuration is managed via YAML files. See `config/default.yaml`:

```yaml
tts:
  model: "xtts_v2"
  device: "cuda"  # or "cpu"

audio:
  sample_rate: 24000
  output_format: "mp3"
  mp3_bitrate: 192
  normalization_target: -16

synthesis:
  temperature: 0.7
  repetition_penalty: 2.0
  default_pause_ms: 400

alignment:
  enabled: true
  drift_threshold_ms: 200

voice_check:
  enabled: true
  similarity_threshold: 0.85

retry:
  max_attempts: 3
```

## Project Structure

```
TtsAndSrtGenerate/
├── src/
│   ├── models/          # Data models (Pydantic)
│   │   ├── script.py    # Input/output schemas
│   │   └── config.py    # Configuration models
│   ├── services/        # Core services
│   │   ├── validator.py # Script validation
│   │   ├── tts_worker.py    # XTTS synthesis
│   │   ├── stitcher.py      # Audio concatenation
│   │   ├── aligner.py       # Whisper alignment
│   │   └── voice_checker.py # Voice consistency
│   ├── pipeline/        # Orchestration
│   │   └── lesson_pipeline.py
│   └── utils/           # Utilities
│       ├── audio.py     # Audio processing
│       └── srt.py       # SRT generation
├── voices/              # Voice reference files
├── config/              # Configuration files
├── examples/            # Sample scripts
├── tests/               # Unit tests
├── main.py              # CLI entry point
└── requirements.txt
```

## Requirements

- Python 3.10+
- CUDA (recommended) or CPU
- ~4GB VRAM for XTTS v2

### Dependencies

- `TTS>=0.22.0` - Coqui TTS (XTTS v2)
- `torch>=2.0.0` - PyTorch
- `pydub>=0.25.1` - Audio processing
- `openai-whisper>=20231117` - Forced alignment
- `pydantic>=2.0` - Data validation

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test file
pytest tests/test_validator.py
```

## Troubleshooting

### Common Issues

**"Voice not found" error**
- Ensure voice `.wav` files are in `voices/` directory
- File names become voice IDs (e.g., `male_us_1.wav` → speaker: `male_us_1`)

**CUDA out of memory**
- Set `device: "cpu"` in config
- Or use a smaller batch of lines

**Poor audio quality**
- Use clean 6-12s voice reference samples
- Reduce `temperature` for more consistent output
- Check `quality_score` in output JSON

**Timestamp drift**
- Enable alignment in config (`alignment.enabled: true`)
- Check Whisper is installed correctly

## License

MIT License - see [LICENSE](LICENSE) for details.
