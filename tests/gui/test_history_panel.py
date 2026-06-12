"""Tests for HistoryPanelLogic (no Tk rendering)."""

import json

from src.gui.panels.history import HistoryPanelLogic
from src.gui.state import AppState
from src.models.config import Config
from src.tui.history_store import HistoryRecord, HistoryStore
from src.tui.models import QueueStatus
from src.tui.player import FakePlayer
from src.tui.runner import FakeRunner


def _make_state(tmp_path, store=None):
    return AppState(
        config=Config(),
        config_path=tmp_path / "config.yaml",
        output_dir=tmp_path / "output",
        history=store or HistoryStore(tmp_path / "history.json"),
        runner=FakeRunner(),
        player=FakePlayer(),
    )


def _write_script(tmp_path, lesson_id="lesson_a"):
    data = {
        "lesson_id": lesson_id, "title": "T",
        "lines": [{"id": 1, "speaker": "female_us_1", "text": "Hi!"}],
    }
    p = tmp_path / f"{lesson_id}.json"
    p.write_text(json.dumps(data))
    return p


def _record(script_path, lesson_id="a"):
    return HistoryRecord(
        timestamp="2026-06-12T00:00:00Z",
        lesson_id=lesson_id, title="T", engine="edge",
        duration_ms=1000, line_count=1,
        script_path=str(script_path),
        audio_file="output/a.mp3", srt_file="output/a.srt",
        subtitle_file="output/a_subtitles.json",
        timeline_file="output/a_timeline.json",
        success=True,
    )


def test_load_returns_newest_first(tmp_path):
    store = HistoryStore(tmp_path / "history.json")
    p = _write_script(tmp_path)
    store.append(_record(p, "first"))
    store.append(_record(p, "second"))
    state = _make_state(tmp_path, store)
    logic = HistoryPanelLogic(state)
    records = logic.load()
    assert records[0].lesson_id == "second"
    assert records[1].lesson_id == "first"


def test_requeue_appends_to_queue(tmp_path):
    p = _write_script(tmp_path, "lesson_a")
    state = _make_state(tmp_path)
    logic = HistoryPanelLogic(state)
    ok, msg = logic.requeue(_record(p, "lesson_a"))
    assert ok is True
    assert len(state.queue) == 1
    assert state.queue[0].lesson_id == "lesson_a"


def test_requeue_fails_if_script_missing(tmp_path):
    state = _make_state(tmp_path)
    logic = HistoryPanelLogic(state)
    rec = _record(tmp_path / "gone.json", "gone")
    ok, msg = logic.requeue(rec)
    assert ok is False
    assert len(state.queue) == 0
