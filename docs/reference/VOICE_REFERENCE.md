# Voice Reference

Complete list of available voices for each TTS engine.

## Edge TTS Voices (Cloud)

Microsoft Edge TTS provides high-quality neural voices via cloud.

### Default Speaker Mappings

| Speaker ID | Voice Name | Gender | Accent | Style |
|------------|------------|--------|--------|-------|
| `female_us_1` | en-US-AriaNeural | Female | US | Friendly, versatile |
| `female_us_2` | en-US-JennyNeural | Female | US | Conversational |
| `male_us_1` | en-US-GuyNeural | Male | US | Casual, friendly |
| `male_us_2` | en-US-ChristopherNeural | Male | US | Professional |
| `female_uk_1` | en-GB-SoniaNeural | Female | UK | Warm, professional |
| `male_uk_1` | en-GB-RyanNeural | Male | UK | Friendly |

### All US English Voices

| Voice Name | Gender | Style |
|------------|--------|-------|
| en-US-AriaNeural | Female | General, friendly |
| en-US-JennyNeural | Female | Conversational |
| en-US-MichelleNeural | Female | Warm |
| en-US-MonicaNeural | Female | Friendly |
| en-US-SaraNeural | Female | Young |
| en-US-GuyNeural | Male | Casual |
| en-US-ChristopherNeural | Male | Professional |
| en-US-EricNeural | Male | Narrative |
| en-US-JacobNeural | Male | Young |
| en-US-RogerNeural | Male | Deep |

### All UK English Voices

| Voice Name | Gender | Style |
|------------|--------|-------|
| en-GB-SoniaNeural | Female | Professional |
| en-GB-LibbyNeural | Female | Young |
| en-GB-MaisieNeural | Female | Warm |
| en-GB-RyanNeural | Male | Friendly |
| en-GB-ThomasNeural | Male | Deep |

### All Australian English Voices

| Voice Name | Gender | Style |
|------------|--------|-------|
| en-AU-NatashaNeural | Female | Professional |
| en-AU-AnnetteNeural | Female | Friendly |
| en-AU-WilliamNeural | Male | Warm |
| en-AU-DarrenNeural | Male | Friendly |

### All Indian English Voices

| Voice Name | Gender | Style |
|------------|--------|-------|
| en-IN-NeerjaNeural | Female | Professional |
| en-IN-PrabhatNeural | Male | Professional |

### Listing All Voices

```bash
# CLI
python main.py voices --engine edge

# Or using edge-tts directly
edge-tts --list-voices | grep "en-"
```

### Using Edge Voices in Scripts

**Via speaker mapping:**
```json
{
  "speaker": "female_us_1"
}
```

**Direct voice name:**
```json
{
  "speaker": "narrator",
  "voice": "en-US-AriaNeural"
}
```

---

## Kokoro-ONNX Voices (Local)

High-quality local TTS using ONNX runtime.

### Default Speaker Mappings

| Speaker ID | Voice Name | Gender | Accent | Style |
|------------|------------|--------|--------|-------|
| `female_us_1` | af_heart | Female | US | Warm, friendly |
| `female_us_2` | af_bella | Female | US | Clear, professional |
| `female_us_3` | af_nicole | Female | US | Young, energetic |
| `female_us_4` | af_sarah | Female | US | Calm, mature |
| `female_us_5` | af_sky | Female | US | Bright, cheerful |
| `female_us_6` | af_nova | Female | US | Bright |
| `female_us_7` | af_river | Female | US | Calm |
| `female_us_8` | af_alloy | Female | US | Neutral |
| `male_us_1` | am_adam | Male | US | Deep, authoritative |
| `male_us_2` | am_michael | Male | US | Friendly, casual |
| `female_uk_1` | bf_emma | Female | UK | Clear, warm |
| `female_uk_2` | bf_isabella | Female | UK | Elegant |
| `male_uk_1` | bm_george | Male | UK | Professional |
| `male_uk_2` | bm_lewis | Male | UK | Friendly |

### All American Female Voices

| Voice Name | Style | Best For |
|------------|-------|----------|
| af_heart | Warm, friendly | General, conversational |
| af_bella | Clear, professional | Business, tutorials |
| af_nicole | Young, energetic | Youth content, casual |
| af_sarah | Calm, mature | Narration, explanations |
| af_sky | Bright, cheerful | Positive content |
| af_nova | Bright | General purpose |
| af_river | Calm | Relaxed content |
| af_alloy | Neutral | Balanced tone |

### All American Male Voices

| Voice Name | Style | Best For |
|------------|-------|----------|
| am_adam | Deep, authoritative | Professional, serious |
| am_michael | Friendly, casual | Conversational, casual |

### All British Female Voices

| Voice Name | Style | Best For |
|------------|-------|----------|
| bf_emma | Clear, warm | General British content |
| bf_isabella | Elegant | Formal content |

### All British Male Voices

| Voice Name | Style | Best For |
|------------|-------|----------|
| bm_george | Professional | Business, formal |
| bm_lewis | Friendly | Conversational |

### Voice Naming Convention

Kokoro voices follow a pattern:
- `af_` = American Female
- `am_` = American Male
- `bf_` = British Female
- `bm_` = British Male

### Using Kokoro Voices in Scripts

**Via speaker mapping:**
```json
{
  "speaker": "female_us_1"
}
```

**Direct voice name:**
```json
{
  "speaker": "custom",
  "voice": "af_heart"
}
```

---

## Voice Selection Guide

### By Content Type

| Content Type | Recommended Edge | Recommended Kokoro |
|--------------|------------------|-------------------|
| General conversation | en-US-AriaNeural | af_heart |
| Business/Formal | en-US-ChristopherNeural | am_adam |
| Tutorial/Education | en-US-JennyNeural | af_bella |
| Youth/Casual | en-US-SaraNeural | af_nicole |
| Narration | en-GB-SoniaNeural | af_sarah |

### By Character Type

| Character | Edge Voice | Kokoro Voice |
|-----------|------------|--------------|
| Teacher | en-US-AriaNeural | af_bella |
| Student | en-US-GuyNeural | am_michael |
| Professional | en-US-ChristopherNeural | am_adam |
| Friend (Female) | en-US-JennyNeural | af_heart |
| Friend (Male) | en-US-GuyNeural | am_michael |
| British character | en-GB-SoniaNeural | bf_emma |

### By Learner Level

| Level | Speed | Recommended Voices |
|-------|-------|-------------------|
| A1-A2 (Beginner) | 0.8-0.9x | Clear voices (AriaNeural, af_bella) |
| B1-B2 (Intermediate) | 1.0x | Any voice |
| C1-C2 (Advanced) | 1.0-1.2x | Natural voices (GuyNeural, am_michael) |

---

## Custom Voice Mappings

### Configuration File

```yaml
# config/voices.yaml
edge:
  voices:
    # Custom character mappings
    teacher: "en-US-AriaNeural"
    student_1: "en-US-GuyNeural"
    student_2: "en-US-JennyNeural"
    boss: "en-US-ChristopherNeural"
    receptionist: "en-US-SaraNeural"
    british_client: "en-GB-RyanNeural"

kokoro:
  voices:
    teacher: "af_bella"
    student_1: "am_michael"
    student_2: "af_heart"
    boss: "am_adam"
    receptionist: "af_nicole"
    british_client: "bm_george"
```

### Usage

```bash
python main.py generate script.json -c config/voices.yaml -o output/
```

---

## Testing Voices

### Quick Test Script

Create `test_voices.json`:

```json
{
  "lesson_id": "voice_test",
  "title": "Voice Test",
  "lines": [
    {"id": 1, "speaker": "female_us_1", "text": "This is female US voice one."},
    {"id": 2, "speaker": "female_us_2", "text": "This is female US voice two."},
    {"id": 3, "speaker": "male_us_1", "text": "This is male US voice one."},
    {"id": 4, "speaker": "male_us_2", "text": "This is male US voice two."},
    {"id": 5, "speaker": "female_uk_1", "text": "This is female UK voice one."},
    {"id": 6, "speaker": "male_uk_1", "text": "This is male UK voice one."}
  ]
}
```

```bash
python main.py generate test_voices.json -o output/
```

### Python Test

```python
from src.engines.edge import EdgeTTSEngine

engine = EdgeTTSEngine()

for speaker in engine.get_available_voices():
    result = engine.synthesize("Hello, this is a test.", speaker)
    if result.success:
        with open(f"test_{speaker}.mp3", "wb") as f:
            f.write(result.audio_bytes)
        print(f"{speaker}: OK")
```
