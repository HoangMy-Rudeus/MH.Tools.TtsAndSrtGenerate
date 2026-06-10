"""Tests for the History screen."""

import json

import pytest

from src.models.config import Config
from src.tui.app import TtsApp
from src.tui.history_store import HistoryRecord, HistoryStore
from src.tui.runner import FakeRunner
from src.tui.screens.history import HistoryScreen


def _write_script(tmp_path, lesson_id):
    p = tmp_path / f"{lesson_id}.json"
    p.write_text(
        json.dumps({
            "lesson_id": lesson_id,
            "title": f"Title {lesson_id}",
            "lines": [{"id": 1, "speaker": "female_us_1", "text": "Hello!"}],
        }),
        encoding="utf-8",
    )
    return p


def _record(script_path, lesson_id):
    return HistoryRecord(
        timestamp="2026-06-11T10:00:00Z", lesson_id=lesson_id, title=f"Title {lesson_id}",
        engine="edge", duration_ms=1000, line_count=1,
        script_path=str(script_path), audio_file="output/x.mp3",
        srt_file="output/x.srt", subtitle_file="output/x_subtitles.json",
        timeline_file="output/x_timeline.json", success=True, error=None,
    )


def _make_app(tmp_path):
    store = HistoryStore(tmp_path / "history.json")
    store.append(_record(_write_script(tmp_path, "a"), "a"))
    store.append(_record(_write_script(tmp_path, "b"), "b"))
    return TtsApp(
        config=Config(),
        config_path=tmp_path / "config.yaml",
        output_dir=tmp_path / "output",
        runner=FakeRunner(),
        history_store=store,
    )


@pytest.mark.asyncio
async def test_history_lists_newest_first(tmp_path):
    app = _make_app(tmp_path)
    async with app.run_test() as pilot:
        await pilot.press("h")
        screen = app.screen
        assert isinstance(screen, HistoryScreen)
        table = screen.query_one("#history-table")
        assert table.row_count == 2
        # newest first -> first data row is lesson "b"
        assert screen.records[0].lesson_id == "b"


@pytest.mark.asyncio
async def test_history_rerun_enqueues_script(tmp_path):
    app = _make_app(tmp_path)
    async with app.run_test() as pilot:
        await pilot.press("h")
        screen = app.screen
        screen.query_one("#history-table").move_cursor(row=0)
        screen.action_rerun()
        await pilot.pause()
        assert len(app.state.queue) == 1
        # row 0 is newest = "b"
        assert app.state.queue[0].lesson_id == "b"


@pytest.mark.asyncio
async def test_history_play_calls_player(tmp_path):
    from src.tui.player import FakePlayer

    store = HistoryStore(tmp_path / "history.json")
    store.append(_record(_write_script(tmp_path, "a"), "a"))
    player = FakePlayer()
    app = TtsApp(
        config=Config(), config_path=tmp_path / "config.yaml",
        output_dir=tmp_path / "output", runner=FakeRunner(),
        history_store=store, player=player,
    )
    async with app.run_test() as pilot:
        await pilot.press("h")
        app.screen.query_one("#history-table").move_cursor(row=0)
        await pilot.press("p")
        await pilot.pause()
        assert player.played == ["output/x.mp3"]
