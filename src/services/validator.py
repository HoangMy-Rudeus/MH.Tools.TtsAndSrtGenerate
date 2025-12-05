"""Script validation service."""

import re
from pathlib import Path
from pydantic import BaseModel, Field, ValidationError as PydanticValidationError

from src.models.script import ScriptInput, ScriptLine


class ValidationError(BaseModel):
    """Single validation error."""
    field: str
    message: str
    line_id: int | None = None


class ValidationResult(BaseModel):
    """Result of script validation."""
    success: bool
    errors: list[ValidationError] = Field(default_factory=list)
    warnings: list[ValidationError] = Field(default_factory=list)


class ScriptValidator:
    """Validates input scripts against schema and content rules."""

    # Allowed characters: letters, numbers, basic punctuation, spaces
    TEXT_PATTERN = re.compile(r"^[a-zA-Z0-9\s.,!?'\"-:;()]+$")

    def __init__(self, voice_registry: dict[str, Path] | None = None):
        """
        Initialize validator.

        Args:
            voice_registry: Dict mapping voice IDs to reference audio paths
        """
        self.voice_registry = voice_registry or {}

    def validate(self, script: dict) -> ValidationResult:
        """
        Validate script against schema and content rules.

        Checks:
        - Required fields present (via Pydantic)
        - Speaker IDs exist in voice registry
        - Text contains only allowed characters
        - Emotion values in allowed set
        - Pause values within range

        Args:
            script: Raw script dictionary

        Returns:
            ValidationResult with errors/warnings
        """
        errors: list[ValidationError] = []
        warnings: list[ValidationError] = []

        # Step 1: Pydantic schema validation
        try:
            parsed = ScriptInput(**script)
        except PydanticValidationError as e:
            for err in e.errors():
                field = ".".join(str(loc) for loc in err["loc"])
                errors.append(ValidationError(
                    field=field,
                    message=err["msg"]
                ))
            return ValidationResult(success=False, errors=errors)

        # Step 2: Content validation
        for line in parsed.lines:
            line_errors, line_warnings = self._validate_line(line)
            errors.extend(line_errors)
            warnings.extend(line_warnings)

        # Step 3: Check for duplicate IDs
        ids = [line.id for line in parsed.lines]
        if len(ids) != len(set(ids)):
            errors.append(ValidationError(
                field="lines",
                message="Duplicate line IDs found"
            ))

        return ValidationResult(
            success=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    def _validate_line(self, line: ScriptLine) -> tuple[list[ValidationError], list[ValidationError]]:
        """Validate a single script line."""
        errors: list[ValidationError] = []
        warnings: list[ValidationError] = []

        # Check voice exists in registry
        if self.voice_registry and line.speaker not in self.voice_registry:
            errors.append(ValidationError(
                field="speaker",
                message=f"Speaker '{line.speaker}' not found in voice registry",
                line_id=line.id
            ))

        # Check text characters
        if not self.TEXT_PATTERN.match(line.text):
            # Find invalid characters
            invalid = set(c for c in line.text if not re.match(r"[a-zA-Z0-9\s.,!?'\"-:;()]", c))
            errors.append(ValidationError(
                field="text",
                message=f"Text contains invalid characters: {invalid}",
                line_id=line.id
            ))

        # Warn about very long lines
        if len(line.text) > 300:
            warnings.append(ValidationError(
                field="text",
                message=f"Line is very long ({len(line.text)} chars), may affect synthesis quality",
                line_id=line.id
            ))

        # Warn about very short pauses after long text
        words = len(line.text.split())
        if words > 15 and line.pause_after_ms < 200:
            warnings.append(ValidationError(
                field="pause_after_ms",
                message="Short pause after long text may sound rushed",
                line_id=line.id
            ))

        return errors, warnings

    def validate_file(self, path: str | Path) -> ValidationResult:
        """Validate script from JSON file."""
        import json

        try:
            with open(path) as f:
                script = json.load(f)
        except json.JSONDecodeError as e:
            return ValidationResult(
                success=False,
                errors=[ValidationError(field="file", message=f"Invalid JSON: {e}")]
            )
        except FileNotFoundError:
            return ValidationResult(
                success=False,
                errors=[ValidationError(field="file", message=f"File not found: {path}")]
            )

        return self.validate(script)
