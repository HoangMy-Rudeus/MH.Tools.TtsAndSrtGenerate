# Code Explanation Guide

Deep-dive explanations of how TTS & SRT Generator works internally.

---

## Table of Contents

1. [Overview](#overview)
2. [The Pipeline Pattern](#the-pipeline-pattern)
3. [Step-by-Step: How Audio Gets Generated](#step-by-step-how-audio-gets-generated)
4. [Key Components Explained](#key-components-explained)
5. [Data Transformations](#data-transformations)
6. [Design Patterns Used](#design-patterns-used)
7. [Common Pitfalls & Best Practices](#common-pitfalls--best-practices)

---

## Overview

### What Does This Code Do?

```
┌──────────────────────────────────────────────────────────────────┐
│                    HIGH-LEVEL OVERVIEW                            │
│                                                                   │
│   JSON Script  ──▶  TTS Engine  ──▶  Audio Processing  ──▶  Output│
│                                                                   │
│   "Hello!"     ──▶  [XTTS v2]   ──▶  [Stitch + Align]  ──▶  MP3  │
│   "Hi there!"       generates        combines audio       + SRT   │
│                     speech            with timing         + JSON  │
└──────────────────────────────────────────────────────────────────┘
```

**Simple Analogy**: Think of it like a recording studio:
1. **Script** = The dialogue actors will read
2. **TTS Worker** = The voice actors (AI-powered)
3. **Stitcher** = The audio engineer who combines takes
4. **Aligner** = Quality control checking timing accuracy
5. **Output** = The final podcast/lesson file

### Complexity Analysis

| Metric | Value | Explanation |
|--------|-------|-------------|
| **Lines of Code** | ~1,200 | Medium-sized project |
| **Classes** | 15 | Well-organized OOP |
| **Key Concepts** | 6 | Pydantic, async-capable, type hints |
| **Difficulty** | Intermediate | Requires Python + audio knowledge |

### Key Concepts Used

```
┌─────────────────────────────────────────────────────────────────┐
│ PROGRAMMING CONCEPTS IN THIS CODEBASE                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Pydantic   │  │  Type Hints  │  │   Logging    │          │
│  │   Models     │  │   (Python    │  │  (structured │          │
│  │              │  │    3.10+)    │  │   output)    │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Factory    │  │    Lazy      │  │   Pipeline   │          │
│  │   Pattern    │  │   Loading    │  │   Pattern    │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## The Pipeline Pattern

### What is a Pipeline?

A pipeline processes data through sequential stages, where each stage transforms the data and passes it to the next.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        PIPELINE PATTERN                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   Input ──▶ [Stage 1] ──▶ [Stage 2] ──▶ [Stage 3] ──▶ [Stage 4] ──▶ Output
│                │              │              │              │            │
│             Validate      Synthesize      Stitch         Align          │
│                                                                          │
│   Each stage:                                                            │
│   ✓ Has a single responsibility                                         │
│   ✓ Receives data from previous stage                                   │
│   ✓ Transforms and passes to next stage                                 │
│   ✓ Can fail independently (error isolation)                            │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### How LessonPipeline Implements This

```python
# src/pipeline/lesson_pipeline.py (simplified)

class LessonPipeline:
    def generate(self, script, output_dir):
        # Stage 1: VALIDATE
        validation = self.validator.validate(script)
        if not validation.success:
            raise PipelineError("Validation failed")

        parsed = ScriptInput(**script)  # Transform: dict → ScriptInput

        # Stage 2: SYNTHESIZE
        synthesis_results = self._synthesize_with_retry(parsed)
        # Transform: ScriptInput → list[SynthesisResult]

        # Stage 3: STITCH
        stitch_result = self.stitcher.stitch(
            synthesis_results, parsed.lines, output_dir, parsed.lesson_id
        )
        # Transform: list[SynthesisResult] → StitchResult (combined audio)

        # Stage 4: ALIGN
        alignment_result = self.aligner.align(
            stitch_result.wav_path, stitch_result.segments, texts
        )
        # Transform: StitchResult → AlignmentResult (accurate timestamps)

        # Stage 5: OUTPUT
        return LessonOutput(...)  # Final output package
```

### Why Use a Pipeline?

| Benefit | Explanation |
|---------|-------------|
| **Modularity** | Each stage can be tested independently |
| **Flexibility** | Easy to add/remove stages |
| **Error Isolation** | Failures don't cascade unpredictably |
| **Debugging** | Clear where problems occur |

---

## Step-by-Step: How Audio Gets Generated

### Step 1: Validation

**Purpose**: Ensure the input is valid before expensive processing.

```
┌─────────────────────────────────────────────────────────────────┐
│                     VALIDATION FLOW                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   JSON Input                                                     │
│       │                                                          │
│       ▼                                                          │
│   ┌─────────────────────────────────────┐                       │
│   │      Pydantic Schema Check          │                       │
│   │   - Required fields present?        │                       │
│   │   - Types correct?                  │──▶ Fail: Schema Error │
│   │   - Values in valid range?          │                       │
│   └─────────────────────────────────────┘                       │
│       │ Pass                                                     │
│       ▼                                                          │
│   ┌─────────────────────────────────────┐                       │
│   │      Content Validation             │                       │
│   │   - Voice IDs exist?                │──▶ Fail: Voice Error  │
│   │   - Text has valid characters?      │                       │
│   │   - No duplicate line IDs?          │                       │
│   └─────────────────────────────────────┘                       │
│       │ Pass                                                     │
│       ▼                                                          │
│   ValidationResult(success=True)                                 │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Code Walkthrough** (`src/services/validator.py`):

```python
class ScriptValidator:
    # Regex pattern for allowed text characters
    TEXT_PATTERN = re.compile(r"^[a-zA-Z0-9\s.,!?'\"-:;()]+$")

    def validate(self, script: dict) -> ValidationResult:
        errors = []

        # PHASE 1: Pydantic validates structure
        try:
            parsed = ScriptInput(**script)  # Pydantic does the heavy lifting
        except PydanticValidationError as e:
            # Convert Pydantic errors to our format
            for err in e.errors():
                errors.append(ValidationError(
                    field=".".join(str(loc) for loc in err["loc"]),
                    message=err["msg"]
                ))
            return ValidationResult(success=False, errors=errors)

        # PHASE 2: Custom content validation
        for line in parsed.lines:
            line_errors, line_warnings = self._validate_line(line)
            errors.extend(line_errors)

        return ValidationResult(success=len(errors) == 0, errors=errors)
```

**Key Insight**: Using Pydantic for schema validation means we write less code and get better error messages.

---

### Step 2: TTS Synthesis

**Purpose**: Convert text to speech using voice cloning.

```
┌─────────────────────────────────────────────────────────────────┐
│                    TTS SYNTHESIS FLOW                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   For each ScriptLine:                                          │
│                                                                  │
│   ┌─────────────┐                                               │
│   │  Get Voice  │  ◀── Look up reference audio from registry   │
│   │  Reference  │      voices/male_us_1.wav                     │
│   └──────┬──────┘                                               │
│          │                                                       │
│          ▼                                                       │
│   ┌─────────────┐                                               │
│   │ Apply Style │  ◀── Emotion affects speed:                   │
│   │ Parameters  │      cheerful=1.05x, serious=0.95x           │
│   └──────┬──────┘                                               │
│          │                                                       │
│          ▼                                                       │
│   ┌─────────────────────────────────────────┐                   │
│   │            XTTS v2 Model                 │                   │
│   │                                          │                   │
│   │   Text: "Hello, how are you?"           │                   │
│   │   Voice: male_us_1.wav (reference)      │                   │
│   │   Language: "en"                         │                   │
│   │   Speed: 1.0                             │                   │
│   │                                          │                   │
│   │   ──────────────────────────             │                   │
│   │   │ Neural Network Magic │              │                   │
│   │   ──────────────────────────             │                   │
│   │                                          │                   │
│   │   Output: numpy array of audio samples   │                   │
│   └──────────────────┬──────────────────────┘                   │
│                      │                                           │
│                      ▼                                           │
│   ┌─────────────┐                                               │
│   │ Convert to  │  ◀── numpy → 16-bit PCM WAV bytes            │
│   │ WAV Bytes   │                                               │
│   └──────┬──────┘                                               │
│          │                                                       │
│          ▼                                                       │
│   SynthesisResult(                                              │
│       line_id=1,                                                 │
│       success=True,                                              │
│       audio_bytes=b"RIFF...",                                   │
│       duration_ms=2500                                           │
│   )                                                              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Code Walkthrough** (`src/services/tts_worker.py`):

```python
class TTSWorker:
    # Emotion affects speech speed
    EMOTION_STYLES = {
        Emotion.NEUTRAL: {"speed": 1.0},
        Emotion.FRIENDLY: {"speed": 1.0},
        Emotion.CHEERFUL: {"speed": 1.05},  # Slightly faster
        Emotion.SERIOUS: {"speed": 0.95},   # Slightly slower
        Emotion.EXCITED: {"speed": 1.1},    # Noticeably faster
    }

    def synthesize_line(self, line: ScriptLine) -> SynthesisResult:
        # Lazy loading - only load model when first needed
        if not self._loaded:
            self.load_model()

        # Get voice reference file
        voice = self.voice_registry.get(line.speaker)

        # Calculate speed based on emotion + any override
        style = self.EMOTION_STYLES.get(line.emotion, {})
        speed = line.speech_rate or style.get("speed", 1.0)

        # THE MAGIC HAPPENS HERE
        wav = self.model.tts(
            text=line.text,
            speaker_wav=str(voice.reference_path),  # Clone this voice
            language="en",
            speed=speed,
        )

        # Convert numpy array to WAV bytes
        audio_bytes = self._numpy_to_wav_bytes(wav, sample_rate)

        return SynthesisResult(
            line_id=line.id,
            success=True,
            audio_bytes=audio_bytes,
            duration_ms=int(len(wav) / sample_rate * 1000),
        )
```

**Key Insight**: Lazy loading (`if not self._loaded`) means the 2GB+ model only loads when actually needed, not at startup.

---

### Step 3: Audio Stitching

**Purpose**: Combine individual audio clips into one continuous file.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        AUDIO STITCHING PROCESS                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   Input: list[SynthesisResult] with audio bytes                         │
│                                                                          │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │                    TIMELINE CONSTRUCTION                         │   │
│   │                                                                  │   │
│   │   0ms        300ms                    2800ms    3400ms          │   │
│   │   │──────────│──────────────────────────│────────│              │   │
│   │   │ SILENCE  │      LINE 1 AUDIO        │ PAUSE  │              │   │
│   │   │ (initial)│    "Hello, world!"       │ 600ms  │              │   │
│   │   └──────────┴──────────────────────────┴────────┘              │   │
│   │                                                                  │   │
│   │                                    3400ms              5800ms    │   │
│   │                                    │────────────────────│        │   │
│   │                                    │    LINE 2 AUDIO    │        │   │
│   │                                    │  "How are you?"    │        │   │
│   │                                    └────────────────────┘        │   │
│   │                                                                  │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│   Processing Steps:                                                      │
│                                                                          │
│   1. Start with initial silence (300ms default)                         │
│   2. For each audio segment:                                             │
│      a. Trim silence from start/end of clip                             │
│      b. Record start timestamp                                           │
│      c. Append to combined audio                                         │
│      d. Record end timestamp                                             │
│      e. Add pause (from script metadata)                                 │
│   3. Normalize entire audio to -16 LUFS                                 │
│   4. Export as WAV (lossless) and MP3 (compressed)                      │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

**Code Walkthrough** (`src/services/stitcher.py`):

```python
def stitch(self, synthesis_results, lines, output_dir, filename_base):
    # Build a lookup: line_id → pause duration
    pause_map = {line.id: line.pause_after_ms for line in lines}

    # Start with initial silence
    combined = add_silence(
        self.synthesis_config.initial_silence_ms,  # e.g., 300ms
        self.audio_config.sample_rate
    )
    current_position_ms = self.synthesis_config.initial_silence_ms

    segments = []  # Track timing for each segment

    for result in synthesis_results:
        if not result.success:
            continue  # Skip failed syntheses

        # Convert bytes to pydub segment
        segment = wav_bytes_to_segment(result.audio_bytes)

        # IMPORTANT: Trim silence from TTS output
        # TTS often adds unwanted silence at start/end
        segment = trim_silence(segment)

        # Record WHERE this segment starts in the timeline
        segment_duration = get_audio_duration_ms(segment)
        segments.append(SegmentTiming(
            line_id=result.line_id,
            start_ms=current_position_ms,
            end_ms=current_position_ms + segment_duration,
            audio_duration_ms=segment_duration,
        ))

        # Append to combined audio
        combined += segment
        current_position_ms += segment_duration

        # Add pause between lines
        pause_ms = pause_map.get(result.line_id, 400)  # Default 400ms
        if pause_ms > 0:
            combined += add_silence(pause_ms, self.audio_config.sample_rate)
            current_position_ms += pause_ms

    # Normalize for consistent volume
    combined = normalize_audio(combined, self.audio_config.normalization_target)

    # Export both formats
    export_audio(combined, wav_path, format="wav")
    export_audio(combined, mp3_path, format="mp3", bitrate="192k")

    return StitchResult(
        success=True,
        wav_path=wav_path,
        mp3_path=mp3_path,
        segments=segments,  # CRITICAL: These timestamps enable SRT
    )
```

**Key Insight**: The `segments` list tracks exactly where each line starts and ends - this is what makes subtitles possible.

---

### Step 4: Forced Alignment

**Purpose**: Verify and correct timestamps using ASR (Automatic Speech Recognition).

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      FORCED ALIGNMENT PROCESS                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   Why Alignment?                                                         │
│   ──────────────                                                         │
│   TTS duration estimates are approximate. Actual speech may be          │
│   faster or slower than expected. Alignment corrects this.              │
│                                                                          │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │                                                                  │   │
│   │   ESTIMATED:  │──Line 1──│    │──Line 2──│                      │   │
│   │               0    2500   3100    5600                          │   │
│   │                                                                  │   │
│   │   ACTUAL:     │──Line 1────│  │──Line 2──│                      │   │
│   │   (Whisper)   0      2800   3200   5800                         │   │
│   │                                                                  │   │
│   │   DRIFT:          +300ms     +100ms   +200ms                    │   │
│   │                                                                  │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│   How It Works:                                                          │
│   ──────────────                                                         │
│                                                                          │
│   1. Whisper transcribes the combined audio                             │
│   2. Whisper provides word-level timestamps                              │
│   3. We match our segments to Whisper's words                           │
│   4. If drift > threshold (200ms), use Whisper's timing                 │
│   5. Calculate confidence scores                                         │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

**Code Walkthrough** (`src/services/aligner.py`):

```python
def align(self, audio_path, segments, texts):
    # Skip if disabled in config
    if not self.config.enabled:
        return AlignmentResult(success=True, segments=[...])  # Pass-through

    # Lazy load Whisper model
    self._load_model()

    # Transcribe with word timestamps
    result = self._model.transcribe(
        str(audio_path),
        word_timestamps=True,  # CRITICAL: We need per-word timing
        language="en",
    )

    # Extract word timings from Whisper output
    word_timings = self._extract_word_timings(result)
    # Result: [{"word": "Hello", "start_ms": 320, "end_ms": 580}, ...]

    # Match our segments to Whisper's words
    aligned_segments = self._match_segments(segments, texts, word_timings)

    return AlignmentResult(success=True, segments=aligned_segments)

def _match_segments(self, segments, texts, word_timings):
    aligned = []
    word_idx = 0  # Track position in word_timings

    for seg in segments:
        text = texts.get(seg.line_id, "")
        num_words = len(text.split())

        # Find where this segment's words are in Whisper output
        if word_idx < len(word_timings):
            best_start_ms = word_timings[word_idx]["start_ms"]
            best_end_ms = word_timings[word_idx + num_words - 1]["end_ms"]
            word_idx += num_words

        # Calculate how much our estimate was off
        start_drift = best_start_ms - seg.start_ms
        end_drift = best_end_ms - seg.end_ms
        avg_drift = (start_drift + end_drift) // 2

        # Only use aligned timestamps if drift is significant
        use_aligned = abs(avg_drift) > self.config.drift_threshold_ms  # 200ms

        aligned.append(AlignedSegment(
            line_id=seg.line_id,
            original_start_ms=seg.start_ms,
            original_end_ms=seg.end_ms,
            aligned_start_ms=best_start_ms if use_aligned else seg.start_ms,
            aligned_end_ms=best_end_ms if use_aligned else seg.end_ms,
            drift_ms=avg_drift,
            confidence=0.9 if use_aligned else 1.0,  # Lower if we had to correct
        ))

    return aligned
```

**Key Insight**: The threshold-based approach means small variations are ignored (stability), but large errors are corrected (accuracy).

---

### Step 5: Output Generation

**Purpose**: Create final deliverables (MP3, SRT, JSON).

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      OUTPUT GENERATION                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   From aligned segments, we generate:                                    │
│                                                                          │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │                         SRT FILE                                 │   │
│   │                                                                  │   │
│   │   1                                                              │   │
│   │   00:00:00,320 --> 00:00:02,850                                 │   │
│   │   Hello, how are you today?                                      │   │
│   │                                                                  │   │
│   │   2                                                              │   │
│   │   00:00:03,400 --> 00:00:05,800                                 │   │
│   │   I'm doing great, thanks!                                       │   │
│   │                                                                  │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│   SRT Format:                                                            │
│   - Index number                                                         │
│   - Timestamp: HH:MM:SS,mmm --> HH:MM:SS,mmm                           │
│   - Text content                                                         │
│   - Blank line separator                                                 │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

**Code Walkthrough** (`src/utils/srt.py`):

```python
def format_timestamp(ms: int) -> str:
    """
    Convert milliseconds to SRT timestamp format.

    Example: 3661500 → "01:01:01,500"
    """
    hours = ms // 3600000           # 3661500 // 3600000 = 1
    minutes = (ms % 3600000) // 60000   # 61500 // 60000 = 1
    seconds = (ms % 60000) // 1000      # 1500 // 1000 = 1
    milliseconds = ms % 1000            # 1500 % 1000 = 500

    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"
    # Returns: "01:01:01,500"

def generate_srt(segments: list[Segment]) -> str:
    """Build SRT content from segments."""
    lines = []

    for idx, segment in enumerate(segments, start=1):
        start = format_timestamp(segment.start_ms)
        end = format_timestamp(segment.end_ms)

        lines.append(str(idx))              # "1"
        lines.append(f"{start} --> {end}")  # "00:00:00,320 --> 00:00:02,850"
        lines.append(segment.text)          # "Hello, how are you today?"
        lines.append("")                    # Blank line separator

    return "\n".join(lines)
```

**Key Insight**: The timestamp math uses integer division (`//`) and modulo (`%`) to extract hours, minutes, seconds, milliseconds - a common pattern for time formatting.

---

## Key Components Explained

### Pydantic Models

**What They Are**: Data classes with automatic validation.

```python
# Traditional Python class
class ScriptLine:
    def __init__(self, id, speaker, text, emotion="neutral", pause_after_ms=400):
        if not isinstance(id, int):
            raise TypeError("id must be int")
        if not text:
            raise ValueError("text cannot be empty")
        # ... more validation
        self.id = id
        self.speaker = speaker
        # ... etc

# With Pydantic - same functionality, less code
class ScriptLine(BaseModel):
    id: int = Field(..., description="Unique line identifier")
    speaker: str = Field(..., description="Voice ID from registry")
    text: str = Field(..., min_length=1, description="Text to synthesize")
    emotion: Emotion = Field(default=Emotion.NEUTRAL)
    pause_after_ms: int = Field(default=400, ge=0, le=5000)
```

**Benefits**:
- Automatic type checking
- Clear error messages
- JSON serialization built-in
- Documentation via Field descriptions

### Lazy Loading Pattern

**What It Is**: Defer expensive operations until actually needed.

```python
class TTSWorker:
    def __init__(self, ...):
        self.model = None       # Don't load yet
        self._loaded = False

    def load_model(self):
        if self._loaded:
            return              # Already loaded, skip

        # EXPENSIVE: 2GB+ model download and GPU allocation
        self.model = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
        self._loaded = True

    def synthesize_line(self, line):
        if not self._loaded:
            self.load_model()   # Load on first use
        # ... use self.model
```

**Why**:
- Faster startup time
- Memory efficient if feature isn't used
- Allows validation before heavy lifting

### Factory Pattern

**What It Is**: Create objects through class methods instead of `__init__`.

```python
class LessonPipeline:
    def __init__(self, config: AppConfig):
        # Regular constructor
        self.config = config
        # ... setup services

    @classmethod
    def from_config_file(cls, config_path: str) -> "LessonPipeline":
        """Factory method: Create from file path."""
        config = AppConfig.from_yaml(config_path)
        return cls(config)

    @classmethod
    def from_default_config(cls) -> "LessonPipeline":
        """Factory method: Create with defaults."""
        return cls(AppConfig.default())

# Usage options:
pipeline = LessonPipeline(custom_config)              # Direct
pipeline = LessonPipeline.from_config_file("cfg.yaml") # From file
pipeline = LessonPipeline.from_default_config()        # Defaults
```

**Why**:
- Multiple ways to create objects
- Cleaner than complex `__init__` logic
- Self-documenting intent

---

## Data Transformations

### The Journey of Data

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    DATA TRANSFORMATION JOURNEY                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   STAGE 1: Input                                                         │
│   ────────────────                                                       │
│   dict (JSON) ──▶ ScriptInput (Pydantic model)                          │
│                                                                          │
│   {                          ScriptInput(                                │
│     "lesson_id": "001",        lesson_id="001",                         │
│     "lines": [...]             lines=[ScriptLine(...), ...]             │
│   }                          )                                           │
│                                                                          │
│   STAGE 2: Synthesis                                                     │
│   ──────────────────                                                     │
│   ScriptLine ──▶ SynthesisResult                                        │
│                                                                          │
│   ScriptLine(                SynthesisResult(                           │
│     id=1,                      line_id=1,                               │
│     text="Hello",              audio_bytes=b"RIFF...",                  │
│     speaker="male_us_1"        duration_ms=1500                         │
│   )                          )                                           │
│                                                                          │
│   STAGE 3: Stitching                                                     │
│   ──────────────────                                                     │
│   list[SynthesisResult] ──▶ StitchResult                                │
│                                                                          │
│   [SynthesisResult,          StitchResult(                              │
│    SynthesisResult,            wav_path="out.wav",                      │
│    ...]                        segments=[SegmentTiming(...)]            │
│                              )                                           │
│                                                                          │
│   STAGE 4: Alignment                                                     │
│   ──────────────────                                                     │
│   SegmentTiming ──▶ AlignedSegment                                      │
│                                                                          │
│   SegmentTiming(             AlignedSegment(                            │
│     start_ms=300,              original_start_ms=300,                   │
│     end_ms=1800                aligned_start_ms=320,  ◀── Corrected     │
│   )                            drift_ms=20                              │
│                              )                                           │
│                                                                          │
│   STAGE 5: Output                                                        │
│   ───────────────                                                        │
│   AlignedSegment ──▶ Segment ──▶ LessonOutput                           │
│                                                                          │
│   AlignedSegment(...)  ──▶  Segment(              LessonOutput(         │
│                               id=1,                 audio_file="x.mp3", │
│                               start_ms=320,         srt_file="x.srt",   │
│                               end_ms=1850,          segments=[...]      │
│                               text="Hello"        )                     │
│                             )                                            │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Design Patterns Used

### 1. Pipeline Pattern
**Where**: `LessonPipeline.generate()`
**Purpose**: Sequential processing with clear stages

### 2. Factory Method Pattern
**Where**: `LessonPipeline.from_config_file()`, `AppConfig.from_yaml()`
**Purpose**: Multiple object creation strategies

### 3. Lazy Initialization
**Where**: `TTSWorker.load_model()`, `AlignmentService._load_model()`
**Purpose**: Defer expensive operations

### 4. Registry Pattern
**Where**: `voice_registry` dictionary
**Purpose**: Central lookup for voice configurations

### 5. Result Object Pattern
**Where**: `ValidationResult`, `SynthesisResult`, `StitchResult`, `AlignmentResult`
**Purpose**: Encapsulate success/failure with data

```python
# Result Object Pattern example
class SynthesisResult(BaseModel):
    line_id: int
    success: bool                    # Was it successful?
    audio_bytes: Optional[bytes]     # The data (if success)
    error: Optional[str]             # The error (if failure)

# Usage
result = worker.synthesize_line(line)
if result.success:
    process(result.audio_bytes)
else:
    log_error(result.error)
```

---

## Common Pitfalls & Best Practices

### Pitfall 1: Not Validating Before Processing

```python
# BAD: Start expensive synthesis without validation
def generate_bad(script):
    for line in script["lines"]:
        audio = tts.synthesize(line["text"])  # Might fail on line 99

# GOOD: Validate everything first
def generate_good(script):
    validation = validator.validate(script)
    if not validation.success:
        return early_with_errors(validation.errors)

    for line in script["lines"]:
        audio = tts.synthesize(line["text"])  # Now we know it will work
```

### Pitfall 2: Loading Models at Import Time

```python
# BAD: Model loads when module is imported
class TTSWorker:
    model = TTS("xtts_v2")  # SLOW: Loads immediately

# GOOD: Load only when needed
class TTSWorker:
    def __init__(self):
        self.model = None

    def _ensure_model_loaded(self):
        if self.model is None:
            self.model = TTS("xtts_v2")
```

### Pitfall 3: Hardcoding Configuration

```python
# BAD: Magic numbers everywhere
combined = add_silence(300, 24000)  # What are these?

# GOOD: Use configuration
combined = add_silence(
    self.config.initial_silence_ms,  # Clear what this is
    self.config.sample_rate
)
```

### Pitfall 4: Silent Failures

```python
# BAD: Errors disappear
def synthesize(line):
    try:
        return do_synthesis(line)
    except:
        pass  # What happened?

# GOOD: Explicit error handling with result objects
def synthesize(line) -> SynthesisResult:
    try:
        audio = do_synthesis(line)
        return SynthesisResult(success=True, audio_bytes=audio)
    except Exception as e:
        logger.error(f"Synthesis failed: {e}")
        return SynthesisResult(success=False, error=str(e))
```

---

## Practice Exercise

Try to understand this code flow:

```python
# Given this input:
script = {
    "lesson_id": "test",
    "title": "Test",
    "lines": [
        {"id": 1, "speaker": "male_us_1", "text": "Hello!", "pause_after_ms": 500},
        {"id": 2, "speaker": "female_us_1", "text": "Hi there!", "pause_after_ms": 300}
    ]
}

# Trace through:
# 1. What does ScriptInput(**script) produce?
# 2. After synthesis, what does synthesis_results look like?
# 3. After stitching with initial_silence=300ms, what are the segment timings?
# 4. What does the final SRT file contain?
```

**Hint**: Try drawing the timeline:
```
0ms    300ms        ???ms    ???ms        ???ms
|------|------------|--------|------------|------|
silence  "Hello!"    pause    "Hi there!"  pause
```
