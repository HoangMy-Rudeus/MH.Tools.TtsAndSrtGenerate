"""Tests for TUI queue models."""

import json

import pytest

from src.services.validator import ValidationError
from src.tui.models import QueueItem, QueueStatus, build_queue_item


def _write_script(path, lesson_id="lesson_x", title="My Title", text="Hello!"):
    data = {
        "lesson_id": lesson_id,
        "title": title,
        "lines": [{"id": 1, "speaker": "female_us_1", "text": text}],
    }
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_build_queue_item_from_valid_file(tmp_path):
    p = _write_script(tmp_path / "ok.json")
    item = build_queue_item(p)

    assert item.title == "My Title"
    assert item.lesson_id == "lesson_x"
    assert item.script_path == str(p)
    assert item.status == QueueStatus.QUEUED
    assert item.progress == 0.0


def test_build_queue_item_invalid_raises(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text(json.dumps({"lesson_id": "", "title": "", "lines": []}), encoding="utf-8")

    with pytest.raises(ValidationError):
        build_queue_item(p)
