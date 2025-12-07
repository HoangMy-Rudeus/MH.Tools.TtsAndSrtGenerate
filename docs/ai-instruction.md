# AI Instruction: TTS & SRT Generator

Build a **batch Text-to-Speech application** that converts conversation scripts into synchronized audio and subtitle files.

---

## Core Requirements

### Input Format (JSON Script)

```json
{
  "lesson_id": "conversation_001",
  "title": "Office Introduction",
  "language": "en",
  "lines": [
    {
      "id": 1,
      "speaker": "female_us_1",
      "text": "Hi everyone, this is Alex, our new front-end developer.",
      "emotion": "friendly",
      "pause_after_ms": 500,
      "speech_rate": 1.0
    },
    {
      "id": 2,
      "speaker": "male_us_1",
      "text": "Hello Alex, nice to meet you.",
      "emotion": "neutral",
      "pause_after_ms": 400
    }
  ]
}
```

**Line Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | int | Yes | Unique line identifier |
| `speaker` | string | Yes | Speaker ID (maps to voice) |
| `text` | string | Yes | Text to synthesize |
| `emotion` | string | No | Emotion hint: neutral, friendly, cheerful, serious, excited |
| `pause_after_ms` | int | No | Pause after line (default: 400ms) |
| `speech_rate` | float | No | Speed multiplier (default: 1.0) |

---

### Output Files

For input `conversation_001.json`, generate:

1. **Audio File**: `conversation_001.mp3` (or .wav)
   - All lines concatenated with pauses
   - Normalized audio levels

2. **SRT Subtitle File**: `conversation_001.srt`
   ```srt
   1
   00:00:00,300 --> 00:00:03,500
   Hi everyone, this is Alex, our new front-end developer.

   2
   00:00:04,000 --> 00:00:05,800
   Hello Alex, nice to meet you.
   ```

3. **Timeline JSON**: `conversation_001.json`
   ```json
   {
     "lesson_id": "conversation_001",
     "title": "Office Introduction",
     "audio_file": "conversation_001.mp3",
     "srt_file": "conversation_001.srt",
     "duration_ms": 12500,
     "segments": [
       {
         "id": 1,
         "speaker": "female_us_1",
         "text": "Hi everyone, this is Alex...",
         "start_ms": 300,
         "end_ms": 3500,
         "audio_duration_ms": 3200
       }
     ],
     "metadata": {
       "engine": "edge",
       "generated_at": "2024-01-15T10:30:00Z"
     }
   }
   ```

---

## Architecture

### Pluggable TTS Engine Interface

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class SynthesisResult:
    line_id: int
    success: bool
    audio_bytes: bytes | None  # WAV or MP3 bytes
    duration_ms: int
    sample_rate: int
    error: str | None = None

class TTSEngine(ABC):
    """Abstract base class for TTS engines."""

    @abstractmethod
    def initialize(self) -> None:
        """Load model/connect to service."""
        pass

    @abstractmethod
    def synthesize(
        self,
        text: str,
        voice: str,
        emotion: str = "neutral",
        speed: float = 1.0
    ) -> SynthesisResult:
        """Synthesize single text to audio."""
        pass

    @abstractmethod
    def get_available_voices(self) -> list[str]:
        """List available voice IDs."""
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """Release resources."""
        pass
```

### Example Engine Implementations

**1. Edge TTS (Cloud, Fast, Free)**
```python
"""Edge TTS Engine - Microsoft's free cloud TTS service."""

import asyncio
import io
from dataclasses import dataclass

import edge_tts

# Voice mapping: speaker ID -> Edge TTS voice name
EDGE_VOICES = {
    # US English voices
    "male_us_1": "en-US-GuyNeural",
    "male_us_2": "en-US-ChristopherNeural",
    "female_us_1": "en-US-AriaNeural",
    "female_us_2": "en-US-JennyNeural",
    # UK English voices
    "male_uk_1": "en-GB-RyanNeural",
    "female_uk_1": "en-GB-SoniaNeural",
}

DEFAULT_VOICE = "en-US-AriaNeural"


class EdgeTTSEngine(TTSEngine):
    """Microsoft Edge TTS - free, fast, cloud-based."""

    def __init__(self, custom_voices: dict[str, str] = None):
        """
        Initialize Edge TTS engine.

        Args:
            custom_voices: Optional custom speaker->voice mapping
        """
        self.voices = {**EDGE_VOICES, **(custom_voices or {})}

    def initialize(self) -> None:
        """No initialization needed for Edge TTS."""
        pass

    def get_voice(self, speaker: str) -> str:
        """Get Edge TTS voice for speaker ID."""
        return self.voices.get(speaker, DEFAULT_VOICE)

    async def _synthesize_async(
        self,
        text: str,
        voice: str,
        rate: str = "+0%"
    ) -> bytes:
        """Async synthesis using Edge TTS."""
        communicate = edge_tts.Communicate(text, voice, rate=rate)

        audio_data = io.BytesIO()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data.write(chunk["data"])

        return audio_data.getvalue()

    def synthesize(
        self,
        text: str,
        voice: str,
        emotion: str = "neutral",
        speed: float = 1.0
    ) -> SynthesisResult:
        """
        Synthesize text to audio.

        Args:
            text: Text to synthesize
            voice: Speaker ID (e.g., "female_us_1")
            emotion: Emotion hint (not fully supported by Edge)
            speed: Speech rate multiplier (1.0 = normal)

        Returns:
            SynthesisResult with MP3 audio bytes
        """
        try:
            # Map speaker to Edge voice
            edge_voice = self.get_voice(voice)

            # Calculate rate string (+10% or -10%)
            rate_percent = int((speed - 1.0) * 100)
            rate = f"+{rate_percent}%" if rate_percent >= 0 else f"{rate_percent}%"

            # Run async synthesis
            audio_bytes = asyncio.run(
                self._synthesize_async(text, edge_voice, rate)
            )

            # Estimate duration (rough: ~16KB/sec for MP3 at 128kbps)
            duration_ms = int(len(audio_bytes) / 16 * 1000 / 1024)

            return SynthesisResult(
                line_id=0,
                success=True,
                audio_bytes=audio_bytes,
                duration_ms=duration_ms,
                sample_rate=24000,
            )

        except Exception as e:
            return SynthesisResult(
                line_id=0,
                success=False,
                audio_bytes=None,
                duration_ms=0,
                sample_rate=24000,
                error=str(e),
            )

    def get_available_voices(self) -> list[str]:
        """List available speaker IDs."""
        return list(self.voices.keys())

    def cleanup(self) -> None:
        """No cleanup needed for Edge TTS."""
        pass


# List all Edge TTS voices (run once to discover)
async def list_all_edge_voices(language: str = "en") -> list[dict]:
    """List all available Edge TTS voices for a language."""
    voices = await edge_tts.list_voices()
    return [v for v in voices if v["Locale"].startswith(language)]


# Usage example
if __name__ == "__main__":
    engine = EdgeTTSEngine()

    result = engine.synthesize(
        text="Hello, this is a test of Edge TTS.",
        voice="female_us_1",
        speed=1.0
    )

    if result.success:
        with open("test_output.mp3", "wb") as f:
            f.write(result.audio_bytes)
        print(f"Generated audio: {result.duration_ms}ms")
    else:
        print(f"Error: {result.error}")
```

**Edge TTS Voice Reference:**

| Speaker ID | Edge Voice | Gender | Accent | Style |
|------------|------------|--------|--------|-------|
| `female_us_1` | en-US-AriaNeural | Female | US | Friendly, versatile |
| `female_us_2` | en-US-JennyNeural | Female | US | Conversational |
| `male_us_1` | en-US-GuyNeural | Male | US | Casual, friendly |
| `male_us_2` | en-US-ChristopherNeural | Male | US | Professional |
| `female_uk_1` | en-GB-SoniaNeural | Female | UK | Warm, professional |
| `male_uk_1` | en-GB-RyanNeural | Male | UK | Friendly |

**List all voices via CLI:**
```bash
edge-tts --list-voices | grep "en-"
```

**2. Kokoro-ONNX (Local, High Quality, Fast)**
```python
"""Kokoro-ONNX Engine - High quality local TTS using ONNX runtime."""

import io
import soundfile as sf
from kokoro_onnx import Kokoro

# Voice mapping: speaker ID -> Kokoro voice name
KOKORO_VOICES = {
    # American English voices
    "female_us_1": "af_heart",      # American Female - Heart (warm, friendly)
    "female_us_2": "af_bella",      # American Female - Bella (clear, professional)
    "female_us_3": "af_nicole",     # American Female - Nicole (young, energetic)
    "female_us_4": "af_sarah",      # American Female - Sarah (calm, mature)
    "female_us_5": "af_sky",        # American Female - Sky (bright, cheerful)
    "female_us_6": "af_nova",       # American Female - Nova (bright)
    "female_us_7": "af_river",      # American Female - River (calm)
    "female_us_8": "af_alloy",      # American Female - Alloy (neutral)
    "male_us_1": "am_adam",         # American Male - Adam (deep, authoritative)
    "male_us_2": "am_michael",      # American Male - Michael (friendly, casual)
    # British English voices
    "female_uk_1": "bf_emma",       # British Female - Emma
    "female_uk_2": "bf_isabella",   # British Female - Isabella
    "male_uk_1": "bm_george",       # British Male - George
    "male_uk_2": "bm_lewis",        # British Male - Lewis
}

DEFAULT_VOICE = "af_heart"


class KokoroTTSEngine(TTSEngine):
    """Kokoro-ONNX TTS - high quality, fast local inference."""

    def __init__(
        self,
        model_path: str = "kokoro-v1.0.onnx",
        voices_path: str = "voices-v1.0.bin",
        custom_voices: dict[str, str] = None
    ):
        """
        Initialize Kokoro-ONNX engine.

        Args:
            model_path: Path to kokoro-v1.0.onnx model file
            voices_path: Path to voices-v1.0.bin file
            custom_voices: Optional custom speaker->voice mapping
        """
        self.model_path = model_path
        self.voices_path = voices_path
        self.voices = {**KOKORO_VOICES, **(custom_voices or {})}
        self.kokoro = None

    def initialize(self) -> None:
        """Load Kokoro ONNX model."""
        self.kokoro = Kokoro(self.model_path, self.voices_path)

    def get_voice(self, speaker: str) -> str:
        """Get Kokoro voice for speaker ID."""
        return self.voices.get(speaker, DEFAULT_VOICE)

    def synthesize(
        self,
        text: str,
        voice: str,
        emotion: str = "neutral",
        speed: float = 1.0
    ) -> SynthesisResult:
        """
        Synthesize text to audio.

        Args:
            text: Text to synthesize
            voice: Speaker ID (e.g., "female_us_1")
            emotion: Emotion hint (not used)
            speed: Speech rate multiplier (1.0 = normal)

        Returns:
            SynthesisResult with WAV audio bytes
        """
        if self.kokoro is None:
            self.initialize()

        try:
            # Map speaker to Kokoro voice
            kokoro_voice = self.get_voice(voice)

            # Generate audio
            samples, sample_rate = self.kokoro.create(
                text,
                voice=kokoro_voice,
                speed=speed,
                lang="en-us"
            )

            # Convert to WAV bytes
            buffer = io.BytesIO()
            sf.write(buffer, samples, sample_rate, format="WAV")
            audio_bytes = buffer.getvalue()

            # Calculate duration
            duration_ms = int(len(samples) / sample_rate * 1000)

            return SynthesisResult(
                line_id=0,
                success=True,
                audio_bytes=audio_bytes,
                duration_ms=duration_ms,
                sample_rate=sample_rate,
            )

        except Exception as e:
            return SynthesisResult(
                line_id=0,
                success=False,
                audio_bytes=None,
                duration_ms=0,
                sample_rate=24000,
                error=str(e),
            )

    def get_available_voices(self) -> list[str]:
        """List available speaker IDs."""
        return list(self.voices.keys())

    def cleanup(self) -> None:
        """Release model resources."""
        self.kokoro = None


# Usage example
if __name__ == "__main__":
    engine = KokoroTTSEngine(
        model_path="kokoro-v1.0.onnx",
        voices_path="voices-v1.0.bin"
    )
    engine.initialize()

    result = engine.synthesize(
        text="Hello, this is a test of Kokoro ONNX TTS.",
        voice="female_us_1",
        speed=1.0
    )

    if result.success:
        with open("test_output.wav", "wb") as f:
            f.write(result.audio_bytes)
        print(f"Generated audio: {result.duration_ms}ms")
    else:
        print(f"Error: {result.error}")
```

**Kokoro-ONNX Voice Reference:**

| Speaker ID | Kokoro Voice | Gender | Accent | Style |
|------------|--------------|--------|--------|-------|
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

**Install Kokoro-ONNX:**
```bash
pip install kokoro-onnx soundfile
```

**Download model files:**
```bash
# Download from Hugging Face
wget https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx
wget https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin
```

Or download from: https://huggingface.co/onnx-community/Kokoro-82M-v1.0-ONNX

---

## Engine Comparison

| Feature | Edge TTS | Kokoro-ONNX |
|---------|----------|-------------|
| **Type** | Cloud | Local |
| **Speed** | ~0.5s/line | ~1-2s/line (CPU), ~0.3s/line (GPU) |
| **Quality** | Good | Excellent |
| **Cost** | Free | Free |
| **Offline** | No | Yes |
| **Model Size** | N/A | ~300MB (quantized: ~80MB) |
| **Voices** | 400+ languages | 14+ English voices |
| **Best For** | Quick preview | Production quality |

---

## Pipeline Flow

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Input     │────▶│   Validate   │────▶│  Synthesize │
│   Script    │     │   Script     │     │  Per Line   │
└─────────────┘     └──────────────┘     └─────────────┘
                                                │
                                                ▼
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Output    │◀────│   Generate   │◀────│   Stitch    │
│   Files     │     │   SRT/JSON   │     │   Audio     │
└─────────────┘     └──────────────┘     └─────────────┘
```

### Pipeline Steps

1. **Validate Script**
   - Check required fields
   - Validate speaker IDs against available voices
   - Check text for invalid characters

2. **Synthesize Lines**
   - For each line, call TTS engine
   - Handle retries on failure
   - Collect audio bytes + duration

3. **Stitch Audio**
   - Concatenate all audio segments
   - Add pauses between lines
   - Add initial silence (300ms default)
   - Normalize audio levels

4. **Generate Outputs**
   - Export final audio (MP3/WAV)
   - Generate SRT with timestamps
   - Generate timeline JSON

---

## Configuration

```yaml
# config.yaml
engine: "edge"  # "edge" or "kokoro"

# Edge TTS settings (cloud-based)
edge:
  default_voice: "en-US-AriaNeural"
  voices:
    female_us_1: "en-US-AriaNeural"
    female_us_2: "en-US-JennyNeural"
    male_us_1: "en-US-GuyNeural"
    male_us_2: "en-US-ChristopherNeural"
    male_uk_1: "en-GB-RyanNeural"
    female_uk_1: "en-GB-SoniaNeural"

# Kokoro-ONNX settings (local)
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

# Audio output
audio:
  sample_rate: 24000
  normalize_to: -16  # LUFS

# Synthesis
synthesis:
  default_pause_ms: 400
  initial_silence_ms: 300
  max_retries: 3
```

---

## CLI Interface

```bash
# Generate with default config (uses edge)
python main.py generate script.json -o output/

# Use Edge TTS (fast, cloud)
python main.py generate script.json --engine edge

# Use Kokoro TTS (high quality, local)
python main.py generate script.json --engine kokoro

# Use custom config
python main.py generate script.json -c config/production.yaml

# List available voices
python main.py voices --engine edge
python main.py voices --engine kokoro

# Validate script only
python main.py validate script.json
```

---

## Project Structure

```
tts-generator/
├── main.py                 # CLI entry point
├── config/
│   └── default.yaml
├── src/
│   ├── models/
│   │   ├── script.py       # Input/output data models
│   │   └── config.py       # Configuration models
│   ├── engines/
│   │   ├── base.py         # TTSEngine abstract class
│   │   ├── edge.py         # Edge TTS implementation
│   │   ├── kokoro.py       # Kokoro TTS implementation
│   │   └── factory.py      # Engine factory
│   ├── services/
│   │   ├── validator.py    # Script validation
│   │   ├── synthesizer.py  # TTS orchestration
│   │   └── stitcher.py     # Audio concatenation
│   ├── utils/
│   │   ├── audio.py        # Audio processing
│   │   └── srt.py          # SRT generation
│   └── pipeline.py         # Main pipeline
├── requirements.txt
└── tests/
```

---

## Key Implementation Notes

### 1. Audio Format Handling
Each engine outputs its native format - no conversion needed:
- **Edge TTS**: MP3 (compressed, smaller files)
- **Kokoro-ONNX**: WAV (uncompressed, higher quality)

Both formats work directly with pydub for stitching.

### 2. Voice Mapping
Each engine maps abstract speaker IDs to engine-specific voices:
```python
# In script: "speaker": "female_us_1"
# Edge maps to: "en-US-AriaNeural"
# Kokoro-ONNX maps to: "af_heart"
```

### 3. Error Handling
- Retry failed synthesis (configurable attempts)
- Log warnings for quality issues
- Fail gracefully with partial output if possible

### 4. SRT Timestamp Format
```python
def ms_to_srt_time(ms: int) -> str:
    """Convert milliseconds to SRT timestamp format."""
    hours = ms // 3600000
    minutes = (ms % 3600000) // 60000
    seconds = (ms % 60000) // 1000
    millis = ms % 1000
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"
```

---

## Dependencies

```txt
# Core
pydub>=0.25.0      # Audio processing
pyyaml>=6.0        # Config parsing
pydantic>=2.0      # Data validation
click>=8.0         # CLI framework
soundfile>=0.12.0  # Audio file I/O
numpy>=1.24.0      # Array operations

# TTS Engines
edge-tts>=6.1.0    # Edge TTS (cloud)
kokoro-onnx>=0.4.0 # Kokoro-ONNX TTS (local)
```

**Install all:**
```bash
pip install pydub pyyaml pydantic click soundfile numpy edge-tts kokoro-onnx
```

**Download Kokoro models:**
```bash
mkdir -p models
wget -P models https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx
wget -P models https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin
```

---

## Example Usage

### Python API

```python
from src.pipeline import Pipeline
from src.engines.factory import create_engine

# Create pipeline with Edge TTS (fast, cloud)
engine = create_engine("edge")
pipeline = Pipeline(engine)

# Or use Kokoro TTS (high quality, local)
# engine = create_engine("kokoro")
# pipeline = Pipeline(engine)

# Generate from script
result = pipeline.generate(
    script_path="conversation.json",
    output_dir="output/"
)

print(f"Audio: {result.audio_file}")
print(f"SRT: {result.srt_file}")
print(f"Duration: {result.duration_ms}ms")
```

### Batch Processing

```python
import glob

for script in glob.glob("scripts/*.json"):
    pipeline.generate(script, output_dir="output/")
```

### Quick Test

```python
# Test Edge TTS
from src.engines.edge import EdgeTTSEngine
engine = EdgeTTSEngine()
result = engine.synthesize("Hello world!", "female_us_1")
with open("test_edge.mp3", "wb") as f:
    f.write(result.audio_bytes)

# Test Kokoro-ONNX TTS
from src.engines.kokoro import KokoroTTSEngine
engine = KokoroTTSEngine(
    model_path="models/kokoro-v1.0.onnx",
    voices_path="models/voices-v1.0.bin"
)
engine.initialize()
result = engine.synthesize("Hello world!", "female_us_1")
with open("test_kokoro.wav", "wb") as f:
    f.write(result.audio_bytes)
```

---

## Quality Checklist

- [ ] All speakers map to valid voices
- [ ] Audio levels normalized consistently
- [ ] SRT timestamps align with audio
- [ ] Pauses between lines sound natural
- [ ] No audio artifacts or glitches
- [ ] Output files named correctly
- [ ] Timeline JSON accurate
