# TTS & SRT Generator - Implementation Plan

## Overview

Batch lesson generator converting scripted English conversations into synchronized audio and SRT transcripts using Coqui XTTS v2, optimized for B2-level listening practice with natural US accent.

---

## 1. Technical Architecture

### 1.1 TTS Engine Selection

```
Engine: Coqui XTTS v2
Reason: Best quality for voice cloning, natural prosody, emotion control
```

| Aspect | Choice | Rationale |
|--------|--------|-----------|
| Model | XTTS v2 | Superior naturalness, speaker cloning |
| Fallback | VITS | Faster, acceptable quality for retries |
| Sample Rate | 24kHz | XTTS native, high quality |
| Output Format | WAV (intermediate), MP3 (final) | Lossless processing, portable output |

### 1.2 Voice Strategy

```json
{
  "voices": {
    "male_us_1": {
      "reference_audio": "voices/male_us_1.wav",
      "description": "Adult male, neutral US accent, conversational"
    },
    "female_us_1": {
      "reference_audio": "voices/female_us_1.wav",
      "description": "Adult female, neutral US accent, friendly"
    }
  },
  "requirements": {
    "reference_duration": "6-12 seconds",
    "reference_quality": "clean, no background noise",
    "sample_rate": 24000
  }
}
```

### 1.3 System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                        INPUT LAYER                               │
├─────────────────────────────────────────────────────────────────┤
│  Script JSON  →  Validator  →  Job Queue (Redis/In-Memory)      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      PROCESSING LAYER                            │
├─────────────────────────────────────────────────────────────────┤
│  TTS Worker  →  Audio Stitcher  →  Alignment Service            │
│      ↓              ↓                    ↓                       │
│  [per-line WAV] [combined WAV]    [adjusted timestamps]         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                       OUTPUT LAYER                               │
├─────────────────────────────────────────────────────────────────┤
│  Final Audio (MP3)  +  SRT File  +  Timeline JSON               │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Data Schemas

### 2.1 Input Script Schema

```json
{
  "$schema": "script-input-v1",
  "lesson_id": "lesson_001",
  "title": "At the Coffee Shop",
  "level": "B2",
  "lines": [
    {
      "id": 1,
      "speaker": "male_us_1",
      "text": "Hi, can I get a large latte please?",
      "emotion": "friendly",
      "pause_after_ms": 500
    },
    {
      "id": 2,
      "speaker": "female_us_1",
      "text": "Sure! Would you like any flavor shots with that?",
      "emotion": "cheerful",
      "pause_after_ms": 800
    }
  ],
  "settings": {
    "speech_rate": 1.0,
    "initial_silence_ms": 300,
    "default_pause_ms": 400
  }
}
```

### 2.2 Output Timeline JSON

```json
{
  "$schema": "timeline-output-v1",
  "lesson_id": "lesson_001",
  "audio_file": "lesson_001.mp3",
  "srt_file": "lesson_001.srt",
  "duration_ms": 12500,
  "segments": [
    {
      "id": 1,
      "speaker": "male_us_1",
      "text": "Hi, can I get a large latte please?",
      "start_ms": 300,
      "end_ms": 2850,
      "audio_duration_ms": 2550,
      "confidence": 0.95
    },
    {
      "id": 2,
      "speaker": "female_us_1",
      "text": "Sure! Would you like any flavor shots with that?",
      "start_ms": 3350,
      "end_ms": 6200,
      "audio_duration_ms": 2850,
      "confidence": 0.92
    }
  ],
  "metadata": {
    "model_version": "xtts_v2.0.3",
    "generated_at": "2025-01-15T10:30:00Z",
    "quality_score": 0.93
  }
}
```

### 2.3 SRT Output Format

```srt
1
00:00:00,300 --> 00:00:02,850
Hi, can I get a large latte please?

2
00:00:03,350 --> 00:00:06,200
Sure! Would you like any flavor shots with that?
```

---

## 3. Component Specifications

### 3.1 Script Validator

```python
# validator.py
class ScriptValidator:
    """Validates input JSON against schema and content rules."""

    def validate(self, script: dict) -> ValidationResult:
        """
        Checks:
        - Required fields present
        - Speaker IDs exist in voice registry
        - Text is non-empty, ASCII/basic punctuation only
        - Emotion values in allowed set
        - Pause values within reasonable range (0-5000ms)

        Returns:
        - ValidationResult with errors/warnings list
        """
```

**Validation Rules:**
| Field | Rule |
|-------|------|
| text | Non-empty, letters/numbers/basic punctuation only |
| speaker | Must exist in voice registry |
| emotion | One of: neutral, friendly, cheerful, serious, excited |
| pause_after_ms | 0-5000, default 400 |
| speech_rate | 0.5-1.5, default 1.0 |

### 3.2 TTS Worker

```python
# tts_worker.py
class TTSWorker:
    """Synthesizes individual lines using XTTS v2."""

    def __init__(self, model_path: str, voice_registry: dict):
        self.model = load_xtts_model(model_path)
        self.voices = voice_registry

    def synthesize_line(self, line: ScriptLine) -> SynthesisResult:
        """
        1. Load speaker reference audio
        2. Apply emotion/rate parameters
        3. Generate audio via XTTS
        4. Return WAV bytes + actual duration

        Returns:
        - SynthesisResult with audio_bytes, duration_ms, success flag
        """

    def synthesize_batch(self, lines: list[ScriptLine]) -> list[SynthesisResult]:
        """Process multiple lines, can parallelize per-speaker."""
```

**Quality Parameters:**
```python
XTTS_CONFIG = {
    "temperature": 0.7,        # Lower = more consistent
    "repetition_penalty": 2.0, # Prevent word repetition
    "top_k": 50,
    "top_p": 0.85,
    "speed": 1.0,              # Adjustable per line
    "enable_text_splitting": True
}
```

### 3.3 Audio Stitcher

```python
# audio_stitcher.py
class AudioStitcher:
    """Concatenates per-line audio with proper gaps and normalization."""

    def stitch(self, segments: list[AudioSegment], settings: StitchSettings) -> StitchResult:
        """
        1. Add initial silence
        2. Concatenate segments with pause_after gaps
        3. Normalize volume (target: -16 LUFS)
        4. Apply light compression for consistency
        5. Export as WAV and MP3

        Returns:
        - StitchResult with final audio + segment timestamps
        """
```

**Audio Processing Chain:**
```
Raw TTS Output → Trim Silence → Normalize → Add Pauses → Concatenate → Final Normalize → Export
```

### 3.4 Forced Alignment Service

```python
# alignment_service.py
class AlignmentService:
    """Adjusts timestamps using forced alignment for accuracy."""

    def align(self, audio_path: str, segments: list[Segment]) -> list[AlignedSegment]:
        """
        Uses whisper/wav2vec2 for forced alignment.

        1. Run forced alignment on combined audio
        2. Compare with estimated timestamps
        3. If drift > threshold, use aligned timestamps
        4. Calculate confidence scores

        Returns:
        - List of segments with adjusted start_ms/end_ms
        """
```

**Alignment Thresholds:**
| Metric | Threshold | Action |
|--------|-----------|--------|
| Drift per segment | > 200ms | Use aligned timestamp |
| Total drift | > 500ms | Flag for review |
| Word error rate | > 10% | Regenerate line |

### 3.5 Voice Consistency Checker

```python
# voice_checker.py
class VoiceConsistencyChecker:
    """Ensures synthesized audio matches reference voice characteristics."""

    def check_consistency(self, generated: AudioSegment, reference: AudioSegment) -> ConsistencyResult:
        """
        Compares:
        - Speaker embedding similarity (threshold: 0.85)
        - Pitch range consistency
        - Speaking rate variance

        Returns:
        - ConsistencyResult with similarity_score, passed flag
        """
```

---

## 4. Pipeline Implementation

### 4.1 Main Pipeline Flow

```python
# pipeline.py
class LessonPipeline:
    """Orchestrates the full generation pipeline."""

    async def generate_lesson(self, script: dict) -> LessonOutput:
        # Step 1: Validate
        validation = self.validator.validate(script)
        if not validation.success:
            raise ValidationError(validation.errors)

        # Step 2: Synthesize all lines
        tts_results = []
        for line in script["lines"]:
            result = await self.tts_worker.synthesize_line(line)
            if not result.success:
                result = await self.retry_with_fallback(line)
            tts_results.append(result)

        # Step 3: Stitch audio
        stitch_result = self.stitcher.stitch(
            segments=[r.audio for r in tts_results],
            settings=script["settings"]
        )

        # Step 4: Forced alignment
        aligned_segments = self.aligner.align(
            audio_path=stitch_result.wav_path,
            segments=stitch_result.segments
        )

        # Step 5: Voice consistency check
        for seg in aligned_segments:
            consistency = self.voice_checker.check_consistency(
                generated=seg.audio,
                reference=self.voices[seg.speaker].reference
            )
            seg.confidence = consistency.similarity_score

        # Step 6: Generate outputs
        return LessonOutput(
            audio_mp3=stitch_result.mp3_path,
            srt=self.generate_srt(aligned_segments),
            timeline_json=self.generate_timeline(aligned_segments, script)
        )
```

### 4.2 Error Recovery Strategy

```python
# retry_strategy.py
class RetryStrategy:
    """Handles failures with progressive fallbacks."""

    MAX_RETRIES = 3

    async def retry_with_fallback(self, line: ScriptLine, attempt: int = 1) -> SynthesisResult:
        if attempt > self.MAX_RETRIES:
            raise SynthesisError(f"Failed after {self.MAX_RETRIES} attempts")

        # Attempt 1-2: Retry with XTTS, adjusted parameters
        if attempt <= 2:
            adjusted = self.adjust_parameters(line, attempt)
            return await self.tts_worker.synthesize_line(adjusted)

        # Attempt 3: Fall back to VITS model
        return await self.vits_fallback.synthesize_line(line)

    def adjust_parameters(self, line: ScriptLine, attempt: int) -> ScriptLine:
        """Reduce temperature, simplify text if needed."""
        line.temperature = 0.5 if attempt == 2 else 0.7
        return line
```

---

## 5. Project Structure

```
TtsAndSrtGenerate/
├── src/
│   ├── __init__.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── script.py          # Input/output dataclasses
│   │   └── config.py          # Configuration models
│   ├── services/
│   │   ├── __init__.py
│   │   ├── validator.py       # Script validation
│   │   ├── tts_worker.py      # XTTS synthesis
│   │   ├── stitcher.py        # Audio concatenation
│   │   ├── aligner.py         # Forced alignment
│   │   └── voice_checker.py   # Consistency checks
│   ├── pipeline/
│   │   ├── __init__.py
│   │   ├── lesson_pipeline.py # Main orchestration
│   │   └── retry_strategy.py  # Error handling
│   └── utils/
│       ├── __init__.py
│       ├── audio.py           # Audio processing helpers
│       └── srt.py             # SRT generation
├── voices/
│   ├── male_us_1.wav
│   └── female_us_1.wav
├── tests/
│   ├── test_validator.py
│   ├── test_tts_worker.py
│   └── test_pipeline.py
├── examples/
│   └── sample_script.json
├── config/
│   └── default.yaml
├── requirements.txt
└── main.py
```

---

## 6. Quality Assurance

### 6.1 Automated Checks

| Check | Tool | Threshold | Action on Fail |
|-------|------|-----------|----------------|
| Alignment drift | Whisper | > 200ms | Use aligned timestamps |
| ASR accuracy | Whisper | WER > 10% | Regenerate line |
| Voice similarity | Resemblyzer | < 0.85 | Flag for review |
| Audio clipping | PyDub | > -1dB | Re-normalize |
| Silence detection | PyDub | > 3s gap | Warning |

### 6.2 Voice Sample Validation

```python
# Run before each batch to ensure model consistency
def validate_voice_samples():
    """
    1. Synthesize reference phrase with each voice
    2. Compare embedding to stored baseline
    3. Alert if similarity < 0.90 (model may have changed)
    """
    REFERENCE_PHRASE = "The quick brown fox jumps over the lazy dog."

    for voice_id, voice in VOICE_REGISTRY.items():
        generated = tts.synthesize(REFERENCE_PHRASE, voice)
        similarity = compare_embeddings(generated, voice.baseline)
        if similarity < 0.90:
            raise VoiceConsistencyError(f"{voice_id} drift detected")
```

---

## 7. Configuration

### 7.1 Default Config

```yaml
# config/default.yaml
tts:
  model: "xtts_v2"
  model_path: "./models/xtts_v2"
  device: "cuda"  # or "cpu"

audio:
  sample_rate: 24000
  output_format: "mp3"
  mp3_bitrate: 192
  normalization_target: -16  # LUFS

synthesis:
  temperature: 0.7
  repetition_penalty: 2.0
  default_pause_ms: 400
  initial_silence_ms: 300

alignment:
  enabled: true
  drift_threshold_ms: 200
  wer_threshold: 0.10

voice_check:
  enabled: true
  similarity_threshold: 0.85

retry:
  max_attempts: 3
  fallback_model: "vits"
```

---

## 8. Dependencies

```txt
# requirements.txt
TTS>=0.22.0              # Coqui TTS (includes XTTS)
torch>=2.0.0
torchaudio>=2.0.0
pydub>=0.25.1            # Audio manipulation
librosa>=0.10.0          # Audio analysis
resemblyzer>=0.1.3       # Speaker embeddings
openai-whisper>=20231117 # Forced alignment
pydantic>=2.0            # Data validation
pyyaml>=6.0              # Config loading
numpy>=1.24.0
```

---

## 9. Implementation Order

### Phase 1: Core TTS (MVP)
1. Set up project structure
2. Implement `ScriptValidator` with JSON schema
3. Implement `TTSWorker` with XTTS v2
4. Basic `AudioStitcher` (concatenate + normalize)
5. SRT generation from estimated timestamps
6. CLI entry point for single lesson

### Phase 2: Quality Enhancement
7. Add `AlignmentService` with Whisper
8. Implement `VoiceConsistencyChecker`
9. Add retry strategy with VITS fallback
10. Automated quality checks

### Phase 3: Production Ready
11. Batch processing support
12. PostgreSQL integration for job history
13. API endpoint (optional)
14. Monitoring and logging

---

## 10. Usage Example

```bash
# Generate a lesson
python main.py generate --input examples/sample_script.json --output ./output/

# Output:
# ./output/lesson_001.mp3
# ./output/lesson_001.srt
# ./output/lesson_001.json
```

```python
# Programmatic usage
from src.pipeline import LessonPipeline

pipeline = LessonPipeline.from_config("config/default.yaml")

with open("script.json") as f:
    script = json.load(f)

result = await pipeline.generate_lesson(script)
print(f"Generated: {result.audio_mp3}")
print(f"Duration: {result.duration_ms}ms")
print(f"Quality score: {result.quality_score}")
```
