# Custom Voices

Configure voice mappings and use custom voices in your scripts.

## Understanding Voice Mappings

The generator uses abstract speaker IDs that map to engine-specific voices:

```
Script Speaker ID → Voice Mapping → Engine Voice
"female_us_1"    → config lookup  → "en-US-AriaNeural"
```

This allows scripts to be engine-agnostic.

## Default Voice Mappings

### Edge TTS (Cloud)

| Speaker ID | Edge Voice | Description |
|------------|------------|-------------|
| `female_us_1` | en-US-AriaNeural | Friendly, versatile |
| `female_us_2` | en-US-JennyNeural | Conversational |
| `male_us_1` | en-US-GuyNeural | Casual, friendly |
| `male_us_2` | en-US-ChristopherNeural | Professional |
| `female_uk_1` | en-GB-SoniaNeural | Warm, professional |
| `male_uk_1` | en-GB-RyanNeural | Friendly |

### Kokoro-ONNX (Local)

| Speaker ID | Kokoro Voice | Description |
|------------|--------------|-------------|
| `female_us_1` | af_heart | Warm, friendly |
| `female_us_2` | af_bella | Clear, professional |
| `female_us_3` | af_nicole | Young, energetic |
| `female_us_4` | af_sarah | Calm, mature |
| `male_us_1` | am_adam | Deep, authoritative |
| `male_us_2` | am_michael | Friendly, casual |
| `female_uk_1` | bf_emma | Clear, warm |
| `male_uk_1` | bm_george | Professional |

## Customizing Voice Mappings

### Method 1: Configuration File

Create or edit `config/default.yaml`:

```yaml
engine: "edge"

edge:
  default_voice: "en-US-AriaNeural"
  voices:
    # Standard mappings
    female_us_1: "en-US-AriaNeural"
    female_us_2: "en-US-JennyNeural"
    male_us_1: "en-US-GuyNeural"
    male_us_2: "en-US-ChristopherNeural"

    # Custom character mappings
    teacher: "en-US-AriaNeural"
    student: "en-US-GuyNeural"
    narrator: "en-GB-SoniaNeural"
    boss: "en-US-ChristopherNeural"
    receptionist: "en-US-JennyNeural"
```

Use custom config:
```bash
python main.py generate script.json -c config/default.yaml -o output/
```

### Method 2: Direct Voice Names in Scripts

Specify the voice directly in your script:

```json
{
  "id": 1,
  "speaker": "custom_character",
  "voice": "en-US-AriaNeural",
  "text": "Hello, I'm a custom character!"
}
```

The `voice` field overrides the speaker mapping.

### Method 3: Python API

```python
from src.engines.edge import EdgeTTSEngine
from src.pipeline import Pipeline

# Custom voice mappings
custom_voices = {
    "teacher": "en-US-AriaNeural",
    "student_1": "en-US-GuyNeural",
    "student_2": "en-US-JennyNeural",
}

engine = EdgeTTSEngine(custom_voices=custom_voices)
pipeline = Pipeline(engine)

result = pipeline.generate("script.json", "output/")
```

## Discovering Available Voices

### Edge TTS Voices

List all available Edge TTS voices:

```bash
python main.py voices --engine edge
```

Or use the CLI tool directly:
```bash
edge-tts --list-voices | grep "en-"
```

Filter by language:
```bash
python main.py voices --engine edge --language en
```

### Kokoro-ONNX Voices

```bash
python main.py voices --engine kokoro
```

## Voice Selection Guide

### By Use Case

| Use Case | Recommended Voice (Edge) |
|----------|-------------------------|
| General narration | en-US-AriaNeural |
| Professional/Business | en-US-ChristopherNeural |
| Casual conversation | en-US-GuyNeural |
| Young character | en-US-JennyNeural |
| British accent | en-GB-SoniaNeural |
| News/Formal | en-US-AriaNeural |

### By Character Type

```yaml
# config/characters.yaml
edge:
  voices:
    # Professional characters
    ceo: "en-US-ChristopherNeural"
    manager: "en-US-AriaNeural"

    # Casual characters
    friend_male: "en-US-GuyNeural"
    friend_female: "en-US-JennyNeural"

    # Service workers
    waiter: "en-US-GuyNeural"
    receptionist: "en-US-JennyNeural"

    # Teachers/Authority
    teacher: "en-US-AriaNeural"
    professor: "en-US-ChristopherNeural"

    # Narration
    narrator: "en-GB-SoniaNeural"
    announcer: "en-US-ChristopherNeural"
```

## Multi-Language Support

### Edge TTS Language Voices

```yaml
edge:
  voices:
    # English (US)
    english_female: "en-US-AriaNeural"
    english_male: "en-US-GuyNeural"

    # English (UK)
    british_female: "en-GB-SoniaNeural"
    british_male: "en-GB-RyanNeural"

    # English (Australia)
    australian_female: "en-AU-NatashaNeural"
    australian_male: "en-AU-WilliamNeural"
```

List all English voices:
```bash
edge-tts --list-voices | grep "en-"
```

## Creating Voice Profiles

### Profile for Business English

```yaml
# config/business.yaml
engine: "edge"

edge:
  default_voice: "en-US-AriaNeural"
  voices:
    interviewer: "en-US-AriaNeural"
    candidate: "en-US-GuyNeural"
    manager: "en-US-ChristopherNeural"
    colleague: "en-US-JennyNeural"
    client: "en-GB-RyanNeural"
```

### Profile for Casual Conversation

```yaml
# config/casual.yaml
engine: "edge"

edge:
  default_voice: "en-US-JennyNeural"
  voices:
    friend_1: "en-US-JennyNeural"
    friend_2: "en-US-GuyNeural"
    friend_3: "en-US-AriaNeural"
    stranger: "en-US-ChristopherNeural"
```

### Using Profiles

```bash
# Business profile
python main.py generate interview.json -c config/business.yaml -o output/

# Casual profile
python main.py generate chat.json -c config/casual.yaml -o output/
```

## Mixing Engines

Use different engines for different scripts:

```bash
# Fast preview with Edge TTS
python main.py generate script.json --engine edge -o preview/

# High-quality final with Kokoro
python main.py generate script.json --engine kokoro -o final/
```

## Troubleshooting

### "Unknown speaker" Warning

The speaker ID isn't in the voice mapping. Solutions:

1. Add it to your config file
2. Use the `voice` field in the script line
3. Use a default speaker ID

### Voice Sounds Wrong

Try a different voice that better matches your character:

```bash
# List all voices to find alternatives
edge-tts --list-voices | grep "en-US"
```

### Inconsistent Character Voice

Ensure the same speaker ID is used throughout:

```json
{
  "lines": [
    {"id": 1, "speaker": "sarah", "text": "Line 1"},
    {"id": 2, "speaker": "sarah", "text": "Line 2"},  // Same speaker
    {"id": 3, "speaker": "Sara", "text": "Line 3"}    // Wrong! Different ID
  ]
}
```

## Next Steps

- [Voice Reference](../reference/VOICE_REFERENCE.md) - Complete voice list
- [Configuration](CONFIGURATION.md) - All config options
- [Creating Scripts](CREATING_SCRIPTS.md) - Script best practices
