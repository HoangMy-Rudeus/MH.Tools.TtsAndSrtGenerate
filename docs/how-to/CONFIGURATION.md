# Configuration

Customize the TTS & SRT Generator settings for your needs.

## Configuration File

Create a configuration file at `config/default.yaml` or any custom location.

### Generate Default Config

```bash
python main.py init-config -o config/my-config.yaml
```

### Use Custom Config

```bash
python main.py generate script.json -c config/my-config.yaml -o output/
```

## Complete Configuration Reference

```yaml
# TTS Engine Selection
# Options: "edge" (cloud, fast) or "kokoro" (local, high quality)
engine: "edge"

# Edge TTS Configuration (Microsoft Cloud TTS)
edge:
  # Default voice when speaker not found in mapping
  default_voice: "en-US-AriaNeural"

  # Speaker ID to voice mapping
  voices:
    female_us_1: "en-US-AriaNeural"
    female_us_2: "en-US-JennyNeural"
    male_us_1: "en-US-GuyNeural"
    male_us_2: "en-US-ChristopherNeural"
    male_uk_1: "en-GB-RyanNeural"
    female_uk_1: "en-GB-SoniaNeural"
    # Add custom mappings here
    teacher: "en-US-AriaNeural"
    student: "en-US-GuyNeural"

# Kokoro-ONNX Configuration (Local TTS)
kokoro:
  # Path to ONNX model file
  model_path: "./models/kokoro-v1.0.onnx"

  # Path to voices binary file
  voices_path: "./models/voices-v1.0.bin"

  # Default voice when speaker not found
  default_voice: "af_heart"

  # Speaker ID to voice mapping
  voices:
    female_us_1: "af_heart"
    female_us_2: "af_bella"
    female_us_3: "af_nicole"
    female_us_4: "af_sarah"
    male_us_1: "am_adam"
    male_us_2: "am_michael"
    female_uk_1: "bf_emma"
    male_uk_1: "bm_george"

# Audio Output Configuration
audio:
  # Sample rate in Hz
  sample_rate: 24000

  # Normalization level in dBFS (use null to disable)
  normalize_to: -16

  # Output format: "mp3" or "wav"
  output_format: "mp3"

# Synthesis Configuration
synthesis:
  # Default pause between lines in milliseconds
  default_pause_ms: 400

  # Silence at the beginning of audio
  initial_silence_ms: 300

  # Maximum retry attempts for failed synthesis
  max_retries: 3
```

## Configuration Sections

### Engine Selection

```yaml
engine: "edge"  # or "kokoro"
```

| Engine | Type | Speed | Quality | Offline |
|--------|------|-------|---------|---------|
| edge | Cloud | Fast | Good | No |
| kokoro | Local | Medium | Excellent | Yes |

### Edge TTS Settings

```yaml
edge:
  default_voice: "en-US-AriaNeural"
  voices:
    speaker_id: "voice-name"
```

### Kokoro Settings

```yaml
kokoro:
  model_path: "./models/kokoro-v1.0.onnx"
  voices_path: "./models/voices-v1.0.bin"
  default_voice: "af_heart"
  voices:
    speaker_id: "kokoro-voice"
```

### Audio Settings

```yaml
audio:
  sample_rate: 24000      # Common: 22050, 24000, 44100, 48000
  normalize_to: -16       # dBFS level, null to disable
  output_format: "mp3"    # "mp3" or "wav"
```

**Normalization:**
- `-16 dBFS`: Standard for speech (recommended)
- `-20 dBFS`: Quieter, more headroom
- `null`: No normalization

### Synthesis Settings

```yaml
synthesis:
  default_pause_ms: 400     # 0-10000
  initial_silence_ms: 300   # 0-5000
  max_retries: 3            # 1-10
```

## Configuration Profiles

### Profile: High Quality

```yaml
# config/high-quality.yaml
engine: "kokoro"

kokoro:
  model_path: "./models/kokoro-v1.0.onnx"
  voices_path: "./models/voices-v1.0.bin"

audio:
  sample_rate: 24000
  normalize_to: -16
  output_format: "wav"  # Lossless

synthesis:
  default_pause_ms: 500
  initial_silence_ms: 400
```

### Profile: Fast Preview

```yaml
# config/preview.yaml
engine: "edge"

audio:
  output_format: "mp3"
  normalize_to: -16

synthesis:
  default_pause_ms: 300
  initial_silence_ms: 200
  max_retries: 1  # Fail fast
```

### Profile: Beginner Learners

```yaml
# config/beginner.yaml
engine: "edge"

audio:
  output_format: "mp3"

synthesis:
  default_pause_ms: 800      # Longer pauses
  initial_silence_ms: 500
```

### Profile: Advanced Learners

```yaml
# config/advanced.yaml
engine: "edge"

audio:
  output_format: "mp3"

synthesis:
  default_pause_ms: 300      # Shorter pauses
  initial_silence_ms: 200
```

## Environment-Specific Configs

### Development

```yaml
# config/development.yaml
engine: "edge"

audio:
  output_format: "mp3"

synthesis:
  max_retries: 1
```

### Production

```yaml
# config/production.yaml
engine: "kokoro"

kokoro:
  model_path: "/opt/models/kokoro-v1.0.onnx"
  voices_path: "/opt/models/voices-v1.0.bin"

audio:
  output_format: "mp3"
  normalize_to: -16

synthesis:
  max_retries: 3
```

## Python Configuration

### Using Config in Code

```python
from src.models.config import Config
from src.pipeline import Pipeline

# Load default config
config = Config()

# Or create custom config
config = Config()
config.engine = "edge"
config.audio.output_format = "wav"
config.synthesis.default_pause_ms = 600

# Use with pipeline
pipeline = Pipeline(config=config)
```

### Loading from YAML

```python
import yaml
from src.models.config import Config

# Load YAML file
with open("config/custom.yaml", "r") as f:
    config_data = yaml.safe_load(f)

# Create config from dict
config = Config.from_dict(config_data)

# Use config
pipeline = Pipeline(config=config)
```

## Overriding Configuration

### Command Line Overrides

```bash
# Override engine
python main.py generate script.json --engine kokoro -o output/

# Override format
python main.py generate script.json --format wav -o output/

# Both
python main.py generate script.json --engine kokoro --format wav -o output/
```

### Script-Level Overrides

Settings in scripts override global config:

```json
{
  "lesson_id": "lesson_001",
  "title": "My Lesson",
  "lines": [...],
  "settings": {
    "speech_rate": 0.9,
    "initial_silence_ms": 600,
    "default_pause_ms": 500
  }
}
```

## Best Practices

1. **Use profiles**: Create configs for different use cases
2. **Version control**: Track config files in git
3. **Document custom mappings**: Comment your voice mappings
4. **Test changes**: Verify audio quality after config changes
5. **Environment separation**: Use different configs for dev/prod

## Troubleshooting

### Config Not Loading

```bash
# Verify config path
python main.py generate script.json -c /full/path/to/config.yaml -o output/
```

### Invalid YAML

Validate your YAML:
```bash
python -c "import yaml; yaml.safe_load(open('config/default.yaml'))"
```

### Voice Not Found

Check speaker is in mapping:
```yaml
edge:
  voices:
    my_speaker: "en-US-AriaNeural"  # Make sure this exists
```

## Next Steps

- [CLI Reference](../reference/CLI_REFERENCE.md) - Command line options
- [Voice Reference](../reference/VOICE_REFERENCE.md) - Available voices
- [Creating Scripts](CREATING_SCRIPTS.md) - Script settings
