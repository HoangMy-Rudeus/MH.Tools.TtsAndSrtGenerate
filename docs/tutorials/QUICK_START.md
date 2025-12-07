# Quick Start

Get up and running in under 5 minutes.

## Prerequisites

- Python 3.10+
- FFmpeg installed

## Installation

```bash
# 1. Navigate to project directory
cd TtsAndSrtGenerate

# 2. Create and activate virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt
```

## Generate Your First Audio

```bash
# Generate audio from sample script
python main.py generate docs/conversation_1.json -o output/
```

That's it! Check the `output/` folder for:
- `office_intro_003.mp3` - Audio file
- `office_intro_003.srt` - Subtitle file
- `office_intro_003_timeline.json` - Timeline data

## Quick Commands

```bash
# Validate a script (no audio generation)
python main.py validate docs/conversation_1.json

# List available voices
python main.py voices --engine edge

# Use WAV format instead of MP3
python main.py generate docs/conversation_1.json -o output/ --format wav

# Process all scripts in a folder
python main.py batch scripts/ -o output/

# Generate config file for customization
python main.py init-config -o config/my-config.yaml
```

## Create a Simple Script

Create `hello.json`:

```json
{
  "lesson_id": "hello_world",
  "title": "Hello World",
  "lines": [
    {
      "id": 1,
      "speaker": "female_us_1",
      "text": "Hello! Welcome to English learning.",
      "pause_after_ms": 500
    },
    {
      "id": 2,
      "speaker": "male_us_1",
      "text": "Let's get started!",
      "pause_after_ms": 300
    }
  ]
}
```

Generate:
```bash
python main.py generate hello.json -o output/
```

## Available Speakers

| Speaker ID | Voice | Gender |
|------------|-------|--------|
| `female_us_1` | Aria | Female US |
| `female_us_2` | Jenny | Female US |
| `male_us_1` | Guy | Male US |
| `male_us_2` | Christopher | Male US |
| `female_uk_1` | Sonia | Female UK |
| `male_uk_1` | Ryan | Male UK |

## Next Steps

- [Getting Started](GETTING_STARTED.md) - Full setup guide
- [Your First Script](YOUR_FIRST_SCRIPT.md) - Learn script format
- [CLI Reference](../reference/CLI_REFERENCE.md) - All commands
