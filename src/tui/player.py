"""Audio replay seam — wraps ffplay so the TUI stays decoupled/testable."""

import shutil
import subprocess
from pathlib import Path
from typing import Optional, Protocol


class AudioPlayer(Protocol):
    def play(self, path: str) -> None: ...
    def stop(self) -> None: ...


class FfplayPlayer:
    """Plays audio via ffplay (bundled with ffmpeg). No-op if ffplay is absent."""

    def __init__(self) -> None:
        self._proc: Optional[subprocess.Popen] = None

    def available(self) -> bool:
        return shutil.which("ffplay") is not None

    def play(self, path: str) -> None:
        if not self.available() or not Path(path).exists():
            return
        self.stop()
        self._proc = subprocess.Popen(
            ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", str(path)]
        )

    def stop(self) -> None:
        if self._proc is not None and self._proc.poll() is None:
            self._proc.terminate()
        self._proc = None


class FakePlayer:
    """Test player: records calls instead of spawning a process."""

    def __init__(self) -> None:
        self.played: list[str] = []
        self.stop_count = 0

    def play(self, path: str) -> None:
        self.played.append(path)

    def stop(self) -> None:
        self.stop_count += 1
