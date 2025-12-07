"""SRT subtitle generation utilities."""

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
