"""Tk-free scanning of an import folder into a 2-level (category → file) list.

Used by the Queue import-folder picker and the Library folder importer. Kept free
of any Tk dependency so it can be unit-tested without opening a window.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from ..tui.history_store import HistoryRecord


@dataclass
class ScannedFile:
    """A .json script discovered while scanning an import folder."""

    path: Path
    category: str          # immediate parent folder name; "" for root-level files
    lesson_id: str
    title: str
    valid: bool = True     # False if the file could not be parsed as a topic
    error: str = ""
    already_done: bool = False  # set by mark_history_duplicates


def scan_folder(root: str | Path) -> list[ScannedFile]:
    """
    Walk ``root`` two levels deep and return one ScannedFile per ``.json`` file.

    Files directly in ``root`` get ``category == ""``; files in an immediate
    subfolder get that subfolder's name as their category. Deeper nesting is
    ignored. Unparseable files are returned with ``valid=False`` so the caller
    can show (but not queue) them.
    """
    root = Path(root)
    if not root.exists():
        return []

    results: list[ScannedFile] = []

    def _add(path: Path, category: str) -> None:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            results.append(ScannedFile(
                path=path,
                category=category,
                lesson_id=data.get("lesson_id", path.stem),
                title=data.get("title", ""),
            ))
        except Exception as exc:
            results.append(ScannedFile(
                path=path, category=category,
                lesson_id=path.stem, title="",
                valid=False, error=str(exc),
            ))

    for path in sorted(root.glob("*.json")):
        _add(path, "")
    for sub in sorted(p for p in root.iterdir() if p.is_dir()):
        for path in sorted(sub.glob("*.json")):
            _add(path, sub.name)

    return results


def mark_history_duplicates(
    files: Iterable[ScannedFile],
    history: Iterable[HistoryRecord],
) -> None:
    """
    Flag ``already_done`` on any scanned file whose basename matches the basename
    of a script already recorded in ``history`` (regardless of directory).
    """
    seen = {Path(r.script_path).name for r in history if r.script_path}
    for f in files:
        if f.path.name in seen:
            f.already_done = True
