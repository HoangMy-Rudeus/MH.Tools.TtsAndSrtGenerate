"""Tests for script validation."""

import pytest
from src.models.script import Script, ScriptLine
from src.services.validator import ScriptValidator, ValidationError


def test_valid_script():
    """Test validation of a valid script."""
    script = Script(
        lesson_id="test_001",
        title="Test Script",
        lines=[
            ScriptLine(id=1, speaker="female_us_1", text="Hello world!"),
            ScriptLine(id=2, speaker="male_us_1", text="Hi there!"),
        ],
    )

    validator = ScriptValidator()
    errors = validator.validate(script)

    assert len(errors) == 0


def test_empty_lesson_id():
    """Test validation fails for empty lesson_id."""
    script = Script(
        lesson_id="",
        title="Test Script",
        lines=[
            ScriptLine(id=1, speaker="female_us_1", text="Hello!"),
        ],
    )

    validator = ScriptValidator()
    errors = validator.validate(script)

    assert len(errors) > 0
    assert any("lesson_id" in e for e in errors)


def test_empty_lines():
    """Test validation fails for empty lines."""
    script = Script(
        lesson_id="test_001",
        title="Test Script",
        lines=[],
    )

    validator = ScriptValidator()
    errors = validator.validate(script)

    assert len(errors) > 0
    assert any("at least one line" in e for e in errors)


def test_duplicate_line_ids():
    """Test validation fails for duplicate line IDs."""
    script = Script(
        lesson_id="test_001",
        title="Test Script",
        lines=[
            ScriptLine(id=1, speaker="female_us_1", text="Hello!"),
            ScriptLine(id=1, speaker="male_us_1", text="Hi!"),  # Duplicate ID
        ],
    )

    validator = ScriptValidator()
    errors = validator.validate(script)

    assert len(errors) > 0
    assert any("Duplicate" in e for e in errors)


def test_invalid_emotion():
    """Test validation fails for invalid emotion."""
    script = Script(
        lesson_id="test_001",
        title="Test Script",
        lines=[
            ScriptLine(id=1, speaker="female_us_1", text="Hello!", emotion="angry"),
        ],
    )

    validator = ScriptValidator()
    errors = validator.validate(script)

    assert len(errors) > 0
    assert any("emotion" in e.lower() for e in errors)


def test_invalid_speech_rate():
    """Test validation fails for invalid speech rate."""
    script = Script(
        lesson_id="test_001",
        title="Test Script",
        lines=[
            ScriptLine(id=1, speaker="female_us_1", text="Hello!", speech_rate=3.0),
        ],
    )

    validator = ScriptValidator()
    errors = validator.validate(script)

    assert len(errors) > 0
    assert any("speech_rate" in e for e in errors)


def test_validate_or_raise():
    """Test validate_or_raise raises for invalid script."""
    script = Script(
        lesson_id="",
        title="",
        lines=[],
    )

    validator = ScriptValidator()

    with pytest.raises(ValidationError):
        validator.validate_or_raise(script)
