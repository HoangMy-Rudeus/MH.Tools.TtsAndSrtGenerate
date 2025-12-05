# Architecture Overview

Technical architecture documentation for TTS & SRT Generator.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              INPUT LAYER                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌──────────────┐     ┌──────────────────┐     ┌──────────────────┐       │
│   │  JSON Script │────▶│  ScriptValidator │────▶│   ScriptInput    │       │
│   │    (file)    │     │    (Pydantic)    │     │   (validated)    │       │
│   └──────────────┘     └──────────────────┘     └──────────────────┘       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PROCESSING LAYER                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌──────────────────────────────────────────────────────────────────┐      │
│   │                        LessonPipeline                             │      │
│   │                                                                   │      │
│   │  ┌─────────────┐   ┌─────────────┐   ┌─────────────────────┐    │      │
│   │  │  TTSWorker  │──▶│  Stitcher   │──▶│  AlignmentService   │    │      │
│   │  │  (XTTS v2)  │   │  (pydub)    │   │    (Whisper)        │    │      │
│   │  └─────────────┘   └─────────────┘   └─────────────────────┘    │      │
│   │        │                  │                    │                 │      │
│   │        ▼                  ▼                    ▼                 │      │
│   │  ┌─────────────┐   ┌─────────────┐   ┌─────────────────────┐    │      │
│   │  │ per-line    │   │ combined    │   │ aligned timestamps  │    │      │
│   │  │ WAV audio   │   │ audio file  │   │ with confidence     │    │      │
│   │  └─────────────┘   └─────────────┘   └─────────────────────┘    │      │
│   │                                                                   │      │
│   └──────────────────────────────────────────────────────────────────┘      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                             OUTPUT LAYER                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐         │
│   │    Audio File    │  │     SRT File     │  │   Timeline JSON  │         │
│   │   (MP3/WAV)      │  │   (subtitles)    │  │   (metadata)     │         │
│   └──────────────────┘  └──────────────────┘  └──────────────────┘         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         src/                                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────┐                                            │
│  │     models/     │  Data structures (Pydantic)                │
│  ├─────────────────┤                                            │
│  │  script.py      │  ScriptInput, ScriptLine, Segment, etc.    │
│  │  config.py      │  AppConfig, TTSConfig, AudioConfig, etc.   │
│  └─────────────────┘                                            │
│           │                                                      │
│           ▼                                                      │
│  ┌─────────────────┐                                            │
│  │    services/    │  Core business logic                       │
│  ├─────────────────┤                                            │
│  │  validator.py   │  Script validation                         │
│  │  tts_worker.py  │  XTTS v2 synthesis                        │
│  │  stitcher.py    │  Audio concatenation                       │
│  │  aligner.py     │  Whisper forced alignment                  │
│  │  voice_checker  │  Voice consistency validation              │
│  └─────────────────┘                                            │
│           │                                                      │
│           ▼                                                      │
│  ┌─────────────────┐                                            │
│  │    pipeline/    │  Orchestration                             │
│  ├─────────────────┤                                            │
│  │  lesson_pipeline│  Main generation pipeline                  │
│  └─────────────────┘                                            │
│           │                                                      │
│           ▼                                                      │
│  ┌─────────────────┐                                            │
│  │     utils/      │  Helper functions                          │
│  ├─────────────────┤                                            │
│  │  audio.py       │  Audio processing (normalize, trim, etc.)  │
│  │  srt.py         │  SRT generation and parsing                │
│  └─────────────────┘                                            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Pipeline Flow

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         LESSON GENERATION PIPELINE                        │
└──────────────────────────────────────────────────────────────────────────┘

    Input Script                                                    Output
    ┌─────────┐                                              ┌─────────────┐
    │  JSON   │                                              │ MP3 + SRT + │
    │ Script  │                                              │    JSON     │
    └────┬────┘                                              └──────▲──────┘
         │                                                          │
         ▼                                                          │
┌─────────────────┐                                                 │
│  Step 1:        │                                                 │
│  VALIDATE       │◀─── ScriptValidator                             │
│                 │     - Schema validation (Pydantic)              │
│                 │     - Voice registry check                      │
│                 │     - Character validation                      │
└────────┬────────┘                                                 │
         │ ScriptInput                                              │
         ▼                                                          │
┌─────────────────┐                                                 │
│  Step 2:        │                                                 │
│  SYNTHESIZE     │◀─── TTSWorker                                   │
│                 │     - Load XTTS v2 model                        │
│                 │     - Generate per-line audio                   │
│                 │     - Retry on failure (up to 3x)              │
└────────┬────────┘                                                 │
         │ list[SynthesisResult]                                    │
         ▼                                                          │
┌─────────────────┐                                                 │
│  Step 3:        │                                                 │
│  STITCH         │◀─── AudioStitcher                               │
│                 │     - Trim silence from segments                │
│                 │     - Add pauses between lines                  │
│                 │     - Normalize to -16 LUFS                     │
│                 │     - Export WAV + MP3                          │
└────────┬────────┘                                                 │
         │ StitchResult (audio + segment timings)                   │
         ▼                                                          │
┌─────────────────┐                                                 │
│  Step 4:        │                                                 │
│  ALIGN          │◀─── AlignmentService                            │
│                 │     - Transcribe with Whisper                   │
│                 │     - Extract word timestamps                   │
│                 │     - Adjust timing if drift > threshold        │
│                 │     - Calculate confidence scores               │
└────────┬────────┘                                                 │
         │ AlignmentResult (adjusted timings)                       │
         ▼                                                          │
┌─────────────────┐                                                 │
│  Step 5:        │                                                 │
│  OUTPUT         │                                                 │
│                 │     - Generate SRT file                         │
│                 │     - Generate timeline JSON                    │
│                 │     - Calculate quality score                   │
└────────┬────────┘                                                 │
         │                                                          │
         └──────────────────────────────────────────────────────────┘
```

---

## Data Flow

```
┌────────────────────────────────────────────────────────────────────────┐
│                            DATA FLOW                                    │
└────────────────────────────────────────────────────────────────────────┘

Script JSON
    │
    ▼
┌─────────────────────────────────────────────────────────────────────┐
│ {                                                                    │
│   "lesson_id": "coffee_shop_001",                                   │
│   "title": "At the Coffee Shop",                                    │
│   "lines": [                                                        │
│     {"id": 1, "speaker": "male_us_1", "text": "Hello!", ...},      │
│     {"id": 2, "speaker": "female_us_1", "text": "Hi!", ...}        │
│   ]                                                                 │
│ }                                                                    │
└─────────────────────────────────────────────────────────────────────┘
    │
    │ Validate & Parse
    ▼
┌─────────────────────────────────────────────────────────────────────┐
│ ScriptInput(                                                         │
│   lesson_id="coffee_shop_001",                                      │
│   lines=[ScriptLine(id=1, ...), ScriptLine(id=2, ...)]             │
│ )                                                                    │
└─────────────────────────────────────────────────────────────────────┘
    │
    │ Synthesize each line
    ▼
┌─────────────────────────────────────────────────────────────────────┐
│ [                                                                    │
│   SynthesisResult(line_id=1, audio_bytes=b"...", duration_ms=2500), │
│   SynthesisResult(line_id=2, audio_bytes=b"...", duration_ms=1800)  │
│ ]                                                                    │
└─────────────────────────────────────────────────────────────────────┘
    │
    │ Stitch together
    ▼
┌─────────────────────────────────────────────────────────────────────┐
│ StitchResult(                                                        │
│   wav_path="output/coffee_shop_001.wav",                            │
│   mp3_path="output/coffee_shop_001.mp3",                            │
│   segments=[                                                         │
│     SegmentTiming(line_id=1, start_ms=300, end_ms=2800),           │
│     SegmentTiming(line_id=2, start_ms=3400, end_ms=5200)           │
│   ]                                                                  │
│ )                                                                    │
└─────────────────────────────────────────────────────────────────────┘
    │
    │ Align timestamps
    ▼
┌─────────────────────────────────────────────────────────────────────┐
│ AlignmentResult(                                                     │
│   segments=[                                                         │
│     AlignedSegment(line_id=1, aligned_start_ms=320, drift_ms=20),  │
│     AlignedSegment(line_id=2, aligned_start_ms=3380, drift_ms=-20) │
│   ]                                                                  │
│ )                                                                    │
└─────────────────────────────────────────────────────────────────────┘
    │
    │ Generate outputs
    ▼
┌─────────────────────────────────────────────────────────────────────┐
│ Output Files:                                                        │
│                                                                      │
│ coffee_shop_001.mp3  ─── Final audio (normalized, compressed)       │
│ coffee_shop_001.srt  ─── Subtitles with aligned timestamps          │
│ coffee_shop_001.json ─── Timeline with metadata and segments        │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Sequence Diagram

```
┌─────────┐  ┌───────────┐  ┌──────────┐  ┌─────────┐  ┌─────────┐  ┌────────┐
│  User   │  │   CLI     │  │ Pipeline │  │   TTS   │  │ Stitcher│  │ Aligner│
└────┬────┘  └─────┬─────┘  └────┬─────┘  └────┬────┘  └────┬────┘  └───┬────┘
     │             │              │             │            │           │
     │ generate    │              │             │            │           │
     │ script.json │              │             │            │           │
     │────────────▶│              │             │            │           │
     │             │              │             │            │           │
     │             │ generate()   │             │            │           │
     │             │─────────────▶│             │            │           │
     │             │              │             │            │           │
     │             │              │ validate()  │            │           │
     │             │              │────────────▶│            │           │
     │             │              │◀────────────│            │           │
     │             │              │  validated  │            │           │
     │             │              │             │            │           │
     │             │              │ synthesize_line() (for each line)    │
     │             │              │────────────▶│            │           │
     │             │              │◀────────────│            │           │
     │             │              │ audio_bytes │            │           │
     │             │              │             │            │           │
     │             │              │ stitch()    │            │           │
     │             │              │─────────────────────────▶│           │
     │             │              │◀─────────────────────────│           │
     │             │              │ combined audio + timings │           │
     │             │              │             │            │           │
     │             │              │ align()     │            │           │
     │             │              │──────────────────────────────────────▶
     │             │              │◀──────────────────────────────────────
     │             │              │ aligned timings                      │
     │             │              │             │            │           │
     │             │ LessonOutput │             │            │           │
     │             │◀─────────────│             │            │           │
     │             │              │             │            │           │
     │ Success!    │              │             │            │           │
     │◀────────────│              │             │            │           │
     │             │              │             │            │           │
```

---

## Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **TTS Engine** | Coqui XTTS v2 | Voice cloning & synthesis |
| **Alignment** | OpenAI Whisper | Forced alignment for timestamps |
| **Audio Processing** | pydub, librosa | Audio manipulation |
| **Voice Embeddings** | Resemblyzer | Speaker similarity checking |
| **Data Validation** | Pydantic v2 | Schema validation |
| **Configuration** | PyYAML | Config file parsing |
| **CLI** | Click | Command-line interface |
| **Runtime** | Python 3.10+ | Application runtime |
| **GPU Acceleration** | PyTorch + CUDA | Model inference |

---

## Quality Assurance Pipeline

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         QUALITY CHECKS                                    │
└──────────────────────────────────────────────────────────────────────────┘

                    ┌─────────────────────┐
                    │   Input Validation  │
                    │   (ScriptValidator) │
                    └──────────┬──────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
    ┌─────────────────┐ ┌─────────────┐ ┌─────────────────┐
    │ Schema Check    │ │ Voice Check │ │ Content Check   │
    │ (Pydantic)      │ │ (registry)  │ │ (characters)    │
    └────────┬────────┘ └──────┬──────┘ └────────┬────────┘
             │                 │                  │
             └────────────────┬┼──────────────────┘
                              │
                              ▼
                    ┌─────────────────────┐
                    │   TTS Synthesis     │
                    │   (with retry)      │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │  Voice Consistency  │
                    │  (embedding check)  │
                    │  threshold: 0.85    │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │  Forced Alignment   │
                    │  (Whisper ASR)      │
                    │  drift < 200ms      │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │  Quality Score      │
                    │  (0.0 - 1.0)        │
                    └─────────────────────┘
```

---

## Error Handling & Retry Strategy

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         RETRY STRATEGY                                    │
└──────────────────────────────────────────────────────────────────────────┘

    Synthesis Request
           │
           ▼
    ┌──────────────┐
    │  Attempt 1   │
    │  (XTTS v2)   │
    └──────┬───────┘
           │
           ▼
    ┌──────────────┐      Success
    │   Success?   │──────────────────────────────▶ Continue
    └──────┬───────┘
           │ Failure
           ▼
    ┌──────────────┐
    │  Attempt 2   │
    │  (XTTS v2)   │
    │  temp=0.5    │  ◀── Lower temperature
    └──────┬───────┘
           │
           ▼
    ┌──────────────┐      Success
    │   Success?   │──────────────────────────────▶ Continue
    └──────┬───────┘
           │ Failure
           ▼
    ┌──────────────┐
    │  Attempt 3   │
    │  (VITS)      │  ◀── Fallback model
    └──────┬───────┘
           │
           ▼
    ┌──────────────┐      Success
    │   Success?   │──────────────────────────────▶ Continue
    └──────┬───────┘
           │ Failure
           ▼
    ┌──────────────┐
    │ PipelineError│
    │   raised     │
    └──────────────┘
```

---

## File Output Structure

```
output/
├── lesson_001.mp3          # Final audio (192kbps MP3)
├── lesson_001.wav          # Intermediate audio (24kHz WAV)
├── lesson_001.srt          # Subtitles (SRT format)
└── lesson_001.json         # Timeline + metadata

voices/
├── male_us_1.wav           # Voice reference (6-12s sample)
└── female_us_1.wav         # Voice reference (6-12s sample)

config/
└── default.yaml            # Application configuration
```
