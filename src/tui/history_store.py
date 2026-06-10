"""Persisted run history stored as a JSON array."""

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional


@dataclass
class HistoryRecord:
    """A single completed (or failed) generation run."""

    timestamp: str
    lesson_id: str
    title: str
    engine: str
    duration_ms: int
    line_count: int
    script_path: str
    audio_file: Optional[str]
    srt_file: Optional[str]
    subtitle_file: Optional[str]
    timeline_file: Optional[str]
    success: bool
    error: Optional[str] = None


class HistoryStore:
    """Reads/writes HistoryRecords to a JSON file."""

    def __init__(self, path: str | Path):
        self.path = Path(path)

    def load(self) -> list[HistoryRecord]:
        """Return all records in insertion order (oldest first)."""
        if not self.path.exists():
            return []
        with open(self.path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [HistoryRecord(**row) for row in data]

    def list(self) -> list[HistoryRecord]:
        """Return all records newest-first (for display)."""
        return list(reversed(self.load()))

    def append(self, record: HistoryRecord) -> None:
        """Append a record and persist."""
        records = self.load()
        records.append(record)
        self._save(records)

    def _save(self, records: list[HistoryRecord]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump([asdict(r) for r in records], f, indent=2, ensure_ascii=False)
