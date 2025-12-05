# Configuration Reference

Complete reference for all configuration options in TTS & SRT Generator.

---

## Configuration File

Configuration is stored in YAML format. Default location: `config/default.yaml`

```yaml
# config/default.yaml - Complete example with all options

tts:
  model: "xtts_v2"
  model_path: "./models/xtts_v2"
  device: "cuda"

audio:
  sample_rate: 24000
  output_format: "mp3"
  mp3_bitrate: 192
  normalization_target: -16

synthesis:
  temperature: 0.7
  repetition_penalty: 2.0
  default_pause_ms: 400
  initial_silence_ms: 300

alignment:
  enabled: true
  drift_threshold_ms: 200
  wer_threshold: 0.10

voice_check:
  enabled: true
  similarity_threshold: 0.85

retry:
  max_attempts: 3
  fallback_model: "vits"

voices:
  directory: "./voices"
```

---

## TTS Configuration

Controls the text-to-speech engine.

```yaml
tts:
  model: "xtts_v2"
  model_path: "./models/xtts_v2"
  device: "cuda"
```

### `model`
**Type**: string
**Default**: `"xtts_v2"`

The TTS model to use for synthesis.

| Value | Description |
|-------|-------------|
| `xtts_v2` | Coqui XTTS v2 - Best quality, voice cloning |

### `model_path`
**Type**: string
**Default**: `"./models/xtts_v2"`

Path to model files. Used for custom/local models.

### `device`
**Type**: `"cuda"` or `"cpu"`
**Default**: `"cuda"`

Compute device for model inference.

| Value | Description | Speed |
|-------|-------------|-------|
| `cuda` | NVIDIA GPU acceleration | Fast (~2-3s per line) |
| `cpu` | CPU processing | Slow (~10-15s per line) |

**Note**: Falls back to CPU automatically if CUDA is unavailable.

---

## Audio Configuration

Controls audio output format and quality.

```yaml
audio:
  sample_rate: 24000
  output_format: "mp3"
  mp3_bitrate: 192
  normalization_target: -16
```

### `sample_rate`
**Type**: integer
**Default**: `24000`

Output sample rate in Hz. XTTS v2 native rate is 24kHz.

| Value | Use Case |
|-------|----------|
| `24000` | Default, high quality |
| `22050` | Standard speech |
| `16000` | Telephony quality |

### `output_format`
**Type**: `"mp3"` or `"wav"`
**Default**: `"mp3"`

Final audio output format.

| Value | Size | Quality | Use Case |
|-------|------|---------|----------|
| `mp3` | Small | Good | Web, mobile |
| `wav` | Large | Lossless | Editing, archival |

### `mp3_bitrate`
**Type**: integer
**Default**: `192`

MP3 encoding bitrate in kbps.

| Value | Quality | File Size |
|-------|---------|-----------|
| `128` | Acceptable | ~1 MB/min |
| `192` | Good | ~1.5 MB/min |
| `256` | High | ~2 MB/min |
| `320` | Highest | ~2.5 MB/min |

### `normalization_target`
**Type**: integer
**Default**: `-16`

Target loudness in LUFS (Loudness Units Full Scale).

| Value | Use Case |
|-------|----------|
| `-14` | Streaming platforms (Spotify, YouTube) |
| `-16` | Broadcast standard |
| `-23` | EBU R128 (European broadcast) |

---

## Synthesis Configuration

Controls voice synthesis parameters.

```yaml
synthesis:
  temperature: 0.7
  repetition_penalty: 2.0
  default_pause_ms: 400
  initial_silence_ms: 300
```

### `temperature`
**Type**: float
**Default**: `0.7`
**Range**: `0.1` - `1.0`

Controls randomness in generation. Lower = more consistent, higher = more varied.

| Value | Effect |
|-------|--------|
| `0.3-0.5` | Very consistent, may sound robotic |
| `0.6-0.7` | Balanced (recommended) |
| `0.8-1.0` | More varied, may have artifacts |

**Tip**: Lower temperature if you get repetition or artifacts.

### `repetition_penalty`
**Type**: float
**Default**: `2.0`
**Range**: `1.0` - `5.0`

Penalty for repeating tokens. Higher = less repetition.

| Value | Effect |
|-------|--------|
| `1.0` | No penalty |
| `2.0` | Standard (recommended) |
| `3.0+` | Strong penalty, may affect flow |

### `default_pause_ms`
**Type**: integer
**Default**: `400`
**Range**: `0` - `5000`

Default pause between lines in milliseconds.

| Value | Effect |
|-------|--------|
| `200-300` | Quick dialogue |
| `400-500` | Natural conversation |
| `600-800` | Deliberate pacing |
| `1000+` | Topic changes |

### `initial_silence_ms`
**Type**: integer
**Default**: `300`
**Range**: `0` - `2000`

Silence at the start of the audio.

---

## Alignment Configuration

Controls forced alignment for timestamp accuracy.

```yaml
alignment:
  enabled: true
  drift_threshold_ms: 200
  wer_threshold: 0.10
```

### `enabled`
**Type**: boolean
**Default**: `true`

Enable/disable Whisper forced alignment.

| Value | Effect |
|-------|--------|
| `true` | Timestamps adjusted based on ASR |
| `false` | Use estimated timestamps only |

### `drift_threshold_ms`
**Type**: integer
**Default**: `200`
**Range**: `50` - `500`

Maximum allowed timestamp drift before correction.

| Value | Behavior |
|-------|----------|
| `100` | Strict - correct small drifts |
| `200` | Standard - balance accuracy/stability |
| `300+` | Lenient - only correct large drifts |

### `wer_threshold`
**Type**: float
**Default**: `0.10`
**Range**: `0.0` - `1.0`

Word Error Rate threshold for regeneration.

| Value | Meaning |
|-------|---------|
| `0.05` | 5% error rate triggers flag |
| `0.10` | 10% error rate (recommended) |
| `0.20` | 20% error rate |

---

## Voice Check Configuration

Controls voice consistency validation.

```yaml
voice_check:
  enabled: true
  similarity_threshold: 0.85
```

### `enabled`
**Type**: boolean
**Default**: `true`

Enable/disable voice consistency checking.

### `similarity_threshold`
**Type**: float
**Default**: `0.85`
**Range**: `0.0` - `1.0`

Minimum speaker embedding similarity score.

| Value | Strictness |
|-------|------------|
| `0.75` | Lenient - allows variation |
| `0.85` | Standard (recommended) |
| `0.90` | Strict - very consistent voice |

---

## Retry Configuration

Controls error recovery behavior.

```yaml
retry:
  max_attempts: 3
  fallback_model: "vits"
```

### `max_attempts`
**Type**: integer
**Default**: `3`
**Range**: `1` - `10`

Maximum synthesis retry attempts per line.

### `fallback_model`
**Type**: string
**Default**: `"vits"`

Model to use if primary model fails repeatedly.

---

## Voices Configuration

Controls voice file location.

```yaml
voices:
  directory: "./voices"
```

### `directory`
**Type**: string
**Default**: `"./voices"`

Path to directory containing voice reference `.wav` files.

---

## Using Custom Configurations

### Method 1: Config File

```bash
python main.py generate script.json -c config/production.yaml
```

### Method 2: Environment-Specific Configs

Create multiple config files:

```
config/
  default.yaml      # Development
  production.yaml   # Production (CPU, high quality)
  fast.yaml         # Quick preview (lower quality)
```

**config/fast.yaml**:
```yaml
tts:
  device: "cuda"

synthesis:
  temperature: 0.5

alignment:
  enabled: false

voice_check:
  enabled: false
```

### Method 3: Programmatic

```python
from src.models.config import AppConfig, TTSConfig

config = AppConfig(
    tts=TTSConfig(device="cpu"),
    # ... other settings
)

pipeline = LessonPipeline(config)
```

---

## Recommended Configurations

### High Quality (Production)

```yaml
tts:
  device: "cuda"

audio:
  output_format: "mp3"
  mp3_bitrate: 256
  normalization_target: -14

synthesis:
  temperature: 0.6
  repetition_penalty: 2.0

alignment:
  enabled: true
  drift_threshold_ms: 150

voice_check:
  enabled: true
  similarity_threshold: 0.88

retry:
  max_attempts: 5
```

### Fast Preview

```yaml
tts:
  device: "cuda"

audio:
  output_format: "mp3"
  mp3_bitrate: 128

synthesis:
  temperature: 0.7

alignment:
  enabled: false

voice_check:
  enabled: false

retry:
  max_attempts: 1
```

### CPU-Only (No GPU)

```yaml
tts:
  device: "cpu"

synthesis:
  temperature: 0.5  # Lower for consistency

alignment:
  enabled: true

retry:
  max_attempts: 2
```
