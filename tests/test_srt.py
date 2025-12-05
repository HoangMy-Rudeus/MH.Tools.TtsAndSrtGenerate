"""Tests for SRT utilities."""

import pytest
from src.utils.srt import format_timestamp, generate_srt, parse_srt
from src.models.script import Segment


class TestSrtUtils:
    """Tests for SRT utility functions."""

    def test_format_timestamp_zero(self):
        """Test formatting zero milliseconds."""
        assert format_timestamp(0) == "00:00:00,000"

    def test_format_timestamp_milliseconds(self):
        """Test formatting milliseconds only."""
        assert format_timestamp(500) == "00:00:00,500"

    def test_format_timestamp_seconds(self):
        """Test formatting seconds and milliseconds."""
        assert format_timestamp(2500) == "00:00:02,500"

    def test_format_timestamp_minutes(self):
        """Test formatting minutes."""
        assert format_timestamp(65000) == "00:01:05,000"

    def test_format_timestamp_hours(self):
        """Test formatting hours."""
        assert format_timestamp(3661500) == "01:01:01,500"

    def test_generate_srt_single_segment(self):
        """Test generating SRT with single segment."""
        segments = [
            Segment(
                id=1,
                speaker="male_us_1",
                text="Hello, how are you?",
                start_ms=300,
                end_ms=2500,
                audio_duration_ms=2200,
            )
        ]

        srt = generate_srt(segments)

        assert "1\n" in srt
        assert "00:00:00,300 --> 00:00:02,500" in srt
        assert "Hello, how are you?" in srt

    def test_generate_srt_multiple_segments(self):
        """Test generating SRT with multiple segments."""
        segments = [
            Segment(
                id=1,
                speaker="male_us_1",
                text="First line.",
                start_ms=300,
                end_ms=1500,
                audio_duration_ms=1200,
            ),
            Segment(
                id=2,
                speaker="female_us_1",
                text="Second line.",
                start_ms=2000,
                end_ms=3500,
                audio_duration_ms=1500,
            ),
        ]

        srt = generate_srt(segments)

        assert "1\n" in srt
        assert "2\n" in srt
        assert "First line." in srt
        assert "Second line." in srt

    def test_parse_srt_roundtrip(self):
        """Test that parse_srt can read generate_srt output."""
        segments = [
            Segment(
                id=1,
                speaker="male_us_1",
                text="Hello world.",
                start_ms=300,
                end_ms=2500,
                audio_duration_ms=2200,
            ),
            Segment(
                id=2,
                speaker="female_us_1",
                text="Goodbye world.",
                start_ms=3000,
                end_ms=5000,
                audio_duration_ms=2000,
            ),
        ]

        srt = generate_srt(segments)
        parsed = parse_srt(srt)

        assert len(parsed) == 2
        assert parsed[0]["text"] == "Hello world."
        assert parsed[0]["start_ms"] == 300
        assert parsed[0]["end_ms"] == 2500
        assert parsed[1]["text"] == "Goodbye world."
