"""Tests for the Editor screen."""

import pytest

from src.models.config import Config
from src.models.script import ScriptLine
from src.services.validator import ScriptValidator
from src.tui.app import TtsApp
from src.tui.history_store import HistoryStore
from src.tui.runner import FakeRunner
from src.tui.screens.editor import EditorScreen


def _make_app(tmp_path):
    return TtsApp(
        config=Config(), config_path=tmp_path / "config.yaml",
        output_dir=tmp_path / "output", runner=FakeRunner(),
        history_store=HistoryStore(tmp_path / "history.json"),
    )


@pytest.mark.asyncio
async def test_editor_saves_valid_script(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)            # so topics/ is written under tmp_path
    app = _make_app(tmp_path)
    async with app.run_test() as pilot:
        app.push_screen(EditorScreen())
        await pilot.pause()
        screen = app.screen
        assert isinstance(screen, EditorScreen)
        screen.query_one("#lesson_id").value = "made_in_tui"
        screen.query_one("#title").value = "Made in TUI"
        screen.lines = [
            ScriptLine(id=1, speaker="female_us_1", text="Hello!"),
            ScriptLine(id=2, speaker="male_us_1", text="Hi!"),
        ]
        screen.action_save()
        await pilot.pause()

    saved = ScriptValidator.load_script(tmp_path / "topics" / "made_in_tui.json")
    assert saved.lesson_id == "made_in_tui"
    assert [l.id for l in saved.lines] == [1, 2]


def test_next_line_id_helper():
    assert EditorScreen._next_id([]) == 1
    assert EditorScreen._next_id([ScriptLine(id=1, speaker="x", text="a"),
                                  ScriptLine(id=4, speaker="y", text="b")]) == 5
