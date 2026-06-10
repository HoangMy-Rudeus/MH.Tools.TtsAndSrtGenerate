"""Tests for the Queue screen."""

import pytest

from src.models.config import Config
from src.tui.app import TtsApp
from src.tui.history_store import HistoryStore
from src.tui.models import QueueItem, QueueStatus
from src.tui.runner import FakeRunner
from src.tui.screens.queue import QueueScreen


def _make_app(tmp_path, runner):
    return TtsApp(
        config=Config(),
        config_path=tmp_path / "config.yaml",
        output_dir=tmp_path / "output",
        runner=runner,
        history_store=HistoryStore(tmp_path / "history.json"),
    )


def _enqueue(app, script_path, title="T", lesson_id="L"):
    app.state.queue.append(
        QueueItem(script_path=str(script_path), title=title, lesson_id=lesson_id)
    )


@pytest.mark.asyncio
async def test_run_all_completes_items_and_records_history(tmp_path):
    app = _make_app(tmp_path, FakeRunner(total_lines=2, duration_ms=3000))
    async with app.run_test() as pilot:
        _enqueue(app, tmp_path / "a.json", lesson_id="a")
        screen = app.screen
        assert isinstance(screen, QueueScreen)
        screen.refresh_table()
        await pilot.press("r")        # run all
        await pilot.pause()
        await app.workers.wait_for_complete()
        await pilot.pause()

        assert app.state.queue[0].status == QueueStatus.DONE
        assert app.state.queue[0].progress == 1.0
        history = app.state.history.list()
        assert len(history) == 1
        assert history[0].success is True
        assert history[0].lesson_id == "a"


@pytest.mark.asyncio
async def test_run_all_marks_failure_and_continues(tmp_path):
    app = _make_app(tmp_path, FakeRunner(total_lines=1, fail_with="network down"))
    async with app.run_test() as pilot:
        _enqueue(app, tmp_path / "a.json", lesson_id="a")
        app.screen.refresh_table()
        await pilot.press("r")
        await app.workers.wait_for_complete()
        await pilot.pause()

        assert app.state.queue[0].status == QueueStatus.FAILED
        assert app.state.queue[0].error == "network down"
        assert app.state.history.list()[0].success is False


@pytest.mark.asyncio
async def test_queue_opens_editor(tmp_path):
    app = _make_app(tmp_path, FakeRunner())
    async with app.run_test() as pilot:
        await pilot.press("e")
        assert app.screen.__class__.__name__ == "EditorScreen"
