"""Tests for SRT generation."""

import pytest
from src.models.script import Segment
from src.utils.srt import ms_to_srt_time, generate_srt


def test_ms_to_srt_time_zero():
    """Test conversion of 0ms."""
    assert ms_to_srt_time(0) == "00:00:00,000"


def test_ms_to_srt_time_milliseconds():
    """Test conversion of milliseconds only."""
    assert ms_to_srt_time(500) == "00:00:00,500"


def test_ms_to_srt_time_seconds():
    """Test conversion of seconds."""
    assert ms_to_srt_time(5000) == "00:00:05,000"


def test_ms_to_srt_time_minutes():
    """Test conversion of minutes."""
    assert ms_to_srt_time(90000) == "00:01:30,000"


def test_ms_to_srt_time_hours():
    """Test conversion of hours."""
    assert ms_to_srt_time(3661500) == "01:01:01,500"


def test_ms_to_srt_time_complex():
    """Test conversion of complex time."""
    # 1h 23m 45s 678ms
    ms = 1 * 3600000 + 23 * 60000 + 45 * 1000 + 678
    assert ms_to_srt_time(ms) == "01:23:45,678"


def test_generate_srt_empty():
    """Test SRT generation for empty segments."""
    result = generate_srt([])
    assert result == ""


def test_generate_srt_single():
    """Test SRT generation for single segment."""
    segments = [
        Segment(
            id=1,
            speaker="female_us_1",
            text="Hello world!",
            start_ms=0,
            end_ms=2000,
            audio_duration_ms=2000,
        ),
    ]

    result = generate_srt(segments)

    assert "1\n" in result
    assert "00:00:00,000 --> 00:00:02,000" in result
    assert "Hello world!" in result


def test_generate_srt_multiple():
    """Test SRT generation for multiple segments."""
    segments = [
        Segment(
            id=1,
            speaker="female_us_1",
            text="Hello!",
            start_ms=300,
            end_ms=1500,
            audio_duration_ms=1200,
        ),
        Segment(
            id=2,
            speaker="male_us_1",
            text="Hi there!",
            start_ms=2000,
            end_ms=3500,
            audio_duration_ms=1500,
        ),
    ]

    result = generate_srt(segments)

    # Check first entry
    assert "1\n" in result
    assert "00:00:00,300 --> 00:00:01,500" in result
    assert "Hello!" in result

    # Check second entry
    assert "2\n" in result
    assert "00:00:02,000 --> 00:00:03,500" in result
    assert "Hi there!" in result
