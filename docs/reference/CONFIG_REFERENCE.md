# Configuration Reference

Complete reference for all configuration options.

## Configuration File Format

Configuration files use YAML format. Default location: `config/default.yaml`

```yaml
# config/default.yaml
engine: "edge"

edge:
  default_voice: "en-US-AriaNeural"
  voices:
    female_us_1: "en-US-AriaNeural"

kokoro:
  model_path: "./models/kokoro-v1.0.onnx"
  voices_path: "./models/voices-v1.0.bin"

audio:
  sample_rate: 24000
  normalize_to: -16
  output_format: "mp3"

synthesis:
  default_pause_ms: 400
  initial_silence_ms: 300
  max_retries: 3
```

---

## Top-Level Options

### `engine`

TTS engine to use.

| Property | Value |
|----------|-------|
| Type | string |
| Required | No |
| Default | `"edge"` |
| Valid Values | `"edge"`, `"kokoro"` |

```yaml
engine: "edge"
```

---

## Edge TTS Configuration

### `edge.default_voice`

Default voice when speaker not found in mapping.

| Property | Value |
|----------|-------|
| Type | string |
| Required | No |
| Default | `"en-US-AriaNeural"` |

```yaml
edge:
  default_voice: "en-US-AriaNeural"
```

### `edge.voices`

Speaker ID to Edge TTS voice mapping.

| Property | Value |
|----------|-------|
| Type | object |
| Required | No |

```yaml
edge:
  voices:
    female_us_1: "en-US-AriaNeural"
    female_us_2: "en-US-JennyNeural"
    male_us_1: "en-US-GuyNeural"
    male_us_2: "en-US-ChristopherNeural"
    # Custom mappings
    teacher: "en-US-AriaNeural"
    student: "en-US-GuyNeural"
```

---

## Kokoro-ONNX Configuration

### `kokoro.model_path`

Path to the ONNX model file.

| Property | Value |
|----------|-------|
| Type | string |
| Required | No |
| Default | `"./models/kokoro-v1.0.onnx"` |

```yaml
kokoro:
  model_path: "./models/kokoro-v1.0.onnx"
```

### `kokoro.voices_path`

Path to the voices binary file.

| Property | Value |
|----------|-------|
| Type | string |
| Required | No |
| Default | `"./models/voices-v1.0.bin"` |

```yaml
kokoro:
  voices_path: "./models/voices-v1.0.bin"
```

### `kokoro.default_voice`

Default voice when speaker not found in mapping.

| Property | Value |
|----------|-------|
| Type | string |
| Required | No |
| Default | `"af_heart"` |

```yaml
kokoro:
  default_voice: "af_heart"
```

### `kokoro.voices`

Speaker ID to Kokoro voice mapping.

| Property | Value |
|----------|-------|
| Type | object |
| Required | No |

```yaml
kokoro:
  voices:
    female_us_1: "af_heart"
    female_us_2: "af_bella"
    male_us_1: "am_adam"
    male_us_2: "am_michael"
```

---

## Audio Configuration

### `audio.sample_rate`

Audio sample rate in Hz.

| Property | Value |
|----------|-------|
| Type | integer |
| Required | No |
| Default | `24000` |
| Common Values | 22050, 24000, 44100, 48000 |

```yaml
audio:
  sample_rate: 24000
```

### `audio.normalize_to`

Audio normalization target in dBFS.

| Property | Value |
|----------|-------|
| Type | integer or null |
| Required | No |
| Default | `-16` |
| Range | -60 to 0 |

```yaml
audio:
  normalize_to: -16    # Normalize to -16 dBFS
  # normalize_to: null  # Disable normalization
```

### `audio.output_format`

Output audio format.

| Property | Value |
|----------|-------|
| Type | string |
| Required | No |
| Default | `"mp3"` |
| Valid Values | `"mp3"`, `"wav"` |

```yaml
audio:
  output_format: "mp3"
```

---

## Synthesis Configuration

### `synthesis.default_pause_ms`

Default pause between lines in milliseconds.

| Property | Value |
|----------|-------|
| Type | integer |
| Required | No |
| Default | `400` |
| Range | 0-10000 |

```yaml
synthesis:
  default_pause_ms: 400
```

### `synthesis.initial_silence_ms`

Silence at the beginning of audio in milliseconds.

| Property | Value |
|----------|-------|
| Type | integer |
| Required | No |
| Default | `300` |
| Range | 0-5000 |

```yaml
synthesis:
  initial_silence_ms: 300
```

### `synthesis.max_retries`

Maximum retry attempts for failed synthesis.

| Property | Value |
|----------|-------|
| Type | integer |
| Required | No |
| Default | `3` |
| Range | 1-10 |

```yaml
synthesis:
  max_retries: 3
```

---

## Complete Default Configuration

```yaml
# TTS Engine
engine: "edge"

# Edge TTS Configuration
edge:
  default_voice: "en-US-AriaNeural"
  voices:
    female_us_1: "en-US-AriaNeural"
    female_us_2: "en-US-JennyNeural"
    male_us_1: "en-US-GuyNeural"
    male_us_2: "en-US-ChristopherNeural"
    male_uk_1: "en-GB-RyanNeural"
    female_uk_1: "en-GB-SoniaNeural"

# Kokoro-ONNX Configuration
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

# Audio Output
audio:
  sample_rate: 24000
  normalize_to: -16
  output_format: "mp3"

# Synthesis
synthesis:
  default_pause_ms: 400
  initial_silence_ms: 300
  max_retries: 3
```

---

## Configuration Profiles

### High Quality (Local)

```yaml
engine: "kokoro"

kokoro:
  model_path: "./models/kokoro-v1.0.onnx"
  voices_path: "./models/voices-v1.0.bin"

audio:
  output_format: "wav"
  normalize_to: -16

synthesis:
  default_pause_ms: 500
  initial_silence_ms: 400
```

### Fast Preview (Cloud)

```yaml
engine: "edge"

audio:
  output_format: "mp3"

synthesis:
  default_pause_ms: 300
  initial_silence_ms: 200
  max_retries: 1
```

### Beginner Learners

```yaml
engine: "edge"

synthesis:
  default_pause_ms: 800
  initial_silence_ms: 500
```

### Advanced Learners

```yaml
engine: "edge"

synthesis:
  default_pause_ms: 300
  initial_silence_ms: 200
```

---

## Loading Configuration

### CLI

```bash
# Use specific config file
python main.py generate script.json -c config/custom.yaml -o output/

# Generate default config
python main.py init-config -o config/my-config.yaml
```

### Python API

```python
import yaml
from src.models.config import Config

# From file
with open("config/custom.yaml", "r") as f:
    config_data = yaml.safe_load(f)
config = Config.from_dict(config_data)

# Programmatic
config = Config()
config.engine = "kokoro"
config.audio.output_format = "wav"
```

---

## Environment-Specific Configurations

Create separate config files for different environments:

```
config/
├── default.yaml      # Default settings
├── development.yaml  # Fast iteration
├── staging.yaml      # Testing
└── production.yaml   # Final output
```

Use environment-specific configs:

```bash
# Development
python main.py generate script.json -c config/development.yaml -o output/

# Production
python main.py generate script.json -c config/production.yaml -o output/
```
