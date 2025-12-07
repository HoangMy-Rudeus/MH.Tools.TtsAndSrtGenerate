# Getting Started

This tutorial will guide you through setting up the TTS & SRT Generator and creating your first audio lesson.

## Prerequisites

Before you begin, ensure you have:

- **Python 3.10+** installed ([Download Python](https://www.python.org/downloads/))
- **pip** package manager (included with Python)
- **FFmpeg** installed (required by pydub for audio processing)

### Installing FFmpeg

**Windows:**
```bash
# Using Chocolatey
choco install ffmpeg

# Or using winget
winget install FFmpeg

# Or download manually from https://ffmpeg.org/download.html
```

**macOS:**
```bash
brew install ffmpeg
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install ffmpeg
```

## Step 1: Clone or Download the Project

```bash
# If using Git
git clone <repository-url>
cd TtsAndSrtGenerate

# Or download and extract the ZIP file
```

## Step 2: Create a Virtual Environment

It's recommended to use a virtual environment to manage dependencies:

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

You should see `(venv)` at the beginning of your command prompt.

## Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `pydub` - Audio processing
- `edge-tts` - Microsoft Edge TTS (free, cloud-based)
- `click` - CLI framework
- `pyyaml` - Configuration parsing
- `soundfile` - Audio file I/O
- `numpy` - Array operations

## Step 4: Verify Installation

Run the help command to verify everything is installed correctly:

```bash
python main.py --help
```

You should see:
```
Usage: main.py [OPTIONS] COMMAND [ARGS]...

  TTS & SRT Generator - Convert conversation scripts to audio and subtitles.

Options:
  -v, --verbose  Enable verbose output
  --help         Show this message and exit.

Commands:
  batch        Process all JSON scripts in a directory.
  generate     Generate audio and subtitles from a conversation script.
  init-config  Generate a default configuration file.
  validate     Validate a conversation script without generating audio.
  voices       List available voices for a TTS engine.
```

## Step 5: List Available Voices

See what voices are available:

```bash
python main.py voices --engine edge
```

Output:
```
Edge TTS voices:

Speaker ID mappings:
  female_us_1: en-US-AriaNeural
  female_us_2: en-US-JennyNeural
  male_us_1: en-US-GuyNeural
  male_us_2: en-US-ChristopherNeural
  male_uk_1: en-GB-RyanNeural
  female_uk_1: en-GB-SoniaNeural
...
```

## Step 6: Generate Your First Audio

Use the sample script included in the project:

```bash
python main.py generate docs/conversation_1.json -o output/
```

You'll see progress output:
```
Using engine: edge
Output format: mp3
Output directory: output/

  [1/17] Line 1: 3200ms
  [2/17] Line 2: 2800ms
  ...

Generation successful!
  Audio: output\office_intro_003.mp3
  SRT: output\office_intro_003.srt
  Timeline: output\office_intro_003_timeline.json
  Duration: 45000ms (45.0s)
```

## Step 7: Check Your Output Files

The `output/` directory now contains:

1. **office_intro_003.mp3** - The audio file with all conversations
2. **office_intro_003.srt** - Subtitles you can use with video players
3. **office_intro_003_timeline.json** - Detailed timing information

### Preview the SRT file:

```srt
1
00:00:00,500 --> 00:00:03,700
Hi everyone, this is Alex, our new front-end developer. Let's give him a warm welcome!

2
00:00:04,500 --> 00:00:07,300
Hello Alex, nice to meet you. I'm David, I work on the back-end team.
```

## Step 8: Create Your Own Script

Create a new file `my_lesson.json`:

```json
{
  "lesson_id": "my_first_lesson",
  "title": "Greeting Practice",
  "language": "en",
  "lines": [
    {
      "id": 1,
      "speaker": "female_us_1",
      "text": "Good morning! How are you today?",
      "emotion": "cheerful",
      "pause_after_ms": 800
    },
    {
      "id": 2,
      "speaker": "male_us_1",
      "text": "I'm doing great, thank you. How about you?",
      "emotion": "friendly",
      "pause_after_ms": 600
    },
    {
      "id": 3,
      "speaker": "female_us_1",
      "text": "I'm wonderful! Ready to start the day.",
      "emotion": "excited",
      "pause_after_ms": 500
    }
  ],
  "settings": {
    "initial_silence_ms": 500,
    "default_pause_ms": 400
  }
}
```

Generate audio from your script:

```bash
python main.py generate my_lesson.json -o output/
```

## Next Steps

Congratulations! You've successfully:
- Set up the TTS & SRT Generator
- Generated audio and subtitles from a script
- Created your own conversation script

### Learn More

- [Quick Start Guide](QUICK_START.md) - Even faster setup
- [Your First Script](YOUR_FIRST_SCRIPT.md) - Deep dive into script creation
- [Creating Scripts](../how-to/CREATING_SCRIPTS.md) - Advanced script techniques
- [Custom Voices](../how-to/CUSTOM_VOICES.md) - Configure different voices

### Troubleshooting

**"FFmpeg not found" error:**
Make sure FFmpeg is installed and in your system PATH. Run `ffmpeg -version` to verify.

**"No module named 'edge_tts'" error:**
Run `pip install edge-tts` to install the Edge TTS package.

**Network errors with Edge TTS:**
Edge TTS requires an internet connection. Check your network connectivity.
