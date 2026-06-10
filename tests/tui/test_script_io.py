"""Tests for script serialization."""

from src.models.script import Script, ScriptLine, ScriptSettings
from src.services.validator import ScriptValidator
from src.tui.script_io import save_script, script_to_dict


def _script():
    return Script(
        lesson_id="lesson_x", title="Title",
        lines=[
            ScriptLine(id=1, speaker="female_us_1", text="Hello!", emotion="cheerful", pause_after_ms=500),
            ScriptLine(id=2, speaker="male_us_1", text="Hi there!"),
        ],
        language="en", level="A2",
        settings=ScriptSettings(speech_rate=1.0, initial_silence_ms=500, default_pause_ms=400),
    )


def test_script_to_dict_round_trips_through_parser():
    parsed = ScriptValidator.parse_script(script_to_dict(_script()))
    assert parsed.lesson_id == "lesson_x"
    assert parsed.title == "Title"
    assert [l.id for l in parsed.lines] == [1, 2]
    assert parsed.lines[0].emotion == "cheerful"
    assert parsed.lines[0].pause_after_ms == 500
    assert parsed.settings.initial_silence_ms == 500


def test_save_script_writes_valid_loadable_file(tmp_path):
    path = tmp_path / "lesson_x.json"
    save_script(_script(), path)
    loaded = ScriptValidator.load_script(path)
    assert loaded.lesson_id == "lesson_x"
    assert len(loaded.lines) == 2
