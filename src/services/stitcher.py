"""Audio stitching service."""

import io
from dataclasses import dataclass
from typing import Optional

from pydub import AudioSegment

from ..models.script import Segment
from ..utils.audio import (
    create_silence,
    load_audio_bytes,
    normalize_audio,
    detect_format,
)


@dataclass
class AudioSegmentInfo:
    """Information about a synthesized audio segment."""

    line_id: int
    speaker: str
    text: str
    audio: AudioSegment
    duration_ms: int


@dataclass
class StitchResult:
    """Result of stitching audio segments."""

    audio: AudioSegment
    segments: list[Segment]
    total_duration_ms: int


class AudioStitcher:
    """Stitches audio segments together with pauses."""

    def __init__(
        self,
        initial_silence_ms: int = 300,
        default_pause_ms: int = 400,
        normalize_dbfs: Optional[float] = -16.0,
        sample_rate: int = 24000,
    ):
        """
        Initialize the audio stitcher.

        Args:
            initial_silence_ms: Silence to add at the beginning
            default_pause_ms: Default pause between segments
            normalize_dbfs: Target dBFS for normalization (None to disable)
            sample_rate: Sample rate for silence generation
        """
        self.initial_silence_ms = initial_silence_ms
        self.default_pause_ms = default_pause_ms
        self.normalize_dbfs = normalize_dbfs
        self.sample_rate = sample_rate

    def stitch(
        self,
        audio_segments: list[AudioSegmentInfo],
        pauses: Optional[list[int]] = None,
    ) -> StitchResult:
        """
        Stitch audio segments together.

        Args:
            audio_segments: List of audio segment info objects
            pauses: Optional list of pause durations after each segment

        Returns:
            StitchResult with combined audio and timing info
        """
        if not audio_segments:
            return StitchResult(
                audio=AudioSegment.empty(),
                segments=[],
                total_duration_ms=0,
            )

        # Start with initial silence
        combined = create_silence(self.initial_silence_ms, self.sample_rate)
        current_position_ms = self.initial_silence_ms

        segments = []

        for i, segment_info in enumerate(audio_segments):
            # Get pause duration for this segment
            pause_ms = self.default_pause_ms
            if pauses and i < len(pauses):
                pause_ms = pauses[i]

            # Record segment timing
            start_ms = current_position_ms
            end_ms = start_ms + segment_info.duration_ms

            segments.append(Segment(
                id=segment_info.line_id,
                speaker=segment_info.speaker,
                text=segment_info.text,
                start_ms=start_ms,
                end_ms=end_ms,
                audio_duration_ms=segment_info.duration_ms,
            ))

            # Add audio segment
            combined += segment_info.audio

            # Update position
            current_position_ms = end_ms

            # Add pause after segment (except for the last one)
            if i < len(audio_segments) - 1:
                pause = create_silence(pause_ms, self.sample_rate)
                combined += pause
                current_position_ms += pause_ms

        # Normalize if enabled
        if self.normalize_dbfs is not None:
            combined = normalize_audio(combined, self.normalize_dbfs)

        return StitchResult(
            audio=combined,
            segments=segments,
            total_duration_ms=len(combined),
        )

    def stitch_from_bytes(
        self,
        audio_data: list[tuple[int, str, str, bytes, int]],
    ) -> StitchResult:
        """
        Stitch audio from raw bytes.

        Args:
            audio_data: List of tuples (line_id, speaker, text, audio_bytes, pause_after_ms)

        Returns:
            StitchResult with combined audio and timing info
        """
        audio_segments = []
        pauses = []

        for line_id, speaker, text, audio_bytes, pause_after_ms in audio_data:
            # Detect format and load audio
            fmt = detect_format(audio_bytes)
            audio = load_audio_bytes(audio_bytes, fmt)

            audio_segments.append(AudioSegmentInfo(
                line_id=line_id,
                speaker=speaker,
                text=text,
                audio=audio,
                duration_ms=len(audio),
            ))
            pauses.append(pause_after_ms)

        return self.stitch(audio_segments, pauses)

    def export_mp3(self, audio: AudioSegment, path: str, bitrate: str = "128k") -> None:
        """
        Export audio to MP3 file.

        Args:
            audio: Audio segment to export
            path: Output file path
            bitrate: MP3 bitrate
        """
        audio.export(path, format="mp3", bitrate=bitrate)

    def export_wav(self, audio: AudioSegment, path: str) -> None:
        """
        Export audio to WAV file.

        Args:
            audio: Audio segment to export
            path: Output file path
        """
        audio.export(path, format="wav")

    def export_bytes(
        self,
        audio: AudioSegment,
        format: str = "mp3",
        bitrate: str = "128k",
    ) -> bytes:
        """
        Export audio to bytes.

        Args:
            audio: Audio segment to export
            format: Output format ("mp3" or "wav")
            bitrate: MP3 bitrate (only for MP3)

        Returns:
            Audio bytes
        """
        buffer = io.BytesIO()
        if format == "mp3":
            audio.export(buffer, format="mp3", bitrate=bitrate)
        else:
            audio.export(buffer, format="wav")
        return buffer.getvalue()
