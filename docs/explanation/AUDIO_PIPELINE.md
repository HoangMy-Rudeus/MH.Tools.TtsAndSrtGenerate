# Audio Pipeline

Understanding how audio is processed, assembled, and exported.

## Overview

The audio pipeline transforms synthesized speech segments into a cohesive audio file with proper timing for subtitles.

```
Per-Line Audio ──▶ Assembly ──▶ Normalization ──▶ Export
```

## Pipeline Stages

### Stage 1: Per-Line Synthesis

Each script line is independently synthesized:

```
Line 1 ──▶ TTS Engine ──▶ audio_bytes_1 (MP3/WAV)
Line 2 ──▶ TTS Engine ──▶ audio_bytes_2 (MP3/WAV)
Line 3 ──▶ TTS Engine ──▶ audio_bytes_3 (MP3/WAV)
...
```

**Output per line:**
- `audio_bytes`: Raw audio data
- `duration_ms`: Actual audio duration
- `sample_rate`: Audio sample rate

### Stage 2: Audio Assembly

Audio segments are combined with timing:

```
┌─────────────────────────────────────────────────────────────┐
│                     Combined Audio                          │
├───────┬─────────────┬───────┬─────────────┬───────┬────────┤
│Silence│   Line 1    │ Pause │   Line 2    │ Pause │Line 3  │
│ 300ms │   2500ms    │ 400ms │   1800ms    │ 600ms │ 2200ms │
└───────┴─────────────┴───────┴─────────────┴───────┴────────┘
  │                     │                     │
  0ms                 2800ms                5000ms
```

**Assembly process:**
1. Add initial silence (configurable, default 300ms)
2. Append first audio segment
3. Record start/end timestamps
4. Add pause after segment
5. Repeat for all segments

### Stage 3: Normalization

Audio levels are normalized for consistent volume:

```
Before: Variable levels
┌──────┬────────────┬───────────┐
│ -20  │    -8      │   -15     │ dBFS
└──────┴────────────┴───────────┘

After: Consistent level (-16 dBFS)
┌──────┬────────────┬───────────┐
│ -16  │   -16      │   -16     │ dBFS
└──────┴────────────┴───────────┘
```

**Normalization algorithm:**
```python
change_in_db = target_dbfs - audio.dBFS
normalized = audio.apply_gain(change_in_db)
```

### Stage 4: Export

Final audio is exported in the chosen format:

```
Combined Audio
      │
      ├──▶ MP3 (compressed, smaller)
      │    └── Bitrate: 128kbps
      │
      └──▶ WAV (uncompressed, larger)
           └── 16-bit PCM
```

## Timing Calculations

### Segment Timing

```python
# For each segment:
start_ms = previous_end_ms + pause_ms
end_ms = start_ms + audio_duration_ms

# Example:
# Initial silence: 300ms
# Line 1: 2500ms duration, 400ms pause after
# Line 2: 1800ms duration, 600ms pause after

Segment 1:
  start_ms = 300 (after initial silence)
  end_ms = 300 + 2500 = 2800
  pause_after = 400

Segment 2:
  start_ms = 2800 + 400 = 3200
  end_ms = 3200 + 1800 = 5000
  pause_after = 600
```

### SRT Timestamp Generation

```python
def ms_to_srt_time(ms: int) -> str:
    """Convert milliseconds to SRT format: HH:MM:SS,mmm"""
    hours = ms // 3600000
    minutes = (ms % 3600000) // 60000
    seconds = (ms % 60000) // 1000
    millis = ms % 1000
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"

# 5000ms → "00:00:05,000"
# 65500ms → "00:01:05,500"
```

## Audio Processing

### Format Detection

The pipeline handles both MP3 and WAV formats:

```python
def detect_format(audio_bytes: bytes) -> str:
    # WAV starts with "RIFF"
    if audio_bytes[:4] == b"RIFF":
        return "wav"
    # MP3 starts with ID3 tag or sync word
    if audio_bytes[:3] == b"ID3" or audio_bytes[:2] == b"\xff\xfb":
        return "mp3"
    return "mp3"  # Default
```

### Audio Loading

```python
from pydub import AudioSegment
import io

def load_audio_bytes(audio_bytes: bytes, format: str) -> AudioSegment:
    return AudioSegment.from_file(io.BytesIO(audio_bytes), format=format)
```

### Silence Generation

```python
from pydub import AudioSegment

def create_silence(duration_ms: int, sample_rate: int = 24000) -> AudioSegment:
    return AudioSegment.silent(duration=duration_ms, frame_rate=sample_rate)
```

## Configuration Options

### Timing Settings

```yaml
synthesis:
  initial_silence_ms: 300   # Silence at start
  default_pause_ms: 400     # Default pause between lines
```

### Audio Quality

```yaml
audio:
  sample_rate: 24000        # Hz
  normalize_to: -16         # dBFS (null to disable)
  output_format: "mp3"      # "mp3" or "wav"
```

## Pause Strategies

### Fixed Pauses

All pauses are the same duration:

```json
{
  "settings": {
    "default_pause_ms": 400
  }
}
```

### Variable Pauses

Different pauses per line:

```json
{
  "lines": [
    {"id": 1, "text": "Question?", "pause_after_ms": 1000},
    {"id": 2, "text": "Statement.", "pause_after_ms": 400},
    {"id": 3, "text": "Excited!", "pause_after_ms": 600}
  ]
}
```

### Pause Guidelines

| Content Type | Recommended Pause |
|--------------|-------------------|
| Question | 800-1200ms |
| Statement | 400-600ms |
| Topic change | 1000-1500ms |
| Exclamation | 500-800ms |
| List item | 300-400ms |

## Output Formats

### MP3 (Default)

- **Compression**: Lossy
- **File size**: ~1MB per minute
- **Quality**: Good for speech
- **Compatibility**: Universal

```python
audio.export(path, format="mp3", bitrate="128k")
```

### WAV

- **Compression**: None
- **File size**: ~2.8MB per minute
- **Quality**: Lossless
- **Use case**: Editing, archival

```python
audio.export(path, format="wav")
```

## Data Structures

### AudioSegmentInfo

```python
@dataclass
class AudioSegmentInfo:
    line_id: int        # Script line ID
    speaker: str        # Speaker identifier
    text: str           # Spoken text
    audio: AudioSegment # pydub audio
    duration_ms: int    # Duration in ms
```

### StitchResult

```python
@dataclass
class StitchResult:
    audio: AudioSegment     # Combined audio
    segments: list[Segment] # Timing information
    total_duration_ms: int  # Total duration
```

### Segment (Timing)

```python
@dataclass
class Segment:
    id: int                 # Line ID
    speaker: str            # Speaker
    text: str               # Text content
    start_ms: int           # Start time
    end_ms: int             # End time
    audio_duration_ms: int  # Audio duration
```

## Error Handling

### Missing Audio

If synthesis fails for a line:
1. Retry (configurable attempts)
2. If all retries fail, raise error
3. Pipeline stops (partial output not saved)

### Format Mismatch

Mixed formats (MP3 from Edge, WAV from Kokoro) are handled:
```python
# Detect format automatically
fmt = detect_format(audio_bytes)
audio = load_audio_bytes(audio_bytes, fmt)
# pydub normalizes internally
```

## Performance Considerations

### Memory Usage

- Each audio segment loaded into memory
- For long scripts, consider chunked processing
- Final audio held in memory during export

### Processing Time

| Operation | Typical Time |
|-----------|--------------|
| Load segment | ~10-50ms |
| Append | ~5-10ms |
| Normalize | ~50-100ms |
| Export MP3 | ~100-500ms |
| Export WAV | ~50-200ms |

### Optimization Tips

1. **Reuse AudioSegment objects**: Don't reload same audio
2. **Stream export**: For very long audio, consider chunked export
3. **Parallel loading**: Load segments in parallel if needed

## Dependencies

### pydub

Core audio processing library:
```python
from pydub import AudioSegment

# Concatenation
combined = audio1 + audio2

# Volume adjustment
louder = audio.apply_gain(6)  # +6 dB

# Export
audio.export("output.mp3", format="mp3")
```

### FFmpeg

Required by pydub for format conversion:
- Decoding MP3
- Encoding MP3
- Format conversion

## Extending the Pipeline

### Custom Normalization

```python
def custom_normalize(audio: AudioSegment) -> AudioSegment:
    # Example: Peak normalization
    peak = audio.max_dBFS
    return audio.apply_gain(-peak)
```

### Adding Effects

```python
def add_fade(audio: AudioSegment) -> AudioSegment:
    return audio.fade_in(100).fade_out(100)
```

### Custom Export Format

```python
def export_ogg(audio: AudioSegment, path: str):
    audio.export(path, format="ogg", codec="libvorbis")
```
