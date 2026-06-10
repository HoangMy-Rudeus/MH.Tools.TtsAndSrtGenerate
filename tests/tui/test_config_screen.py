"""Tests for the Config screen."""

import pytest

from src.models.config import Config
from src.tui.app import TtsApp
from src.tui.config_io import load_config
from src.tui.history_store import HistoryStore
from src.tui.runner import FakeRunner
from src.tui.screens.config import ConfigScreen


def _make_app(tmp_path):
    return TtsApp(
        config=Config(),
        config_path=tmp_path / "config.yaml",
        output_dir=tmp_path / "output",
        runner=FakeRunner(),
        history_store=HistoryStore(tmp_path / "history.json"),
    )


@pytest.mark.asyncio
async def test_config_save_persists_changes(tmp_path):
    app = _make_app(tmp_path)
    async with app.run_test() as pilot:
        await pilot.press("c")
        screen = app.screen
        assert isinstance(screen, ConfigScreen)

        screen.query_one("#max_retries").value = "7"
        screen.query_one("#default_pause_ms").value = "555"
        screen.action_save()
        await pilot.pause()

    saved = load_config(tmp_path / "config.yaml")
    assert saved.synthesis.max_retries == 7
    assert saved.synthesis.default_pause_ms == 555
    assert app.state.config.synthesis.max_retries == 7
