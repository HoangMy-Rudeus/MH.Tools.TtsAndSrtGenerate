"""Serialize and save conversation scripts to JSON."""

import json
from pathlib import Path

from ..models.script import Script


def script_to_dict(script: Script) -> dict:
    """Inverse of ScriptValidator.parse_script."""
    data = {
        "lesson_id": script.lesson_id,
        "title": script.title,
        "language": script.language,
        "level": script.level,
        "lines": [],
    }
    for line in script.lines:
        line_dict = {"id": line.id, "speaker": line.speaker, "text": line.text}
        if line.voice:
            line_dict["voice"] = line.voice
        line_dict["emotion"] = line.emotion
        line_dict["pause_after_ms"] = line.pause_after_ms
        line_dict["speech_rate"] = line.speech_rate
        data["lines"].append(line_dict)
    if script.settings:
        data["settings"] = {
            "speech_rate": script.settings.speech_rate,
            "initial_silence_ms": script.settings.initial_silence_ms,
            "default_pause_ms": script.settings.default_pause_ms,
        }
    return data


def save_script(script: Script, path: str | Path) -> None:
    """Write a Script to a pretty JSON file (creating parent dirs)."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(script_to_dict(script), f, indent=2, ensure_ascii=False)
