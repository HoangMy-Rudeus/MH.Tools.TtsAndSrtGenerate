# Creating Scripts

Learn advanced techniques for creating effective conversation scripts.

## Script Structure Overview

```json
{
  "lesson_id": "string (required)",
  "title": "string (required)",
  "language": "string (optional, default: en)",
  "level": "string (optional, e.g., A1, B2)",
  "lines": [/* array of line objects */],
  "settings": {/* optional settings object */}
}
```

## Designing Effective Conversations

### 1. Define Your Learning Objectives

Before writing, identify:
- **Topic**: What situation are learners practicing?
- **Level**: A1 (beginner) to C2 (advanced)
- **Target vocabulary**: Key words/phrases to introduce
- **Grammar focus**: Structures being practiced

### 2. Create Natural Dialogue Flow

**Good Example:**
```json
{
  "lines": [
    {"id": 1, "speaker": "female_us_1", "text": "Excuse me, is this seat taken?"},
    {"id": 2, "speaker": "male_us_1", "text": "No, please go ahead."},
    {"id": 3, "speaker": "female_us_1", "text": "Thanks! I'm Sarah, by the way."},
    {"id": 4, "speaker": "male_us_1", "text": "Nice to meet you, Sarah. I'm Tom."}
  ]
}
```

**Avoid:** Unnatural exchanges that real people wouldn't say.

### 3. Use Multiple Speakers Effectively

Create distinct characters:

```json
{
  "lesson_id": "meeting_001",
  "title": "Team Meeting",
  "lines": [
    {
      "id": 1,
      "speaker": "female_us_1",
      "text": "Good morning everyone. Let's start the meeting.",
      "emotion": "serious"
    },
    {
      "id": 2,
      "speaker": "male_us_1",
      "text": "Sure thing, boss. I have the sales report ready.",
      "emotion": "friendly"
    },
    {
      "id": 3,
      "speaker": "female_us_2",
      "text": "Great! I'd also like to discuss the new marketing campaign.",
      "emotion": "cheerful"
    }
  ]
}
```

## Working with Emotions

### Available Emotions

| Emotion | Best Used For |
|---------|---------------|
| `neutral` | Statements, explanations |
| `friendly` | Casual conversation, greetings |
| `cheerful` | Positive news, welcomes |
| `serious` | Business, important information |
| `excited` | Celebrations, enthusiasm |

### Emotion Examples

```json
{
  "lines": [
    {
      "id": 1,
      "speaker": "female_us_1",
      "text": "We got the contract!",
      "emotion": "excited"
    },
    {
      "id": 2,
      "speaker": "male_us_1",
      "text": "That's wonderful news! Congratulations to the team.",
      "emotion": "cheerful"
    },
    {
      "id": 3,
      "speaker": "female_us_1",
      "text": "However, we need to deliver by next month.",
      "emotion": "serious"
    }
  ]
}
```

## Controlling Timing

### Pause After Lines

```json
{
  "id": 1,
  "speaker": "female_us_1",
  "text": "What do you think about this?",
  "pause_after_ms": 1000  // Longer pause for questions
}
```

**Recommended Pauses:**
- After questions: 800-1200ms
- After statements: 400-600ms
- After exclamations: 500-800ms
- Between topic changes: 1000-1500ms

### Speech Rate

```json
{
  "id": 1,
  "speaker": "female_us_1",
  "text": "Please repeat after me: Hello, how are you?",
  "speech_rate": 0.8  // Slower for learners to follow
}
```

**Recommended Rates by Level:**
- A1-A2 (Beginner): 0.8 - 0.9
- B1-B2 (Intermediate): 0.9 - 1.0
- C1-C2 (Advanced): 1.0 - 1.2

## Script Settings

### Global Settings

```json
{
  "lesson_id": "lesson_001",
  "title": "My Lesson",
  "lines": [...],
  "settings": {
    "speech_rate": 0.9,
    "initial_silence_ms": 500,
    "default_pause_ms": 400
  }
}
```

| Setting | Description | Default |
|---------|-------------|---------|
| `speech_rate` | Global speed multiplier | 1.0 |
| `initial_silence_ms` | Silence at beginning | 300ms |
| `default_pause_ms` | Default pause between lines | 400ms |

## Advanced Techniques

### Using Direct Voice Names

Override speaker mappings with specific voices:

```json
{
  "id": 1,
  "speaker": "narrator",
  "voice": "en-US-AriaNeural",
  "text": "Chapter 1: The Beginning"
}
```

### Creating Lesson Series

Organize related lessons:

```
scripts/
├── unit_01/
│   ├── lesson_01_greetings.json
│   ├── lesson_02_introductions.json
│   └── lesson_03_farewells.json
├── unit_02/
│   ├── lesson_01_shopping.json
│   └── lesson_02_restaurant.json
```

### Including Metadata

Add custom fields for your application:

```json
{
  "lesson_id": "business_001",
  "title": "Business Meeting",
  "language": "en",
  "level": "B2",
  "category": "business",
  "tags": ["meetings", "formal", "workplace"],
  "duration_estimate_minutes": 5,
  "lines": [...]
}
```

## Templates

### Basic Conversation Template

```json
{
  "lesson_id": "template_basic",
  "title": "Basic Conversation",
  "language": "en",
  "level": "A2",
  "lines": [
    {
      "id": 1,
      "speaker": "female_us_1",
      "text": "[Opening line]",
      "emotion": "friendly",
      "pause_after_ms": 600
    },
    {
      "id": 2,
      "speaker": "male_us_1",
      "text": "[Response]",
      "emotion": "friendly",
      "pause_after_ms": 500
    }
  ],
  "settings": {
    "speech_rate": 1.0,
    "initial_silence_ms": 500,
    "default_pause_ms": 400
  }
}
```

### Interview Template

```json
{
  "lesson_id": "interview_template",
  "title": "Job Interview",
  "language": "en",
  "level": "B2",
  "lines": [
    {
      "id": 1,
      "speaker": "female_us_1",
      "text": "Please, have a seat. Thank you for coming today.",
      "emotion": "friendly",
      "pause_after_ms": 800
    },
    {
      "id": 2,
      "speaker": "male_us_1",
      "text": "Thank you for having me.",
      "emotion": "neutral",
      "pause_after_ms": 600
    },
    {
      "id": 3,
      "speaker": "female_us_1",
      "text": "So, tell me about yourself.",
      "emotion": "neutral",
      "pause_after_ms": 1000
    }
  ]
}
```

## Validation Checklist

Before generating, verify:

- [ ] All line IDs are unique
- [ ] Every line has `speaker` and `text`
- [ ] Speaker IDs match available voices
- [ ] Emotions are valid values
- [ ] Speech rates are between 0.5 and 2.0
- [ ] Pauses are reasonable (0-10000ms)

Run validation:
```bash
python main.py validate your_script.json
```

## Best Practices Summary

1. **Start simple**: Begin with 3-5 lines, expand as needed
2. **Test frequently**: Generate audio to hear how it sounds
3. **Vary speakers**: Use different voices for distinct characters
4. **Match emotions**: Align emotions with dialogue content
5. **Consider learners**: Adjust speed and pauses for target level
6. **Be natural**: Write how people actually speak

## Next Steps

- [Script Format Reference](../reference/SCRIPT_FORMAT.md) - Complete specification
- [Voice Reference](../reference/VOICE_REFERENCE.md) - All available voices
- [Batch Processing](BATCH_PROCESSING.md) - Process multiple scripts
