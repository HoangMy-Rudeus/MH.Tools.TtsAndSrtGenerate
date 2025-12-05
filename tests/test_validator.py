"""Tests for script validator."""

import pytest
from src.services.validator import ScriptValidator, ValidationResult


class TestScriptValidator:
    """Tests for ScriptValidator."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = ScriptValidator()

    def test_valid_script(self):
        """Test validation of a valid script."""
        script = {
            "lesson_id": "test_001",
            "title": "Test Lesson",
            "level": "B2",
            "lines": [
                {
                    "id": 1,
                    "speaker": "male_us_1",
                    "text": "Hello, how are you?",
                    "emotion": "friendly",
                    "pause_after_ms": 500,
                }
            ],
            "settings": {
                "speech_rate": 1.0,
                "initial_silence_ms": 300,
                "default_pause_ms": 400,
            },
        }

        result = self.validator.validate(script)
        assert result.success is True
        assert len(result.errors) == 0

    def test_missing_required_field(self):
        """Test validation fails for missing required field."""
        script = {
            "title": "Test Lesson",
            "lines": [],
        }

        result = self.validator.validate(script)
        assert result.success is False
        assert any("lesson_id" in e.field for e in result.errors)

    def test_empty_lines(self):
        """Test validation fails for empty lines array."""
        script = {
            "lesson_id": "test_001",
            "title": "Test Lesson",
            "lines": [],
        }

        result = self.validator.validate(script)
        assert result.success is False

    def test_invalid_characters_in_text(self):
        """Test validation fails for invalid characters."""
        script = {
            "lesson_id": "test_001",
            "title": "Test Lesson",
            "lines": [
                {
                    "id": 1,
                    "speaker": "male_us_1",
                    "text": "Hello @#$ world",
                    "emotion": "neutral",
                }
            ],
        }

        result = self.validator.validate(script)
        assert result.success is False
        assert any("invalid characters" in e.message.lower() for e in result.errors)

    def test_duplicate_line_ids(self):
        """Test validation fails for duplicate line IDs."""
        script = {
            "lesson_id": "test_001",
            "title": "Test Lesson",
            "lines": [
                {"id": 1, "speaker": "male_us_1", "text": "Hello"},
                {"id": 1, "speaker": "male_us_1", "text": "World"},
            ],
        }

        result = self.validator.validate(script)
        assert result.success is False
        assert any("duplicate" in e.message.lower() for e in result.errors)

    def test_invalid_emotion(self):
        """Test validation fails for invalid emotion."""
        script = {
            "lesson_id": "test_001",
            "title": "Test Lesson",
            "lines": [
                {
                    "id": 1,
                    "speaker": "male_us_1",
                    "text": "Hello",
                    "emotion": "angry",  # Not in allowed list
                }
            ],
        }

        result = self.validator.validate(script)
        assert result.success is False

    def test_pause_out_of_range(self):
        """Test validation fails for pause out of range."""
        script = {
            "lesson_id": "test_001",
            "title": "Test Lesson",
            "lines": [
                {
                    "id": 1,
                    "speaker": "male_us_1",
                    "text": "Hello",
                    "pause_after_ms": 10000,  # > 5000 limit
                }
            ],
        }

        result = self.validator.validate(script)
        assert result.success is False

    def test_warning_for_long_text(self):
        """Test warning is generated for very long text."""
        long_text = "Hello world. " * 50  # > 300 chars

        script = {
            "lesson_id": "test_001",
            "title": "Test Lesson",
            "lines": [
                {
                    "id": 1,
                    "speaker": "male_us_1",
                    "text": long_text,
                }
            ],
        }

        result = self.validator.validate(script)
        assert result.success is True  # Should pass but with warning
        assert len(result.warnings) > 0
        assert any("long" in w.message.lower() for w in result.warnings)

    def test_voice_registry_validation(self):
        """Test validation checks voice registry."""
        from pathlib import Path

        validator = ScriptValidator(
            voice_registry={"male_us_1": Path("voices/male_us_1.wav")}
        )

        script = {
            "lesson_id": "test_001",
            "title": "Test Lesson",
            "lines": [
                {
                    "id": 1,
                    "speaker": "unknown_voice",
                    "text": "Hello",
                }
            ],
        }

        result = validator.validate(script)
        assert result.success is False
        assert any("not found" in e.message.lower() for e in result.errors)
