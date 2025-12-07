"""Script validation service."""

import json
from pathlib import Path
from typing import Optional

from ..models.script import Script, ScriptLine, ScriptSettings
from ..engines.base import TTSEngine


class ValidationError(Exception):
    """Raised when script validation fails."""

    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__(f"Validation failed: {'; '.join(errors)}")


class ScriptValidator:
    """Validates conversation scripts."""

    # Valid emotion values
    VALID_EMOTIONS = {"neutral", "friendly", "cheerful", "serious", "excited"}

    def __init__(self, engine: Optional[TTSEngine] = None):
        """
        Initialize the validator.

        Args:
            engine: Optional TTS engine for voice validation
        """
        self.engine = engine

    def validate(self, script: Script) -> list[str]:
        """
        Validate a script and return list of errors.

        Args:
            script: Script to validate

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        # Validate lesson_id
        if not script.lesson_id:
            errors.append("lesson_id is required")
        elif not script.lesson_id.replace("_", "").replace("-", "").isalnum():
            errors.append("lesson_id must contain only alphanumeric characters, underscores, and hyphens")

        # Validate title
        if not script.title:
            errors.append("title is required")

        # Validate lines
        if not script.lines:
            errors.append("Script must have at least one line")
        else:
            seen_ids = set()
            available_voices = self.engine.get_available_voices() if self.engine else None

            for i, line in enumerate(script.lines):
                line_prefix = f"Line {i + 1} (id={line.id})"

                # Check unique ID
                if line.id in seen_ids:
                    errors.append(f"{line_prefix}: Duplicate line ID")
                seen_ids.add(line.id)

                # Validate required fields
                if not line.speaker:
                    errors.append(f"{line_prefix}: speaker is required")
                elif available_voices and line.speaker not in available_voices:
                    # Check if it's a direct voice name (not an error if so)
                    if not self._is_direct_voice(line.speaker, line.voice):
                        errors.append(
                            f"{line_prefix}: Unknown speaker '{line.speaker}'. "
                            f"Available: {', '.join(available_voices)}"
                        )

                if not line.text:
                    errors.append(f"{line_prefix}: text is required")
                elif len(line.text) > 5000:
                    errors.append(f"{line_prefix}: text is too long (max 5000 characters)")

                # Validate emotion
                if line.emotion and line.emotion not in self.VALID_EMOTIONS:
                    errors.append(
                        f"{line_prefix}: Invalid emotion '{line.emotion}'. "
                        f"Valid: {', '.join(self.VALID_EMOTIONS)}"
                    )

                # Validate pause_after_ms
                if line.pause_after_ms < 0:
                    errors.append(f"{line_prefix}: pause_after_ms cannot be negative")
                elif line.pause_after_ms > 10000:
                    errors.append(f"{line_prefix}: pause_after_ms too long (max 10000ms)")

                # Validate speech_rate
                if line.speech_rate < 0.5 or line.speech_rate > 2.0:
                    errors.append(f"{line_prefix}: speech_rate must be between 0.5 and 2.0")

        return errors

    def _is_direct_voice(self, speaker: str, voice: Optional[str]) -> bool:
        """Check if speaker/voice is a direct voice name."""
        # Edge TTS voice pattern
        if "-" in speaker and "Neural" in speaker:
            return True
        # Kokoro voice pattern
        if speaker.startswith(("af_", "am_", "bf_", "bm_")):
            return True
        # Check voice field
        if voice:
            return True
        return False

    def validate_or_raise(self, script: Script) -> None:
        """
        Validate a script and raise if invalid.

        Args:
            script: Script to validate

        Raises:
            ValidationError: If validation fails
        """
        errors = self.validate(script)
        if errors:
            raise ValidationError(errors)

    @staticmethod
    def load_script(path: str | Path) -> Script:
        """
        Load and parse a script from a JSON file.

        Args:
            path: Path to the JSON script file

        Returns:
            Parsed Script object

        Raises:
            FileNotFoundError: If file doesn't exist
            json.JSONDecodeError: If JSON is invalid
            ValueError: If script structure is invalid
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Script file not found: {path}")

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return ScriptValidator.parse_script(data)

    @staticmethod
    def parse_script(data: dict) -> Script:
        """
        Parse a script from a dictionary.

        Args:
            data: Script data dictionary

        Returns:
            Parsed Script object

        Raises:
            ValueError: If script structure is invalid
        """
        try:
            # Parse lines
            lines = []
            for line_data in data.get("lines", []):
                line = ScriptLine(
                    id=line_data["id"],
                    speaker=line_data["speaker"],
                    text=line_data["text"],
                    voice=line_data.get("voice"),
                    emotion=line_data.get("emotion", "neutral"),
                    pause_after_ms=line_data.get("pause_after_ms", 400),
                    speech_rate=line_data.get("speech_rate", 1.0),
                )
                lines.append(line)

            # Parse settings
            settings = None
            if "settings" in data:
                settings_data = data["settings"]
                settings = ScriptSettings(
                    speech_rate=settings_data.get("speech_rate", 1.0),
                    initial_silence_ms=settings_data.get("initial_silence_ms", 300),
                    default_pause_ms=settings_data.get("default_pause_ms", 400),
                )

            # Create script
            return Script(
                lesson_id=data.get("lesson_id", ""),
                title=data.get("title", ""),
                lines=lines,
                language=data.get("language", "en"),
                level=data.get("level", "B1"),
                settings=settings,
            )

        except KeyError as e:
            raise ValueError(f"Missing required field: {e}")
        except (TypeError, ValueError) as e:
            raise ValueError(f"Invalid script data: {e}")
