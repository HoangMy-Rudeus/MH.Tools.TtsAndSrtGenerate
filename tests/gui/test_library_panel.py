"""Tests for LibraryPanelLogic (no Tk rendering)."""

import json
import shutil

from src.gui.panels.library import LibraryPanelLogic


def _write_script(directory, lesson_id, title="T"):
    directory.mkdir(parents=True, exist_ok=True)
    data = {
        "lesson_id": lesson_id, "title": title,
        "lines": [{"id": 1, "speaker": "female_us_1", "text": "Hi!"}],
    }
    p = directory / f"{lesson_id}.json"
    p.write_text(json.dumps(data))
    return p


def test_load_lists_json_files(tmp_path):
    topics = tmp_path / "topics"
    topics.mkdir()
    _write_script(topics, "lesson_a", "Alpha")
    _write_script(topics, "lesson_b", "Beta")
    logic = LibraryPanelLogic(topics)
    items = logic.load()
    assert len(items) == 2
    lesson_ids = {item[1] for item in items}
    assert lesson_ids == {"lesson_a", "lesson_b"}


def test_load_returns_empty_for_missing_dir(tmp_path):
    logic = LibraryPanelLogic(tmp_path / "missing")
    assert logic.load() == []


def test_duplicate_creates_copy(tmp_path):
    topics = tmp_path / "topics"
    topics.mkdir()
    src = _write_script(topics, "lesson_a")
    logic = LibraryPanelLogic(topics)
    copy_path = logic.duplicate(src)
    assert copy_path.exists()
    assert copy_path.name == "lesson_a_copy.json"
    assert copy_path.read_text() == src.read_text()


def test_delete_removes_file(tmp_path):
    topics = tmp_path / "topics"
    topics.mkdir()
    p = _write_script(topics, "lesson_a")
    logic = LibraryPanelLogic(topics)
    logic.delete(p)
    assert not p.exists()


def test_load_includes_subfolder_files(tmp_path):
    topics = tmp_path / "topics"
    _write_script(topics, "root_one")
    _write_script(topics / "grammar", "g1")
    logic = LibraryPanelLogic(topics)
    lesson_ids = {item[1] for item in logic.load()}
    assert lesson_ids == {"root_one", "g1"}


def test_load_grouped_two_levels(tmp_path):
    topics = tmp_path / "topics"
    _write_script(topics, "loose")
    _write_script(topics / "grammar", "g1", "Grammar One")
    _write_script(topics / "grammar", "g2", "Grammar Two")
    logic = LibraryPanelLogic(topics)

    grouped = dict((cat, [it[1] for it in items]) for cat, items in logic.load_grouped())

    assert grouped[""] == ["loose"]
    assert sorted(grouped["grammar"]) == ["g1", "g2"]


def test_import_folder_copies_preserving_structure(tmp_path):
    topics = tmp_path / "topics"
    topics.mkdir()
    src = tmp_path / "inbox"
    _write_script(src, "loose")
    _write_script(src / "vocab", "v1")
    logic = LibraryPanelLogic(topics)

    count = logic.import_folder(src)

    assert count == 2
    assert (topics / "loose.json").exists()
    assert (topics / "vocab" / "v1.json").exists()
