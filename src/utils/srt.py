"""SRT subtitle generation utilities."""

from pathlib import Path

from src.models.script import Segment


def format_timestamp(ms: int) -> str:
    """
    Format milliseconds as SRT timestamp.

    Format: HH:MM:SS,mmm

    Args:
        ms: Time in milliseconds

    Returns:
        Formatted timestamp string
    """
    hours = ms // 3600000
    minutes = (ms % 3600000) // 60000
    seconds = (ms % 60000) // 1000
    milliseconds = ms % 1000

    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"


def generate_srt(segments: list[Segment]) -> str:
    """
    Generate SRT content from segments.

    Args:
        segments: List of timed segments

    Returns:
        SRT formatted string
    """
    lines = []

    for idx, segment in enumerate(segments, start=1):
        start = format_timestamp(segment.start_ms)
        end = format_timestamp(segment.end_ms)

        lines.append(str(idx))
        lines.append(f"{start} --> {end}")
        lines.append(segment.text)
        lines.append("")  # Blank line between entries

    return "\n".join(lines)


def save_srt(segments: list[Segment], output_path: str | Path) -> Path:
    """
    Save segments as SRT file.

    Args:
        segments: List of timed segments
        output_path: Output file path

    Returns:
        Path to saved file
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    srt_content = generate_srt(segments)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(srt_content)

    return output_path


def parse_srt(content: str) -> list[dict]:
    """
    Parse SRT content into segment dictionaries.

    Args:
        content: SRT file content

    Returns:
        List of segment dicts with id, start_ms, end_ms, text
    """
    segments = []
    blocks = content.strip().split("\n\n")

    for block in blocks:
        lines = block.strip().split("\n")
        if len(lines) < 3:
            continue

        idx = int(lines[0])
        timing = lines[1]
        text = "\n".join(lines[2:])

        # Parse timing
        start_str, end_str = timing.split(" --> ")
        start_ms = _parse_timestamp(start_str)
        end_ms = _parse_timestamp(end_str)

        segments.append({
            "id": idx,
            "start_ms": start_ms,
            "end_ms": end_ms,
            "text": text,
        })

    return segments


def _parse_timestamp(timestamp: str) -> int:
    """Parse SRT timestamp to milliseconds."""
    # Format: HH:MM:SS,mmm
    time_part, ms_part = timestamp.split(",")
    h, m, s = time_part.split(":")

    return (
        int(h) * 3600000 +
        int(m) * 60000 +
        int(s) * 1000 +
        int(ms_part)
    )
