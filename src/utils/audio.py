"""Audio processing utilities."""

import io
from typing import Optional

from pydub import AudioSegment


def get_audio_duration(audio_bytes: bytes, format: str = "mp3") -> int:
    """
    Get audio duration in milliseconds.

    Args:
        audio_bytes: Audio data as bytes
        format: Audio format ("mp3" or "wav")

    Returns:
        Duration in milliseconds
    """
    audio = AudioSegment.from_file(io.BytesIO(audio_bytes), format=format)
    return len(audio)


def normalize_audio(
    audio: AudioSegment,
    target_dbfs: float = -16.0,
) -> AudioSegment:
    """
    Normalize audio to target dBFS level.

    Args:
        audio: Audio segment to normalize
        target_dbfs: Target dBFS level (default: -16.0 LUFS approximation)

    Returns:
        Normalized AudioSegment
    """
    change_in_dbfs = target_dbfs - audio.dBFS
    return audio.apply_gain(change_in_dbfs)


def convert_to_mp3(
    audio: AudioSegment,
    bitrate: str = "128k",
) -> bytes:
    """
    Convert audio segment to MP3 bytes.

    Args:
        audio: Audio segment to convert
        bitrate: MP3 bitrate (default: "128k")

    Returns:
        MP3 audio as bytes
    """
    buffer = io.BytesIO()
    audio.export(buffer, format="mp3", bitrate=bitrate)
    return buffer.getvalue()


def convert_to_wav(audio: AudioSegment) -> bytes:
    """
    Convert audio segment to WAV bytes.

    Args:
        audio: Audio segment to convert

    Returns:
        WAV audio as bytes
    """
    buffer = io.BytesIO()
    audio.export(buffer, format="wav")
    return buffer.getvalue()


def create_silence(duration_ms: int, sample_rate: int = 24000) -> AudioSegment:
    """
    Create a silent audio segment.

    Args:
        duration_ms: Duration in milliseconds
        sample_rate: Sample rate (default: 24000)

    Returns:
        Silent AudioSegment
    """
    return AudioSegment.silent(duration=duration_ms, frame_rate=sample_rate)


def load_audio_bytes(audio_bytes: bytes, format: str = "mp3") -> AudioSegment:
    """
    Load audio from bytes.

    Args:
        audio_bytes: Audio data as bytes
        format: Audio format ("mp3" or "wav")

    Returns:
        AudioSegment
    """
    return AudioSegment.from_file(io.BytesIO(audio_bytes), format=format)


def detect_format(audio_bytes: bytes) -> str:
    """
    Detect audio format from bytes.

    Args:
        audio_bytes: Audio data as bytes

    Returns:
        Format string ("mp3" or "wav")
    """
    # Check for WAV magic bytes (RIFF)
    if audio_bytes[:4] == b"RIFF":
        return "wav"
    # Check for MP3 magic bytes (ID3 or sync word)
    if audio_bytes[:3] == b"ID3" or audio_bytes[:2] == b"\xff\xfb":
        return "mp3"
    # Default to mp3
    return "mp3"
