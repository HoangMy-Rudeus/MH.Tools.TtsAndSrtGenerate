# Your First Script

Learn how to create conversation scripts for the TTS & SRT Generator.

## What is a Script?

A script is a JSON file that defines a conversation with multiple speakers. Each line includes:
- Who is speaking
- What they're saying
- How they're saying it (emotion, speed)
- Timing (pauses between lines)

## Basic Script Structure

```json
{
  "lesson_id": "unique_identifier",
  "title": "Human Readable Title",
  "language": "en",
  "lines": [
    {
      "id": 1,
      "speaker": "female_us_1",
      "text": "Text to speak"
    }
  ]
}
```

## Step-by-Step: Create a Greeting Lesson

### Step 1: Create the File

Create a new file called `greetings_lesson.json`:

```json
{
  "lesson_id": "greetings_001",
  "title": "Basic Greetings"
}
```

### Step 2: Add the Lines Array

```json
{
  "lesson_id": "greetings_001",
  "title": "Basic Greetings",
  "lines": []
}
```

### Step 3: Add Your First Line

```json
{
  "lesson_id": "greetings_001",
  "title": "Basic Greetings",
  "lines": [
    {
      "id": 1,
      "speaker": "female_us_1",
      "text": "Hello! My name is Sarah."
    }
  ]
}
```

### Step 4: Add More Lines with Different Speakers

```json
{
  "lesson_id": "greetings_001",
  "title": "Basic Greetings",
  "lines": [
    {
      "id": 1,
      "speaker": "female_us_1",
      "text": "Hello! My name is Sarah.",
      "pause_after_ms": 800
    },
    {
      "id": 2,
      "speaker": "male_us_1",
      "text": "Hi Sarah! I'm John. Nice to meet you.",
      "pause_after_ms": 600
    },
    {
      "id": 3,
      "speaker": "female_us_1",
      "text": "Nice to meet you too, John!",
      "pause_after_ms": 500
    }
  ]
}
```

### Step 5: Add Emotions

Emotions help make the speech more natural:

```json
{
  "lesson_id": "greetings_001",
  "title": "Basic Greetings",
  "lines": [
    {
      "id": 1,
      "speaker": "female_us_1",
      "text": "Hello! My name is Sarah.",
      "emotion": "cheerful",
      "pause_after_ms": 800
    },
    {
      "id": 2,
      "speaker": "male_us_1",
      "text": "Hi Sarah! I'm John. Nice to meet you.",
      "emotion": "friendly",
      "pause_after_ms": 600
    },
    {
      "id": 3,
      "speaker": "female_us_1",
      "text": "Nice to meet you too, John!",
      "emotion": "excited",
      "pause_after_ms": 500
    }
  ]
}
```

Available emotions:
- `neutral` (default)
- `friendly`
- `cheerful`
- `serious`
- `excited`

### Step 6: Add Settings (Optional)

```json
{
  "lesson_id": "greetings_001",
  "title": "Basic Greetings",
  "language": "en",
  "level": "A1",
  "lines": [
    {
      "id": 1,
      "speaker": "female_us_1",
      "text": "Hello! My name is Sarah.",
      "emotion": "cheerful",
      "pause_after_ms": 800
    },
    {
      "id": 2,
      "speaker": "male_us_1",
      "text": "Hi Sarah! I'm John. Nice to meet you.",
      "emotion": "friendly",
      "pause_after_ms": 600
    },
    {
      "id": 3,
      "speaker": "female_us_1",
      "text": "Nice to meet you too, John!",
      "emotion": "excited",
      "pause_after_ms": 500
    }
  ],
  "settings": {
    "speech_rate": 0.9,
    "initial_silence_ms": 500,
    "default_pause_ms": 400
  }
}
```

### Step 7: Validate Your Script

Before generating, validate to catch any errors:

```bash
python main.py validate greetings_lesson.json
```

Expected output:
```
Script is valid!
  Lesson ID: greetings_001
  Title: Basic Greetings
  Lines: 3
  Language: en
```

### Step 8: Generate Audio

```bash
python main.py generate greetings_lesson.json -o output/
```

## Complete Example: Coffee Shop Conversation

Here's a more complex example:

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
      "text": "Good morning! Welcome to Coffee House. What can I get for you today?",
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
      "text": "Sure! Would you like that for here or to go?",
      "emotion": "friendly",
      "pause_after_ms": 700
    },
    {
      "id": 4,
      "speaker": "male_us_1",
      "text": "To go, please. And can I also get a blueberry muffin?",
      "emotion": "neutral",
      "pause_after_ms": 600
    },
    {
      "id": 5,
      "speaker": "female_us_1",
      "text": "Of course! That will be six dollars and fifty cents.",
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
      "text": "Thank you! Your order will be ready in just a moment.",
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

## Tips for Good Scripts

### 1. Natural Conversation Flow
- Keep exchanges realistic
- Vary sentence lengths
- Include natural responses ("Sure!", "Of course!")

### 2. Appropriate Pauses
- Longer pauses (800-1000ms) after questions
- Shorter pauses (400-600ms) after statements
- Give learners time to process

### 3. Clear Speaker Distinction
- Use different speaker IDs for each character
- Mix male/female voices for clarity
- Consider US vs UK accents for variety

### 4. Speech Rate for Level
- Beginners (A1-A2): `speech_rate: 0.8` to `0.9`
- Intermediate (B1-B2): `speech_rate: 1.0`
- Advanced (C1-C2): `speech_rate: 1.1` to `1.2`

## Common Mistakes to Avoid

1. **Duplicate IDs**: Each line must have a unique `id`
2. **Empty text**: Every line needs `text` content
3. **Invalid speaker**: Use valid speaker IDs from the voice list
4. **Too long pauses**: Keep `pause_after_ms` under 10 seconds

## Next Steps

- [Creating Scripts](../how-to/CREATING_SCRIPTS.md) - Advanced techniques
- [Script Format Reference](../reference/SCRIPT_FORMAT.md) - Complete specification
- [Voice Reference](../reference/VOICE_REFERENCE.md) - All available voices
