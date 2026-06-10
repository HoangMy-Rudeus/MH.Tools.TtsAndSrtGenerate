"""Tests for the run history store."""

from src.tui.history_store import HistoryRecord, HistoryStore


def _record(lesson_id="lesson_1", success=True):
    return HistoryRecord(
        timestamp="2026-06-11T10:00:00Z",
        lesson_id=lesson_id,
        title="Title",
        engine="edge",
        duration_ms=1000,
        line_count=2,
        script_path="topics/a.json",
        audio_file="output/a.mp3",
        srt_file="output/a.srt",
        subtitle_file="output/a_subtitles.json",
        timeline_file="output/a_timeline.json",
        success=success,
        error=None,
    )


def test_load_missing_file_returns_empty(tmp_path):
    store = HistoryStore(tmp_path / "history.json")
    assert store.load() == []


def test_append_then_load_round_trips(tmp_path):
    store = HistoryStore(tmp_path / "history.json")
    rec = _record()
    store.append(rec)

    loaded = store.load()
    assert len(loaded) == 1
    assert loaded[0] == rec


def test_list_returns_newest_first(tmp_path):
    store = HistoryStore(tmp_path / "history.json")
    store.append(_record(lesson_id="first"))
    store.append(_record(lesson_id="second"))

    listed = store.list()
    assert [r.lesson_id for r in listed] == ["second", "first"]
