# Script Format Reference

Complete specification for conversation script JSON files.

## Overview

Scripts are JSON files that define conversations for TTS generation. Each script contains metadata, conversation lines, and optional settings.

## Schema

```json
{
  "lesson_id": "string (required)",
  "title": "string (required)",
  "language": "string (optional)",
  "level": "string (optional)",
  "lines": [
    {
      "id": "integer (required)",
      "speaker": "string (required)",
      "text": "string (required)",
      "voice": "string (optional)",
      "emotion": "string (optional)",
      "pause_after_ms": "integer (optional)",
      "speech_rate": "float (optional)"
    }
  ],
  "settings": {
    "speech_rate": "float (optional)",
    "initial_silence_ms": "integer (optional)",
    "default_pause_ms": "integer (optional)"
  }
}
```

## Root Fields

### `lesson_id` (required)

Unique identifier for the lesson. Used for output filenames.

| Property | Value |
|----------|-------|
| Type | string |
| Required | Yes |
| Constraints | Alphanumeric, underscores, hyphens only |

**Examples:**
```json
"lesson_id": "greeting_001"
"lesson_id": "unit-1-lesson-3"
"lesson_id": "coffee_shop_conversation"
```

---

### `title` (required)

Human-readable title for the lesson.

| Property | Value |
|----------|-------|
| Type | string |
| Required | Yes |

**Example:**
```json
"title": "Ordering Coffee at a Café"
```

---

### `language` (optional)

Language code for the content.

| Property | Value |
|----------|-------|
| Type | string |
| Required | No |
| Default | `"en"` |

**Examples:**
```json
"language": "en"
"language": "en-US"
"language": "en-GB"
```

---

### `level` (optional)

CEFR language proficiency level.

| Property | Value |
|----------|-------|
| Type | string |
| Required | No |
| Valid Values | A1, A2, B1, B2, C1, C2 |

**Example:**
```json
"level": "B2"
```

---

### `lines` (required)

Array of conversation lines.

| Property | Value |
|----------|-------|
| Type | array |
| Required | Yes |
| Min Items | 1 |

---

### `settings` (optional)

Global settings for the script.

| Property | Value |
|----------|-------|
| Type | object |
| Required | No |

---

## Line Object Fields

### `id` (required)

Unique identifier for the line within the script.

| Property | Value |
|----------|-------|
| Type | integer |
| Required | Yes |
| Constraints | Must be unique within script |

**Example:**
```json
"id": 1
```

---

### `speaker` (required)

Speaker identifier. Maps to a voice in the configuration.

| Property | Value |
|----------|-------|
| Type | string |
| Required | Yes |

**Standard Speaker IDs:**
- `female_us_1`, `female_us_2`
- `male_us_1`, `male_us_2`
- `female_uk_1`, `male_uk_1`

**Example:**
```json
"speaker": "female_us_1"
```

---

### `text` (required)

The text to be synthesized to speech.

| Property | Value |
|----------|-------|
| Type | string |
| Required | Yes |
| Max Length | 5000 characters |

**Example:**
```json
"text": "Good morning! How can I help you today?"
```

---

### `voice` (optional)

Direct voice name override. Bypasses speaker mapping.

| Property | Value |
|----------|-------|
| Type | string |
| Required | No |

**Example (Edge TTS):**
```json
"voice": "en-US-AriaNeural"
```

**Example (Kokoro):**
```json
"voice": "af_heart"
```

---

### `emotion` (optional)

Emotional style hint for the speech.

| Property | Value |
|----------|-------|
| Type | string |
| Required | No |
| Default | `"neutral"` |
| Valid Values | `neutral`, `friendly`, `cheerful`, `serious`, `excited` |

**Examples:**
```json
"emotion": "cheerful"
"emotion": "serious"
```

---

### `pause_after_ms` (optional)

Pause duration after this line in milliseconds.

| Property | Value |
|----------|-------|
| Type | integer |
| Required | No |
| Default | 400 |
| Range | 0-10000 |

**Example:**
```json
"pause_after_ms": 800
```

---

### `speech_rate` (optional)

Speech speed multiplier.

| Property | Value |
|----------|-------|
| Type | float |
| Required | No |
| Default | 1.0 |
| Range | 0.5-2.0 |

**Examples:**
```json
"speech_rate": 0.8   // Slower (80% speed)
"speech_rate": 1.0   // Normal speed
"speech_rate": 1.2   // Faster (120% speed)
```

---

## Settings Object Fields

### `speech_rate` (optional)

Global speech rate for all lines.

| Property | Value |
|----------|-------|
| Type | float |
| Required | No |
| Default | 1.0 |
| Range | 0.5-2.0 |

---

### `initial_silence_ms` (optional)

Silence at the beginning of the audio.

| Property | Value |
|----------|-------|
| Type | integer |
| Required | No |
| Default | 300 |
| Range | 0-5000 |

---

### `default_pause_ms` (optional)

Default pause between lines when not specified per-line.

| Property | Value |
|----------|-------|
| Type | integer |
| Required | No |
| Default | 400 |
| Range | 0-10000 |

---

## Complete Example

```json
{
  "lesson_id": "coffee_shop_001",
  "title": "Ordering Coffee",
  "language": "en",
  "level": "A2",
  "lines": [
    {
      "id": 1,
      "speaker": "female_us_1",
      "text": "Good morning! Welcome to Coffee House. What can I get for you?",
      "emotion": "cheerful",
      "pause_after_ms": 800
    },
    {
      "id": 2,
      "speaker": "male_us_1",
      "text": "Hi! I'd like a medium cappuccino, please.",
      "emotion": "friendly",
      "pause_after_ms": 600
    },
    {
      "id": 3,
      "speaker": "female_us_1",
      "text": "Sure! For here or to go?",
      "emotion": "friendly",
      "pause_after_ms": 700
    },
    {
      "id": 4,
      "speaker": "male_us_1",
      "text": "To go, please.",
      "emotion": "neutral",
      "pause_after_ms": 500
    },
    {
      "id": 5,
      "speaker": "female_us_1",
      "text": "That will be four dollars and fifty cents.",
      "emotion": "friendly",
      "pause_after_ms": 800
    },
    {
      "id": 6,
      "speaker": "male_us_1",
      "text": "Here you go. Thank you!",
      "emotion": "friendly",
      "pause_after_ms": 500
    },
    {
      "id": 7,
      "speaker": "female_us_1",
      "text": "Thank you! Your coffee will be ready in just a moment.",
      "emotion": "cheerful",
      "pause_after_ms": 600
    }
  ],
  "settings": {
    "speech_rate": 1.0,
    "initial_silence_ms": 500,
    "default_pause_ms": 400
  }
}
```

---

## Validation Rules

1. **lesson_id**: Must be non-empty, alphanumeric with underscores/hyphens
2. **title**: Must be non-empty
3. **lines**: Must have at least one line
4. **Line IDs**: Must be unique within the script
5. **speaker**: Must be non-empty
6. **text**: Must be non-empty, max 5000 characters
7. **emotion**: Must be one of valid values
8. **pause_after_ms**: Must be 0-10000
9. **speech_rate**: Must be 0.5-2.0

---

## Output Files

For a script with `lesson_id: "coffee_shop_001"`:

| File | Description |
|------|-------------|
| `coffee_shop_001.mp3` | Audio file |
| `coffee_shop_001.srt` | SRT subtitles |
| `coffee_shop_001_timeline.json` | Timeline with segments |

### Timeline JSON Format

```json
{
  "lesson_id": "coffee_shop_001",
  "title": "Ordering Coffee",
  "audio_file": "coffee_shop_001.mp3",
  "srt_file": "coffee_shop_001.srt",
  "duration_ms": 25000,
  "segments": [
    {
      "id": 1,
      "speaker": "female_us_1",
      "text": "Good morning! Welcome to Coffee House...",
      "start_ms": 500,
      "end_ms": 3500,
      "audio_duration_ms": 3000
    }
  ],
  "metadata": {
    "engine": "edge",
    "generated_at": "2024-01-15T10:30:00Z"
  }
}
```

### SRT Format

```srt
1
00:00:00,500 --> 00:00:03,500
Good morning! Welcome to Coffee House. What can I get for you?

2
00:00:04,300 --> 00:00:06,900
Hi! I'd like a medium cappuccino, please.
```
