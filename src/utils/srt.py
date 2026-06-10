"""SRT subtitle generation utilities."""

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..models.script import Segment


def ms_to_srt_time(ms: int) -> str:
    """
    Convert milliseconds to SRT timestamp format.

    Args:
        ms: Time in milliseconds

    Returns:
        SRT timestamp string (HH:MM:SS,mmm)
    """
    hours = ms // 3600000
    minutes = (ms % 3600000) // 60000
    seconds = (ms % 60000) // 1000
    millis = ms % 1000
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"


def generate_srt(segments: list["Segment"]) -> str:
    """
    Generate SRT subtitle content from segments.

    Args:
        segments: List of Segment objects with timing information

    Returns:
        SRT file content as string
    """
    srt_lines = []

    for i, segment in enumerate(segments, start=1):
        start_time = ms_to_srt_time(segment.start_ms)
        end_time = ms_to_srt_time(segment.end_ms)

        srt_lines.append(str(i))
        srt_lines.append(f"{start_time} --> {end_time}")
        srt_lines.append(segment.text)
        srt_lines.append("")  # Empty line between entries

    return "\n".join(srt_lines)


def generate_srt_with_speakers(
    segments: list["Segment"],
    include_speaker: bool = True,
) -> str:
    """
    Generate SRT subtitle content with optional speaker labels.

    Args:
        segments: List of Segment objects with timing information
        include_speaker: Whether to include speaker labels in subtitles

    Returns:
        SRT file content as string
    """
    srt_lines = []

    for i, segment in enumerate(segments, start=1):
        start_time = ms_to_srt_time(segment.start_ms)
        end_time = ms_to_srt_time(segment.end_ms)

        text = segment.text
        if include_speaker:
            # Format speaker name nicely
            speaker = segment.speaker.replace("_", " ").title()
            text = f"[{speaker}] {text}"

        srt_lines.append(str(i))
        srt_lines.append(f"{start_time} --> {end_time}")
        srt_lines.append(text)
        srt_lines.append("")  # Empty line between entries

    return "\n".join(srt_lines)


def save_srt(content: str, path: str) -> None:
    """
    Save SRT content to a file.

    Args:
        content: SRT content string
        path: Output file path
    """
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def generate_subtitle_json(segments: list["Segment"]) -> str:
    """
    Generate subtitle JSON content from segments.

    Produces a flat array of {startTime, endTime, text} objects where the
    times are expressed in seconds (e.g. 0.0, 5.5).

    Args:
        segments: List of Segment objects with timing information

    Returns:
        JSON string with subtitle data
    """
    data = [
        {
            "startTime": round(segment.start_ms / 1000.0, 3),
            "endTime": round(segment.end_ms / 1000.0, 3),
            "text": segment.text,
        }
        for segment in segments
    ]
    return json.dumps(data, ensure_ascii=False, indent=2)


def save_subtitle_json(content: str, path: str) -> None:
    """
    Save subtitle JSON content to a file.

    Args:
        content: JSON content string
        path: Output file path
    """
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
