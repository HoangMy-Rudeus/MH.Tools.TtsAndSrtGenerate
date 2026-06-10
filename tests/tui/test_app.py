"""Tests for the top-level TtsApp shell."""

import pytest

from src.models.config import Config
from src.tui.app import TtsApp
from src.tui.history_store import HistoryStore
from src.tui.runner import FakeRunner


def _make_app(tmp_path):
    return TtsApp(
        config=Config(),
        config_path=tmp_path / "config.yaml",
        output_dir=tmp_path / "output",
        runner=FakeRunner(),
        history_store=HistoryStore(tmp_path / "history.json"),
    )


@pytest.mark.asyncio
async def test_app_starts_on_queue_screen(tmp_path):
    app = _make_app(tmp_path)
    async with app.run_test() as pilot:
        assert app.screen.__class__.__name__ == "QueueScreen"


@pytest.mark.asyncio
async def test_app_switches_to_config_and_history(tmp_path):
    app = _make_app(tmp_path)
    async with app.run_test() as pilot:
        await pilot.press("c")
        assert app.screen.__class__.__name__ == "ConfigScreen"
        await pilot.press("escape")
        await pilot.press("h")
        assert app.screen.__class__.__name__ == "HistoryScreen"
