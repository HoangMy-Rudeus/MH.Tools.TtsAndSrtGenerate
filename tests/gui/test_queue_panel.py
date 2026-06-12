"""Tests for QueuePanelLogic (state mutations, no Tk rendering)."""

import json

import pytest

from src.gui.panels.queue import QueuePanelLogic
from src.gui.state import AppState
from src.models.config import Config
from src.tui.history_store import HistoryStore
from src.tui.models import QueueStatus
from src.tui.player import FakePlayer
from src.tui.runner import FakeRunner


def _make_state(tmp_path, runner=None):
    return AppState(
        config=Config(),
        config_path=tmp_path / "config.yaml",
        output_dir=tmp_path / "output",
        history=HistoryStore(tmp_path / "history.json"),
        runner=runner or FakeRunner(total_lines=1, duration_ms=500),
        player=FakePlayer(),
    )


def _write_script(tmp_path, lesson_id="lesson_x"):
    data = {
        "lesson_id": lesson_id, "title": "T",
        "lines": [{"id": 1, "speaker": "female_us_1", "text": "Hello!"}],
    }
    p = tmp_path / f"{lesson_id}.json"
    p.write_text(json.dumps(data))
    return p


def test_add_item_enqueues(tmp_path):
    state = _make_state(tmp_path)
    logic = QueuePanelLogic(state)
    p = _write_script(tmp_path)
    item = logic.add_item(str(p))
    assert item.lesson_id == "lesson_x"
    assert len(state.queue) == 1


def test_add_item_raises_on_invalid(tmp_path):
    from src.services.validator import ValidationError
    state = _make_state(tmp_path)
    logic = QueuePanelLogic(state)
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"lesson_id": "", "title": "", "lines": []}))
    with pytest.raises(ValidationError):
        logic.add_item(str(bad))


def test_remove_queued_item(tmp_path):
    state = _make_state(tmp_path)
    logic = QueuePanelLogic(state)
    p = _write_script(tmp_path)
    logic.add_item(str(p))
    assert logic.remove_item(0) is True
    assert len(state.queue) == 0


def test_remove_refuses_running_item(tmp_path):
    state = _make_state(tmp_path)
    logic = QueuePanelLogic(state)
    p = _write_script(tmp_path)
    logic.add_item(str(p))
    state.queue[0].status = QueueStatus.RUNNING
    assert logic.remove_item(0) is False
    assert len(state.queue) == 1


def test_run_all_sets_done_and_records_history(tmp_path):
    state = _make_state(tmp_path, FakeRunner(total_lines=1, duration_ms=500))
    logic = QueuePanelLogic(state)
    p = _write_script(tmp_path)
    logic.add_item(str(p))

    done = []
    t = logic.run_all(on_update=lambda: None, on_done=lambda: done.append(1))
    t.join(timeout=5)

    assert state.queue[0].status == QueueStatus.DONE
    assert state.queue[0].progress == 1.0
    assert len(state.history.list()) == 1
    assert state.history.list()[0].success is True
    assert done


def test_run_all_marks_failed_on_error(tmp_path):
    state = _make_state(tmp_path, FakeRunner(total_lines=1, fail_with="boom"))
    logic = QueuePanelLogic(state)
    p = _write_script(tmp_path)
    logic.add_item(str(p))

    done = []
    t = logic.run_all(on_update=lambda: None, on_done=lambda: done.append(1))
    t.join(timeout=5)

    assert state.queue[0].status == QueueStatus.FAILED
    assert state.queue[0].error == "boom"
    assert done
