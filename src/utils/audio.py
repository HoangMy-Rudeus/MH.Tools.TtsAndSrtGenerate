"""Audio processing utilities."""

import io
import logging
from pathlib import Path

from pydub import AudioSegment

logger = logging.getLogger(__name__)


def wav_bytes_to_segment(wav_bytes: bytes) -> AudioSegment:
    """Convert WAV bytes to pydub AudioSegment."""
    return AudioSegment.from_wav(io.BytesIO(wav_bytes))


def segment_to_wav_bytes(segment: AudioSegment) -> bytes:
    """Convert pydub AudioSegment to WAV bytes."""
    buffer = io.BytesIO()
    segment.export(buffer, format="wav")
    return buffer.getvalue()


def normalize_audio(segment: AudioSegment, target_dbfs: float = -16.0) -> AudioSegment:
    """
    Normalize audio to target dBFS level.

    Args:
        segment: Audio segment to normalize
        target_dbfs: Target loudness in dBFS (default -16)

    Returns:
        Normalized audio segment
    """
    change_in_dbfs = target_dbfs - segment.dBFS
    return segment.apply_gain(change_in_dbfs)


def add_silence(duration_ms: int, sample_rate: int = 24000) -> AudioSegment:
    """
    Create silent audio segment.

    Args:
        duration_ms: Duration in milliseconds
        sample_rate: Sample rate (default 24000)

    Returns:
        Silent audio segment
    """
    return AudioSegment.silent(duration=duration_ms, frame_rate=sample_rate)


def trim_silence(
    segment: AudioSegment,
    silence_thresh: float = -50.0,
    min_silence_len: int = 100,
    keep_silence: int = 50
) -> AudioSegment:
    """
    Trim silence from start and end of audio.

    Args:
        segment: Audio segment to trim
        silence_thresh: Silence threshold in dBFS
        min_silence_len: Minimum silence length to detect (ms)
        keep_silence: Amount of silence to keep at edges (ms)

    Returns:
        Trimmed audio segment
    """
    from pydub.silence import detect_leading_silence

    # Trim leading silence
    start_trim = detect_leading_silence(segment, silence_threshold=silence_thresh)
    start_trim = max(0, start_trim - keep_silence)

    # Trim trailing silence
    end_trim = detect_leading_silence(segment.reverse(), silence_threshold=silence_thresh)
    end_trim = max(0, end_trim - keep_silence)

    duration = len(segment)
    return segment[start_trim:duration - end_trim]


def export_audio(
    segment: AudioSegment,
    output_path: str | Path,
    format: str = "mp3",
    bitrate: str = "192k"
) -> Path:
    """
    Export audio segment to file.

    Args:
        segment: Audio segment to export
        output_path: Output file path
        format: Output format (mp3, wav)
        bitrate: Bitrate for lossy formats

    Returns:
        Path to exported file
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if format == "mp3":
        segment.export(output_path, format="mp3", bitrate=bitrate)
    else:
        segment.export(output_path, format=format)

    logger.info(f"Exported audio to {output_path}")
    return output_path


def get_audio_duration_ms(segment: AudioSegment) -> int:
    """Get duration of audio segment in milliseconds."""
    return len(segment)
