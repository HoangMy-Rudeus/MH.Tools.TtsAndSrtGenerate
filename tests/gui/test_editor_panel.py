"""Tests for EditorPanelLogic (no Tk rendering)."""

import pytest

from src.gui.panels.editor import EditorPanelLogic
from src.gui.state import AppState
from src.models.config import Config
from src.models.script import ScriptLine
from src.tui.history_store import HistoryStore
from src.tui.player import FakePlayer
from src.tui.runner import FakeRunner


def _make_state(tmp_path):
    return AppState(
        config=Config(),
        config_path=tmp_path / "config.yaml",
        output_dir=tmp_path / "output",
        history=HistoryStore(tmp_path / "history.json"),
        runner=FakeRunner(),
        player=FakePlayer(),
    )


def test_next_line_id_empty():
    logic = EditorPanelLogic.__new__(EditorPanelLogic)
    logic.lines = []
    assert logic._next_id() == 1


def test_next_line_id_with_lines():
    logic = EditorPanelLogic.__new__(EditorPanelLogic)
    logic.lines = [
        ScriptLine(id=1, speaker="female_us_1", text="a"),
        ScriptLine(id=4, speaker="male_us_1", text="b"),
    ]
    assert logic._next_id() == 5


def test_move_up_swaps(tmp_path):
    state = _make_state(tmp_path)
    logic = EditorPanelLogic(state)
    logic.lines = [
        ScriptLine(id=1, speaker="female_us_1", text="first"),
        ScriptLine(id=2, speaker="male_us_1", text="second"),
    ]
    assert logic.move_up(1) is True
    assert logic.lines[0].text == "second"
    assert logic.lines[1].text == "first"


def test_move_up_noop_at_top(tmp_path):
    state = _make_state(tmp_path)
    logic = EditorPanelLogic(state)
    logic.lines = [ScriptLine(id=1, speaker="female_us_1", text="only")]
    assert logic.move_up(0) is False


def test_move_down_swaps(tmp_path):
    state = _make_state(tmp_path)
    logic = EditorPanelLogic(state)
    logic.lines = [
        ScriptLine(id=1, speaker="female_us_1", text="first"),
        ScriptLine(id=2, speaker="male_us_1", text="second"),
    ]
    assert logic.move_down(0) is True
    assert logic.lines[0].text == "second"


def test_save_writes_file_and_calls_callback(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    state = _make_state(tmp_path)
    logic = EditorPanelLogic(state)
    logic.lines = [ScriptLine(id=1, speaker="female_us_1", text="Hello!")]

    saved = []
    ok, msg = logic.save("test_lesson", "Test Title", "en", "B1", on_save=lambda: saved.append(1))

    assert ok is True
    assert (tmp_path / "topics" / "test_lesson.json").exists()
    assert saved


def test_save_fails_on_empty_lesson_id(tmp_path):
    state = _make_state(tmp_path)
    logic = EditorPanelLogic(state)
    logic.lines = [ScriptLine(id=1, speaker="female_us_1", text="Hello!")]
    ok, msg = logic.save("", "Title", "en", "B1", on_save=lambda: None)
    assert ok is False
    assert msg
