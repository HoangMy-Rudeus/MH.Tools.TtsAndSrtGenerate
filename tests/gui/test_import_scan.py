"""Tests for the Tk-free import-folder scanner and history dedup."""

import json

from src.gui.import_scan import ScannedFile, scan_folder, mark_history_duplicates
from src.tui.history_store import HistoryRecord


def _write_script(directory, lesson_id, title="T"):
    directory.mkdir(parents=True, exist_ok=True)
    data = {
        "lesson_id": lesson_id, "title": title,
        "lines": [{"id": 1, "speaker": "female_us_1", "text": "Hi!"}],
    }
    p = directory / f"{lesson_id}.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    return p


def test_scan_missing_dir_returns_empty(tmp_path):
    assert scan_folder(tmp_path / "missing") == []


def test_scan_groups_by_two_levels(tmp_path):
    root = tmp_path / "inbox"
    _write_script(root / "grammar", "g1", "Grammar One")
    _write_script(root / "grammar", "g2", "Grammar Two")
    _write_script(root / "vocab", "v1", "Vocab One")

    files = scan_folder(root)

    by_cat = {}
    for f in files:
        by_cat.setdefault(f.category, []).append(f.lesson_id)
    assert sorted(by_cat["grammar"]) == ["g1", "g2"]
    assert by_cat["vocab"] == ["v1"]


def test_scan_root_level_files_have_empty_category(tmp_path):
    root = tmp_path / "inbox"
    _write_script(root, "loose", "Loose Topic")

    files = scan_folder(root)

    assert len(files) == 1
    assert files[0].category == ""
    assert files[0].title == "Loose Topic"


def test_scan_flags_invalid_json(tmp_path):
    root = tmp_path / "inbox"
    root.mkdir()
    (root / "broken.json").write_text("{not json", encoding="utf-8")

    files = scan_folder(root)

    assert len(files) == 1
    assert files[0].valid is False
    assert files[0].lesson_id == "broken"  # falls back to stem


def test_mark_history_duplicates_by_basename(tmp_path):
    root = tmp_path / "inbox"
    p1 = _write_script(root, "g1")
    _write_script(root, "g2")
    files = scan_folder(root)

    history = [
        HistoryRecord(
            timestamp="t", lesson_id="g1", title="T", engine="edge",
            duration_ms=0, line_count=0,
            script_path=str(tmp_path / "elsewhere" / "g1.json"),
            audio_file=None, srt_file=None, subtitle_file=None,
            timeline_file=None, success=True,
        )
    ]
    mark_history_duplicates(files, history)

    done = {f.lesson_id: f.already_done for f in files}
    assert done["g1"] is True   # same basename g1.json, different dir
    assert done["g2"] is False
