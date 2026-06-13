"""Tests for TUI config load/save."""

from src.models.config import Config
from src.tui.config_io import load_config, save_config


def test_to_dict_round_trips_with_from_dict():
    cfg = Config()
    cfg.engine = "kokoro"
    cfg.edge.voices["female_us_1"] = "en-US-AriaNeural"
    cfg.audio.output_format = "wav"
    cfg.synthesis.max_retries = 5

    rebuilt = Config.from_dict(cfg.to_dict())

    assert rebuilt.engine == "kokoro"
    assert rebuilt.edge.voices["female_us_1"] == "en-US-AriaNeural"
    assert rebuilt.audio.output_format == "wav"
    assert rebuilt.synthesis.max_retries == 5


def test_save_then_load_returns_equal_config(tmp_path):
    cfg = Config()
    cfg.engine = "kokoro"
    cfg.audio.normalize_to = -14.0
    path = tmp_path / "config.yaml"

    save_config(cfg, path)
    loaded = load_config(path)

    assert loaded.engine == "kokoro"
    assert loaded.audio.normalize_to == -14.0
    assert loaded.edge.voices == cfg.edge.voices


def test_load_missing_file_returns_defaults(tmp_path):
    loaded = load_config(tmp_path / "does_not_exist.yaml")
    assert loaded.engine == "edge"


def test_paths_defaults():
    cfg = Config()
    assert cfg.paths.topics_dir == "topics"
    assert cfg.paths.output_dir == "output"
    assert cfg.paths.import_dir == ""


def test_paths_round_trip():
    cfg = Config()
    cfg.paths.topics_dir = "my_topics"
    cfg.paths.output_dir = "build/out"
    cfg.paths.import_dir = "inbox"

    rebuilt = Config.from_dict(cfg.to_dict())

    assert rebuilt.paths.topics_dir == "my_topics"
    assert rebuilt.paths.output_dir == "build/out"
    assert rebuilt.paths.import_dir == "inbox"


def test_paths_partial_config_falls_back_to_defaults():
    cfg = Config.from_dict({"paths": {"topics_dir": "only_topics"}})
    assert cfg.paths.topics_dir == "only_topics"
    assert cfg.paths.output_dir == "output"
    assert cfg.paths.import_dir == ""
