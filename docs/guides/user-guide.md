# User Guide

Step-by-step guide for using TTS & SRT Generator to create audio lessons.

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Creating Voice Samples](#creating-voice-samples)
3. [Writing Scripts](#writing-scripts)
4. [Generating Lessons](#generating-lessons)
5. [Working with Output Files](#working-with-output-files)
6. [Common Workflows](#common-workflows)
7. [Troubleshooting](#troubleshooting)

---

## Getting Started

### Prerequisites

Before you begin, ensure you have:

- Python 3.10 or higher
- NVIDIA GPU with CUDA (recommended) or CPU
- ~4GB VRAM for GPU mode
- FFmpeg installed (for audio processing)

### Installation

1. **Clone the repository**

```bash
git clone https://github.com/your-org/TtsAndSrtGenerate.git
cd TtsAndSrtGenerate
```

2. **Create a virtual environment**

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Verify installation**

```bash
python main.py --version
# Output: 0.1.0
```

---

## Creating Voice Samples

Voice samples are the foundation of high-quality synthesis. XTTS v2 clones voices from short audio references.

### Requirements

| Attribute | Requirement |
|-----------|-------------|
| Duration | 6-12 seconds |
| Format | WAV |
| Channels | Mono |
| Sample Rate | 24kHz (recommended) |
| Quality | Clean, no background noise |

### Recording Tips

1. **Environment**: Record in a quiet room with minimal echo
2. **Microphone**: Use a decent quality microphone
3. **Content**: Speak naturally with varied intonation
4. **Avoid**: Background music, other voices, typing sounds

### Adding Voices

Place `.wav` files in the `voices/` directory:

```
voices/
  male_us_1.wav       # Voice ID: "male_us_1"
  female_us_1.wav     # Voice ID: "female_us_1"
  john_narrator.wav   # Voice ID: "john_narrator"
```

The filename (without `.wav`) becomes the voice ID used in scripts.

### Verify Voices

```bash
python main.py list-voices
```

Output:
```
Available voices:
  - male_us_1: voices/male_us_1.wav
  - female_us_1: voices/female_us_1.wav
```

---

## Writing Scripts

Scripts are JSON files that define the conversation to generate.

### Basic Structure

```json
{
  "lesson_id": "unique_identifier",
  "title": "Lesson Title",
  "level": "B2",
  "lines": [
    {
      "id": 1,
      "speaker": "voice_id",
      "text": "Text to synthesize",
      "emotion": "friendly",
      "pause_after_ms": 500
    }
  ],
  "settings": {
    "speech_rate": 1.0,
    "initial_silence_ms": 300,
    "default_pause_ms": 400
  }
}
```

### Line Properties

#### `id` (required)
Unique integer identifier for the line.

```json
{"id": 1, ...}
{"id": 2, ...}
```

#### `speaker` (required)
Voice ID matching a file in `voices/` directory.

```json
{"speaker": "male_us_1", ...}
{"speaker": "female_us_1", ...}
```

#### `text` (required)
The text to synthesize. Use natural punctuation for better prosody.

```json
// Good - natural punctuation
{"text": "Hello! How are you today?", ...}

// Avoid - run-on sentences
{"text": "hello how are you today", ...}
```

**Allowed characters**: Letters, numbers, spaces, and basic punctuation: `. , ! ? ' " - : ; ( )`

#### `emotion` (optional)
Speech style. Default: `"neutral"`

| Emotion | Description | Speed |
|---------|-------------|-------|
| `neutral` | Default, factual | 1.0x |
| `friendly` | Warm, conversational | 1.0x |
| `cheerful` | Happy, upbeat | 1.05x |
| `serious` | Formal, important | 0.95x |
| `excited` | High energy | 1.1x |

```json
{"emotion": "cheerful", ...}
```

#### `pause_after_ms` (optional)
Silence after this line in milliseconds. Default: `400`, Range: `0-5000`

```json
// Short pause for quick exchange
{"pause_after_ms": 300, ...}

// Longer pause for topic change
{"pause_after_ms": 1000, ...}
```

#### `speech_rate` (optional)
Override speech speed for this line. Range: `0.5-1.5`

```json
// Slower for emphasis
{"speech_rate": 0.9, ...}

// Faster for excitement
{"speech_rate": 1.2, ...}
```

### Settings

Global settings that apply to all lines unless overridden.

```json
"settings": {
  "speech_rate": 1.0,        // Default speech rate
  "initial_silence_ms": 300, // Silence at start
  "default_pause_ms": 400    // Default pause between lines
}
```

### Complete Example

```json
{
  "lesson_id": "restaurant_order_001",
  "title": "Ordering at a Restaurant",
  "level": "B2",
  "lines": [
    {
      "id": 1,
      "speaker": "female_us_1",
      "text": "Good evening! Welcome to The Golden Fork. Table for two?",
      "emotion": "cheerful",
      "pause_after_ms": 800
    },
    {
      "id": 2,
      "speaker": "male_us_1",
      "text": "Yes, please. Do you have anything by the window?",
      "emotion": "friendly",
      "pause_after_ms": 600
    },
    {
      "id": 3,
      "speaker": "female_us_1",
      "text": "Absolutely! Right this way. Here are your menus.",
      "emotion": "friendly",
      "pause_after_ms": 1000
    },
    {
      "id": 4,
      "speaker": "male_us_1",
      "text": "Thank you. What do you recommend?",
      "emotion": "neutral",
      "pause_after_ms": 700
    },
    {
      "id": 5,
      "speaker": "female_us_1",
      "text": "Our chef's special today is grilled salmon with lemon butter sauce. It's excellent!",
      "emotion": "excited",
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

---

## Generating Lessons

### Basic Generation

```bash
python main.py generate script.json -o ./output
```

Output:
```
Generating lesson from: script.json
10:30:15 [INFO] Step 1: Validating script...
10:30:15 [INFO] Validated script: restaurant_order_001 with 5 lines
10:30:15 [INFO] Step 2: Synthesizing audio...
10:30:45 [INFO] Step 3: Stitching audio...
10:30:46 [INFO] Step 4: Running forced alignment...
10:30:50 [INFO] Step 5: Generating outputs...

Generation complete!
  Audio: ./output/restaurant_order_001.mp3
  SRT:   ./output/restaurant_order_001.srt
  JSON:  ./output/restaurant_order_001.json
  Duration: 25.3s
  Quality:  0.94
```

### Validate Without Generating

Check your script for errors before full generation:

```bash
python main.py validate script.json
```

Output (success):
```
Validation passed!
```

Output (with errors):
```
Validation failed!

Errors:
  - speaker (line 3): Speaker 'unknown_voice' not found in voice registry
  - text (line 5): Text contains invalid characters: {'@', '#'}
```

### Command Options

```bash
python main.py generate script.json \
  -o ./output \           # Output directory
  -c config/custom.yaml \ # Custom config
  -v                      # Verbose logging
```

---

## Working with Output Files

### Audio File (MP3)

The final audio file, normalized and ready for use.

- Format: MP3, 192kbps
- Sample rate: 24kHz
- Loudness: -16 LUFS (broadcast standard)

**Use cases:**
- Upload to learning platforms
- Embed in mobile apps
- Play in media players

### Subtitles (SRT)

Standard subtitle format for video players and learning apps.

```srt
1
00:00:00,500 --> 00:00:03,200
Good evening! Welcome to The Golden Fork. Table for two?

2
00:00:04,000 --> 00:00:06,500
Yes, please. Do you have anything by the window?

3
00:00:07,100 --> 00:00:10,300
Absolutely! Right this way. Here are your menus.
```

**Use cases:**
- Display synchronized text during playback
- Import into video editing software
- Accessibility features

### Timeline JSON

Detailed metadata for custom integrations.

```json
{
  "lesson_id": "restaurant_order_001",
  "audio_file": "./output/restaurant_order_001.mp3",
  "srt_file": "./output/restaurant_order_001.srt",
  "duration_ms": 25300,
  "segments": [
    {
      "id": 1,
      "speaker": "female_us_1",
      "text": "Good evening! Welcome to The Golden Fork.",
      "start_ms": 500,
      "end_ms": 3200,
      "audio_duration_ms": 2700,
      "confidence": 0.95
    }
  ],
  "metadata": {
    "model_version": "xtts_v2",
    "generated_at": "2025-01-15T10:30:50Z",
    "quality_score": 0.94
  }
}
```

**Use cases:**
- Custom audio players with highlighting
- Analytics and reporting
- Re-processing or editing

---

## Common Workflows

### Workflow 1: Create a Conversation Lesson

1. **Write the script**

```json
{
  "lesson_id": "grocery_shopping_001",
  "title": "At the Grocery Store",
  "lines": [
    {"id": 1, "speaker": "male_us_1", "text": "Excuse me, where can I find the bread?"},
    {"id": 2, "speaker": "female_us_1", "text": "It's in aisle three, on your left."},
    {"id": 3, "speaker": "male_us_1", "text": "Thanks! Do you have whole wheat?"},
    {"id": 4, "speaker": "female_us_1", "text": "Yes, we have several brands. The fresh-baked is at the end of the aisle."}
  ]
}
```

2. **Validate**

```bash
python main.py validate grocery.json
```

3. **Generate**

```bash
python main.py generate grocery.json -o ./lessons
```

4. **Review output**
   - Listen to `grocery_shopping_001.mp3`
   - Check timestamps in `grocery_shopping_001.srt`

### Workflow 2: Batch Generate Multiple Lessons

Create a shell script for batch processing:

```bash
#!/bin/bash
# generate_all.sh

for script in scripts/*.json; do
    echo "Processing: $script"
    python main.py generate "$script" -o ./output
done
```

### Workflow 3: Custom Voice for Narrator

1. **Record 10 seconds of narrator voice**
   - Save as `voices/narrator.wav`

2. **Use in scripts**

```json
{
  "lesson_id": "intro_001",
  "title": "Welcome to the Course",
  "lines": [
    {
      "id": 1,
      "speaker": "narrator",
      "text": "Welcome to our English conversation course. In this lesson, we'll practice ordering food at a restaurant.",
      "emotion": "friendly",
      "pause_after_ms": 1000
    }
  ]
}
```

---

## Troubleshooting

### Error: "Voice not found"

**Problem**: Speaker ID doesn't match any file in `voices/`

**Solution**:
1. Check voice files exist: `python main.py list-voices`
2. Verify spelling matches exactly (case-sensitive)
3. Ensure files have `.wav` extension

### Error: "Text contains invalid characters"

**Problem**: Script contains unsupported characters

**Solution**:
- Remove special characters: `@`, `#`, `$`, `%`, `&`, `*`, `{`, `}`, `[`, `]`, etc.
- Use only: letters, numbers, spaces, `. , ! ? ' " - : ; ( )`

### Error: "CUDA out of memory"

**Problem**: GPU doesn't have enough memory

**Solutions**:
1. Use CPU mode:
   ```yaml
   # config/default.yaml
   tts:
     device: "cpu"
   ```

2. Process fewer lines at a time
3. Close other GPU-intensive applications

### Poor Audio Quality

**Symptoms**: Robotic voice, artifacts, repetition

**Solutions**:
1. **Improve voice sample**
   - Use cleaner recording
   - Ensure 6-12 seconds duration
   - Remove background noise

2. **Adjust synthesis parameters**
   ```yaml
   synthesis:
     temperature: 0.5  # Lower = more consistent
   ```

3. **Check quality score** in output JSON
   - Score < 0.8 indicates potential issues

### Timestamp Drift

**Symptoms**: Subtitles don't match audio timing

**Solutions**:
1. **Enable alignment** (default is enabled)
   ```yaml
   alignment:
     enabled: true
     drift_threshold_ms: 200
   ```

2. **Check alignment results** in JSON output
   - High drift values indicate issues
   - Low confidence scores flag problems

### Slow Generation

**Cause**: CPU mode or large files

**Solutions**:
1. Use GPU if available (`device: "cuda"`)
2. Split long lessons into smaller parts
3. Use shorter pauses to reduce total duration
