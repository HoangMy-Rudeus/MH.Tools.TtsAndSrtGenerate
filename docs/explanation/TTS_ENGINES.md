# TTS Engines

Understanding the text-to-speech engines available in the system.

## Overview

The TTS & SRT Generator supports multiple TTS engines through a pluggable architecture. Each engine has different characteristics suited for different use cases.

## Engine Comparison

| Feature | Edge TTS | Kokoro-ONNX |
|---------|----------|-------------|
| **Type** | Cloud | Local |
| **Quality** | Good | Excellent |
| **Speed** | ~0.3-0.5s/line | ~0.5-2s/line |
| **Offline** | No | Yes |
| **Cost** | Free | Free |
| **Model Size** | N/A | ~300MB |
| **Voices** | 400+ (all languages) | 14+ (English) |
| **Privacy** | Text sent to Microsoft | Fully local |

## Edge TTS (Cloud)

### How It Works

Edge TTS uses Microsoft's neural text-to-speech service, the same technology powering Microsoft Edge's Read Aloud feature.

```
Your Text ──▶ Microsoft Servers ──▶ Neural TTS ──▶ Audio (MP3)
```

### Advantages

1. **No setup required**: Works immediately
2. **Wide voice selection**: 400+ voices in 100+ languages
3. **Fast synthesis**: Optimized cloud infrastructure
4. **Free**: No API keys or payment required
5. **High quality**: Neural voices sound natural

### Limitations

1. **Requires internet**: No offline capability
2. **Privacy**: Text is sent to Microsoft servers
3. **Rate limits**: May be throttled with heavy use
4. **Dependency**: Relies on external service availability

### Technical Details

- **Audio format**: MP3 (compressed)
- **Sample rate**: 24kHz
- **Bit rate**: ~128kbps
- **API**: WebSocket-based streaming

### Best For

- Quick previews during development
- Projects without strict privacy requirements
- Multi-language support
- Rapid prototyping

## Kokoro-ONNX (Local)

### How It Works

Kokoro-ONNX runs a neural TTS model locally using the ONNX runtime.

```
Your Text ──▶ Local ONNX Model ──▶ Neural Inference ──▶ Audio (WAV)
```

### Advantages

1. **Offline**: Works without internet
2. **Privacy**: Text never leaves your machine
3. **Consistent quality**: No network variability
4. **No rate limits**: Process as much as needed
5. **Excellent quality**: High-fidelity audio

### Limitations

1. **Setup required**: Download model files (~300MB)
2. **Limited voices**: ~14 English voices
3. **Processing time**: Slower than cloud (especially on CPU)
4. **Resource usage**: Uses CPU/GPU for inference

### Technical Details

- **Audio format**: WAV (uncompressed)
- **Sample rate**: 24kHz
- **Model**: 82M parameter neural network
- **Runtime**: ONNX Runtime (CPU or GPU)

### Model Files

| File | Size | Purpose |
|------|------|---------|
| kokoro-v1.0.onnx | ~300MB | Neural network weights |
| voices-v1.0.bin | ~40MB | Voice embeddings |

### Best For

- Production-quality audio
- Privacy-sensitive applications
- Offline environments
- Consistent, repeatable output

## Voice Quality

### Edge TTS Quality Factors

1. **Voice selection**: Newer Neural voices are higher quality
2. **Text complexity**: Handles complex sentences well
3. **Pronunciation**: Generally accurate, some edge cases
4. **Prosody**: Natural rhythm and intonation

### Kokoro-ONNX Quality Factors

1. **Voice style**: Each voice has distinct characteristics
2. **Text length**: Works well with short to medium sentences
3. **Punctuation**: Respects pauses and emphasis
4. **Speed control**: Maintains quality at different speeds

## Choosing an Engine

### Decision Flowchart

```
Is offline operation required?
├── Yes ──▶ Use Kokoro-ONNX
└── No
    │
    Is privacy critical?
    ├── Yes ──▶ Use Kokoro-ONNX
    └── No
        │
        Need non-English languages?
        ├── Yes ──▶ Use Edge TTS
        └── No
            │
            Is this for production?
            ├── Yes ──▶ Consider Kokoro-ONNX for quality
            └── No ──▶ Use Edge TTS for speed
```

### Recommendation Summary

| Scenario | Recommended Engine |
|----------|-------------------|
| Development/Testing | Edge TTS |
| Production | Kokoro-ONNX |
| Multi-language | Edge TTS |
| Offline/Air-gapped | Kokoro-ONNX |
| Privacy-sensitive | Kokoro-ONNX |
| Quick iteration | Edge TTS |

## Engine Architecture

### Abstract Interface

Both engines implement the same interface:

```python
class TTSEngine(ABC):
    @abstractmethod
    def initialize(self) -> None:
        """Load model or connect to service."""

    @abstractmethod
    def synthesize(
        self,
        text: str,
        voice: str,
        emotion: str = "neutral",
        speed: float = 1.0,
    ) -> SynthesisResult:
        """Convert text to audio."""

    @abstractmethod
    def get_available_voices(self) -> list[str]:
        """List available voices."""

    @abstractmethod
    def cleanup(self) -> None:
        """Release resources."""
```

### Voice Mapping

Both engines support abstract speaker IDs:

```
Script: "speaker": "female_us_1"
           │
           ▼
    Voice Mapping (Config)
           │
    ┌──────┴──────┐
    ▼             ▼
Edge TTS      Kokoro
    │             │
    ▼             ▼
"en-US-       "af_heart"
AriaNeural"
```

## Performance Optimization

### Edge TTS

1. **Connection reuse**: Reuse pipeline for multiple generations
2. **Error handling**: Implement retries for network issues
3. **Caching**: Cache common phrases locally

### Kokoro-ONNX

1. **Model caching**: Keep model loaded between generations
2. **GPU acceleration**: Use CUDA/DirectML if available
3. **Batch processing**: Process multiple scripts sequentially
4. **Quantization**: Use quantized models for faster inference

## Extending with New Engines

To add a new TTS engine:

1. **Implement the interface**:

```python
class MyCustomEngine(TTSEngine):
    def initialize(self) -> None:
        # Load your model/connect to service
        pass

    def synthesize(self, text, voice, emotion, speed) -> SynthesisResult:
        # Generate audio
        audio_bytes = my_tts_function(text, voice)
        return SynthesisResult(
            line_id=0,
            success=True,
            audio_bytes=audio_bytes,
            duration_ms=calculate_duration(audio_bytes),
            sample_rate=24000
        )

    def get_available_voices(self) -> list[str]:
        return ["voice1", "voice2"]

    def cleanup(self) -> None:
        # Release resources
        pass
```

2. **Register in factory**:

```python
# In engines/factory.py
def create_engine(engine_type: str, config: Config) -> TTSEngine:
    if engine_type == "my_custom":
        return MyCustomEngine()
    # ...existing engines...
```

3. **Add configuration**:

```yaml
# In config
engine: "my_custom"

my_custom:
  api_key: "..."
  voices:
    female_us_1: "my_voice_1"
```

## Common Issues

### Edge TTS

| Issue | Cause | Solution |
|-------|-------|----------|
| Connection timeout | Network issues | Check internet, retry |
| Rate limited | Too many requests | Add delays between requests |
| Voice not found | Invalid voice name | Use `voices` command to list |

### Kokoro-ONNX

| Issue | Cause | Solution |
|-------|-------|----------|
| Model not found | Missing files | Download model files |
| Out of memory | Large model | Use smaller batch sizes |
| Slow inference | CPU only | Enable GPU acceleration |
